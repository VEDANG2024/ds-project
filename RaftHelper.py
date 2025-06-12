import sys
import os
import time
import grpc
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from Raft import Raft
except ImportError as e:
    logging.error(f"Error importing Raft: {str(e)}")
    sys.exit(1)

try:
    import fileService_pb2
    import fileService_pb2_grpc
except ImportError as e:
    logging.error(f"Error importing fileService_pb2: {str(e)}")
    sys.exit(1)

class RaftHelper:
    def __init__(self, hostname, server_port, raft_port, activeNodesChecker, super_node_address):
        self.hostname = hostname
        self.server_port = server_port
        self.raft_port = raft_port
        self.node_id = f"{hostname}:{server_port}"
        self.active_checker = activeNodesChecker
        self.super_node_address = super_node_address
        self.node = None
        self.cluster_name = 'team1'
        logging.getLogger().handlers[0].setFormatter(
            logging.Formatter(f'%(asctime)s | %(levelname)s | Node {self.node_id} | %(message)s')
        )
        logging.getLogger().handlers[1].setFormatter(
            logging.Formatter(f'%(asctime)s | %(levelname)s | Node {self.node_id} | %(message)s')
        )
        self.initialize_raft()

    def wait_for_supernode(self, max_attempts=10, delay=2):
        logging.info(f"Waiting for supernode at {self.super_node_address}")
        for attempt in range(max_attempts):
            try:
                with grpc.insecure_channel(self.super_node_address) as channel:
                    future = grpc.channel_ready_future(channel)
                    future.result(timeout=3)
                    logging.info(f"Connected to supernode after attempt {attempt+1}")
                    return True
            except (grpc.FutureTimeoutError, grpc.RpcError) as e:
                logging.warning(f"Supernode connection attempt {attempt+1} failed: {type(e).__name__}: {str(e)}")
                time.sleep(delay)
        logging.error(f"Supernode not ready after {max_attempts} attempts")
        return False

    def initialize_raft(self):
        logging.info("Initializing Raft node")
        try:
            raft_nodes = []
            for _ in range(3):  # Reduced retries
                active_channels = self.active_checker.get_active_channels()
                logging.info(f"Active channels: {list(active_channels.keys())}")
                for ip in active_channels:
                    if ip != f"{self.hostname}:{self.server_port}":
                        raft_ip = ip.split(':')[0]
                        raft_port = str(int(ip.split(':')[1]) + 1)
                        if f"{raft_ip}:{raft_port}" not in raft_nodes:
                            raft_nodes.append(f"{raft_ip}:{raft_port}")
                            logging.info(f"Discovered peer: {raft_ip}:{raft_port}")
                if raft_nodes:
                    break
                logging.warning("No peers found, retrying...")
                time.sleep(1)
            logging.info(f"Raft peers: {raft_nodes}")
            self.node = Raft(f"{self.hostname}:{self.raft_port}", raft_nodes)
            for _ in range(10):  # Reduced stabilization time
                status = self.node.getStatus()
                state = status.get('state')
                leader = str(status.get('leader', 'None'))
                role = 'Leader' if state == 2 else 'Follower'
                logging.info(f"Raft status: Role={role}, Leader={leader}")
                if state == 2 or (raft_nodes and leader != 'None'):
                    break
                time.sleep(1)
            logging.info("Raft node initialized successfully")
            if not self.wait_for_supernode():
                logging.warning("Proceeding without supernode notification")
            else:
                self.notify_supernode()
        except Exception as e:
            logging.error(f"Raft initialization failed: {type(e).__name__}: {str(e)}", exc_info=True)
            raise

    def is_leader(self):
        try:
            for attempt in range(3):
                status = self.node.getStatus()
                leader = str(status.get('leader', 'None'))
                self_addr = f"{self.hostname}:{self.raft_port}"
                is_leader = leader == self_addr and status.get('state') == 2
                role = 'Leader' if is_leader else 'Follower'
                logging.info(f"Leadership check: Role={role}, Leader={leader}, Attempt={attempt+1}")
                if is_leader or leader != 'None':
                    break
                time.sleep(0.5)
            if is_leader:
                self.notify_supernode()
            return is_leader
        except Exception as e:
            logging.error(f"Leadership check failed: {type(e).__name__}: {str(e)}")
            return False

    def notify_supernode(self):
        retries = 3  # Reduced retries
        for attempt in range(retries):
            try:
                with grpc.insecure_channel(self.super_node_address) as channel:
                    stub = fileService_pb2_grpc.FileserviceStub(channel)
                    response = stub.getLeaderInfo(fileService_pb2.ClusterInfo(
                        ip=self.hostname,
                        port=str(self.server_port),
                        clusterName=self.cluster_name
                    ), timeout=3)
                    logging.info(f"Notified supernode attempt {attempt+1}: Success={response.success}, Message={response.message}")
                    if response.success:
                        return True
                    logging.warning(f"Supernode notification failed: {response.message}")
                time.sleep(1)
            except grpc.RpcError as e:
                logging.warning(f"Supernode notification attempt {attempt+1} failed: {type(e).__name__}: {str(e)}")
                time.sleep(1)
        logging.error(f"Supernode notification failed after {retries} attempts")
        return False

    def connectivity_test(self, node_ip):
        try:
            with grpc.insecure_channel(node_ip) as channel:
                stub = fileService_pb2_grpc.FileserviceStub(channel)
                response = stub.getLeaderInfo(fileService_pb2.ClusterInfo(
                    ip=self.hostname,
                    port=str(self.server_port),
                    clusterName=self.cluster_name
                ))
                logging.info(f"Connectivity test to {node_ip}: Success={response.success}")
                return response.success
        except Exception as e:
            logging.error(f"Connectivity test to {node_ip} failed: {type(e).__name__}: {str(e)}")
            return False