import sys
import os
import grpc
import logging
import yaml
from concurrent import futures
import ast

project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    logging.info(f"superNode.py: Added {project_dir} to sys.path")

try:
    import fileService_pb2
    import fileService_pb2_grpc
except ImportError as e:
    logging.error(f"Import error in superNode.py: {e}")
    raise

from ActiveNodesChecker import ActiveNodesChecker
from db import DB
from DeleteHelper import DeleteHelper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | Supernode | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('supernode.log', mode='a')
    ]
)

class SuperNode(fileService_pb2_grpc.FileserviceServicer):
    def __init__(self, hostIP, port):
        self.serverAddress = f"{hostIP}:{port}"
        self.clusterList = {}
        self.clusterLeaders = {}
        self.activeChecker = ActiveNodesChecker()
        self.db = DB()
        self.delete_helper = DeleteHelper(hostIP, str(port), self.activeChecker)
        self.db.deleteEntry("leader_team1")
        self.initializeClusterList()
        logging.info(f"Supernode initialized: Address={self.serverAddress}")

    def initializeClusterList(self):
        try:
            with open('iptable.txt', 'r') as file:
                for idx, line in enumerate(file, 1):
                    ip_port = line.strip()
                    if ip_port:
                        team = f"team{idx}"
                        self.clusterList[team] = ip_port
                        logging.info(f"Added to cluster: Team={team}, Address={ip_port}")
            logging.info(f"Cluster list built: {self.clusterList}")
        except FileNotFoundError:
            logging.error("iptable.txt not found")
            raise
        except Exception as e:
            logging.error(f"Error reading iptable.txt: {type(e).__name__}: {str(e)}")
            raise

    def updateClusterLeaders(self):
        active_ips = self.activeChecker.get_active_channels()
        logging.info(f"Active nodes: {list(active_ips.keys())}")
        self.clusterLeaders.clear()
        for team, ip in self.clusterList.items():
            if ip in active_ips:
                self.clusterLeaders[team] = ip
                logging.info(f"Updated leader: Team={team}, Leader={ip}")
            else:
                logging.warning(f"No active leader for Team={team}")
        leader_ip = self.db.getData("leader_team1")
        if leader_ip and leader_ip in active_ips:
            self.clusterLeaders['team1'] = leader_ip
            logging.info(f"Restored leader from DB: Team=team1, Leader={leader_ip}")
        elif self.clusterLeaders.get('team1'):
            self.db.setData("leader_team1", self.clusterLeaders['team1'])
            logging.info(f"Set leader_team1 to {self.clusterLeaders['team1']}")
        logging.info(f"Current leaders: {self.clusterLeaders}")

    def getClusterStats(self, request, context):
        logging.info("Providing cluster stats")
        return fileService_pb2.ClusterStats(cpu_usage="0", disk_space="0", used_mem="0")

    def leastUtilizedNode(self, request, context):
        logging.info("Selecting least utilized node")
        stats = {}
        for team, ip in self.clusterList.items():
            try:
                with grpc.insecure_channel(ip) as channel:
                    stub = fileService_pb2_grpc.FileserviceStub(channel)
                    response = stub.getClusterStats(fileService_pb2.Empty())
                    stats[ip] = {'cpu': float(response.cpu_usage), 'disk': float(response.disk_space), 'mem': float(response.used_mem)}
                    logging.info(f"Stats for {team}: cpu={response.cpu_usage}, disk={response.disk_space}, mem={response.used_mem}")
            except grpc.RpcError as e:
                logging.warning(f"Channel {ip} timed out: {str(e)}")
                stats[ip] = {'cpu': float('inf'), 'disk': float('inf'), 'mem': float('inf')}
        if not stats:
            logging.error("No active nodes found")
            return fileService_pb2.leastUtilizedResponse(primary="", replica="")
        sorted_nodes = sorted(stats.items(), key=lambda x: (x[1]['cpu'], x[1]['disk'], x[1]['mem']))
        primary = sorted_nodes[0][0]
        replica = sorted_nodes[1][0] if len(sorted_nodes) > 1 else primary
        logging.info(f"Selected nodes: Primary={primary}, Replica={replica}")
        if primary in self.activeChecker.get_active_channels():
            self.db.setData("leader_team1", primary)
            logging.info(f"Updated leader_team1 to {primary}")
        return fileService_pb2.leastUtilizedResponse(primary=primary, replica=replica)

    def UploadFile(self, request_iterator, context):
        self.updateClusterLeaders()
        leader_ip = self.clusterLeaders.get('team1')
        if not leader_ip:
            logging.error("No leader available for team1")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("No active leader available")
            return fileService_pb2.ack(success=False, message="No active leader available")
        logging.info(f"Forwarding upload to leader: {leader_ip}")
        try:
            with grpc.insecure_channel(leader_ip) as channel:
                grpc.channel_ready_future(channel).result(timeout=3)
                stub = fileService_pb2_grpc.FileserviceStub(channel)
                response = stub.UploadFile(request_iterator)
                logging.info(f"Upload response from {leader_ip}: Success={response.success}, Message={response.message}")
                return response
        except grpc.FutureTimeoutError:
            logging.error(f"Connection timeout to leader: {leader_ip}")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Failed to connect to {leader_ip}")
            return fileService_pb2.ack(success=False, message=f"Failed to connect to {leader_ip}")
        except grpc.RpcError as e:
            logging.error(f"Upload failed: {type(e).__name__}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Upload failed: {str(e)}")
            return fileService_pb2.ack(success=False, message=f"Upload failed: {str(e)}")

    def DownloadFile(self, request, context):
        self.updateClusterLeaders()
        leader_ip = self.clusterLeaders.get('team1')
        if not leader_ip:
            logging.error("No leader available for team1")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("No active leader available")
            return
        logging.info(f"Forwarding download to leader: {leader_ip}")
        try:
            with grpc.insecure_channel(leader_ip) as channel:
                grpc.channel_ready_future(channel).result(timeout=3)
                stub = fileService_pb2_grpc.FileserviceStub(channel)
                response_iterator = stub.DownloadFile(request)
                for chunk in response_iterator:
                    yield chunk
                logging.info(f"Download forwarded from {leader_ip}")
        except grpc.FutureTimeoutError:
            logging.error(f"Connection timeout to leader: {leader_ip}")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Failed to connect to {leader_ip}")
        except grpc.RpcError as e:
            logging.error(f"Download failed: {type(e).__name__}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Download failed: {str(e)}")

    def FileSearch(self, request, context):
        username = request.username
        filename = request.filename
        logging.info(f"FileSearch: username={username}, filename={filename}")
        if not username or not filename:
            logging.error("FileSearch: Username or filename is empty")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Username and filename cannot be empty")
            return fileService_pb2.ack(success=False, message="Username and filename cannot be empty")
        
        # Check local database first
        exists = self.db.keyExists(f"{username}_{filename}")
        if not exists:
            logging.info(f"FileSearch: File {username}_{filename} not found in local database")
            return fileService_pb2.ack(success=False, message=f"File {filename} does not exist for user {username}")
        
        # Forward to leader for confirmation
        self.updateClusterLeaders()
        leader_ip = self.clusterLeaders.get('team1')
        if not leader_ip:
            logging.error("No leader available for team1")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("No active leader available")
            return fileService_pb2.ack(success=False, message="No active leader available")
        
        logging.info(f"Forwarding FileSearch to leader: {leader_ip}")
        try:
            with grpc.insecure_channel(leader_ip) as channel:
                grpc.channel_ready_future(channel).result(timeout=3)
                stub = fileService_pb2_grpc.FileserviceStub(channel)
                response = stub.FileSearch(request)
                logging.info(f"FileSearch response from {leader_ip}: Success={response.success}, Message={response.message}")
                return response
        except grpc.FutureTimeoutError:
            logging.error(f"Connection timeout to leader: {leader_ip}")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Failed to connect to {leader_ip}")
            return fileService_pb2.ack(success=False, message=f"Failed to connect to {leader_ip}")
        except grpc.RpcError as e:
            logging.error(f"FileSearch failed: {type(e).__name__}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"FileSearch failed: {str(e)}")
            return fileService_pb2.ack(success=False, message=f"FileSearch failed: {str(e)}")

    def FileDelete(self, request, context):
        logging.info(f"FileDelete: username={request.username}, filename={request.filename}")
        if not self.db.keyExists(f"{request.username}_{request.filename}"):
            logging.warning(f"File {request.filename} does not exist for {request.username}")
            return fileService_pb2.ack(success=False, message=f"File {request.filename} does not exist.")

        fileMeta = self.db.parseMetaData(request.username, request.filename)
        if not fileMeta:
            logging.error(f"No metadata found for {request.username}_{request.filename}")
            return fileService_pb2.ack(success=False, message="Metadata not found.")

        self.updateClusterLeaders()
        leader_ip = self.clusterLeaders.get('team1')
        if not leader_ip:
            logging.error("No leader available for team1")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("No active leader available")
            return fileService_pb2.ack(success=False, message="No active leader available")

        try:
            self.delete_helper.deleteFileChunksAndMetaFromNodes(request.username, request.filename, [fileMeta])
            user_files = self.db.getUserFiles(request.username)
            file_list = ast.literal_eval(user_files) if user_files else []
            if request.filename in file_list:
                file_list.remove(request.filename)
                self.db.setData(request.username, str(file_list))
            logging.info(f"Metadata and user file list updated for {request.username}")
            return fileService_pb2.ack(success=True, message=f"File {request.filename} successfully deleted.")
        except Exception as e:
            logging.error(f"FileDelete failed: {type(e).__name__}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Delete failed: {str(e)}")
            return fileService_pb2.ack(success=False, message=f"Delete failed: {str(e)}")

    def getLeaderInfo(self, request, context):
        try:
            leader_addr = f"{request.ip}:{request.port}"
            if leader_addr not in self.activeChecker.get_active_channels():
                logging.warning(f"Ignoring inactive leader: {leader_addr}")
                return fileService_pb2.ack(success=False, message=f"Leader {leader_addr} is not active")
            success = self.db.setData(f"leader_{request.clusterName}", leader_addr)
            logging.info(f"Updated leader info: Cluster={request.clusterName}, Leader={leader_addr}, Redis_Success={success}")
            message = "Leader updated successfully" if success else "Failed to update leader"
            return fileService_pb2.ack(success=success, message=message)
        except Exception as e:
            logging.error(f"getLeaderInfo error: {type(e).__name__}: {str(e)}")
            return fileService_pb2.ack(success=False, message=f"Failed to update leader: {str(e)}")

    def UpdateFile(self, request_iterator, context):
        self.updateClusterLeaders()
        leader_ip = self.clusterLeaders.get('team1')
        if not leader_ip:
            logging.error("No leader available for team1")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("No active leader available")
            return fileService_pb2.ack(success=False, message="No active leader available")
        logging.info(f"Forwarding update to leader: {leader_ip}")
        try:
            with grpc.insecure_channel(leader_ip) as channel:
                grpc.channel_ready_future(channel).result(timeout=3)
                stub = fileService_pb2_grpc.FileserviceStub(channel)
                response = stub.UpdateFile(request_iterator)
                logging.info(f"Update response from {leader_ip}: Success={response.success}, Message={response.message}")
                return response
        except grpc.FutureTimeoutError:
            logging.error(f"Connection timeout to leader: {leader_ip}")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Failed to connect to {leader_ip}")
            return fileService_pb2.ack(success=False, message=f"Failed to connect to {leader_ip}")
        except grpc.RpcError as e:
            logging.error(f"Update failed: {type(e).__name__}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Update failed: {str(e)}")
            return fileService_pb2.ack(success=False, message=f"Update failed: {str(e)}")

    def FileList(self, request, context):
        username = request.username
        logging.info(f"FileList: username={username}")
        if not username:
            logging.error("FileList: Username is empty")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Username cannot be empty")
            return fileService_pb2.FileListResponse(Filenames="")
        
        self.updateClusterLeaders()
        leader_ip = self.clusterLeaders.get('team1')
        if not leader_ip:
            logging.error("No leader available for team1")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("No active leader available")
            return fileService_pb2.FileListResponse(Filenames="")
        
        logging.info(f"Forwarding FileList to leader: {leader_ip}")
        try:
            with grpc.insecure_channel(leader_ip) as channel:
                grpc.channel_ready_future(channel).result(timeout=3)
                stub = fileService_pb2_grpc.FileserviceStub(channel)
                response = stub.FileList(request)
                logging.info(f"FileList response from {leader_ip}: Filenames={response.Filenames}")
                return response
        except grpc.FutureTimeoutError:
            logging.error(f"Connection timeout to leader: {leader_ip}")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Failed to connect to {leader_ip}")
            return fileService_pb2.FileListResponse(Filenames="")
        except grpc.RpcError as e:
            logging.error(f"FileList failed: {type(e).__name__}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"FileList failed: {str(e)}")
            return fileService_pb2.FileListResponse(Filenames="")

def serve(hostIP, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    fileService_pb2_grpc.add_FileserviceServicer_to_server(SuperNode(hostIP, port), server)
    server.add_insecure_port(f'[::]:{port}')
    logging.info(f"Supernode started on {hostIP}:{port}")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.info("Starting supernode with config: hostIP=localhost, port=9000")
    serve("localhost", 9000)