from concurrent import futures
import sys
import os
import grpc
import yaml
import time
import logging
import socket

# Add project directory to sys.path
project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    logging.info(f"server.py: Added {project_dir} to sys.path")

try:
    import fileService_pb2
    import fileService_pb2_grpc
except ImportError as e:
    logging.error(f"Import error in server.py: {e}")
    raise

from FileServer import FileServer
from ActiveNodesChecker import ActiveNodesChecker
from ShardingHandler import ShardingHandler
from RaftHelper import RaftHelper

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | Server | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except socket.error as e:
            logging.error(f"Port {port} binding failed: {str(e)}")
            return False

def run_server(hostIP, port, raftPort):
    logging.info(f"Starting server on {hostIP}:{port}, Raft on {raftPort}")
    try:
        if not check_port(hostIP, int(port)):
            raise RuntimeError(f"Port {port} is not available")
        if not check_port(hostIP, int(raftPort)):
            raise RuntimeError(f"Raft port {raftPort} is not available")
        active_checker = ActiveNodesChecker()
        sharding_handler = ShardingHandler(active_checker)
        super_node_address = f"{hostIP}:9000"
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        fileService_pb2_grpc.add_FileserviceServicer_to_server(
            FileServer(hostIP, int(port), active_checker, sharding_handler, super_node_address), server
        )
        server.add_insecure_port(f'[::]:{port}')
        logging.info(f"gRPC server started on {hostIP}:{port}")
        server.start()
        logging.info(f"Server running on {hostIP}:{port}")
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            logging.info("Shutting down server")
            server.stop(0)
    except Exception as e:
        logging.error(f"Server startup error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        logging.info(f"sys.path updated: {os.path.abspath(os.path.dirname(__file__))} in {sys.path}")
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        node_id = sys.argv[1] if len(sys.argv) > 1 else 'one'
        hostIP = config['nodes'][node_id]['hostname']
        port = str(config['nodes'][node_id]['server_port'])
        raftPort = str(config['nodes'][node_id]['raft_port'])
        super_node_address = config.get('super_node_address', f"{hostIP}:9000")
        logging.info(f"Starting server on {hostIP}:{port}, Raft on {raftPort}")
        run_server(hostIP, port, raftPort)
    except FileNotFoundError:
        logging.error("config.yaml not found")
        sys.exit(1)
    except KeyError as e:
        logging.error(f"Invalid node ID or config missing: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading config: {type(e).__name__}: {str(e)}", exc_info=True)
        sys.exit(1)