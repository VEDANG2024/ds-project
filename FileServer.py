import sys
import os
import grpc
import time
import threading
import psutil
import hashlib
import redis
import math
import yaml
import logging
from concurrent import futures

project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    logging.info(f"FileServer.py: Added {project_dir} to sys.path")

try:
    import fileService_pb2
    import fileService_pb2_grpc
    import heartbeat_pb2
    import heartbeat_pb2_grpc
    import fluffy_pb2
    import fluffy_pb2_grpc
except ImportError as e:
    logging.error(f"Import error in FileServer.py: {e}")
    raise

from db import DB
from ShardingHandler import ShardingHandler
from ActiveNodesChecker import ActiveNodesChecker
from RaftHelper import RaftHelper
from DeleteHelper import DeleteHelper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

class FileServer(fileService_pb2_grpc.FileserviceServicer):
    def __init__(self, hostname, port, activeNodesChecker, shardingHandler, super_node_address):
        self.activeNodesChecker = activeNodesChecker
        self.shardingHandler = shardingHandler
        self.hostname = hostname
        self.port = port
        self.node_id = f"{hostname}:{port}"
        self.super_node_address = super_node_address
        self.channel = grpc.insecure_channel(self.super_node_address)
        self.stub = fileService_pb2_grpc.FileserviceStub(self.channel)
        self.db = DB()
        self.raft_helper = RaftHelper(hostname, port, port + 1, activeNodesChecker, super_node_address)
        self.delete_helper = DeleteHelper(hostname, str(port), activeNodesChecker)
        logging.getLogger().handlers[0].setFormatter(
            logging.Formatter(f'%(asctime)s | %(levelname)s | Node {self.node_id} | %(message)s')
        )
        logging.getLogger().handlers[1].setFormatter(
            logging.Formatter(f'%(asctime)s | %(levelname)s | Node {self.node_id} | %(message)s')
        )
        logging.info(f"FileServer initialized for {hostname}:{port}")

    def getClusterStats(self, request, context):
        logging.info("Inside getClusterStats")
        try:
            stats = psutil.virtual_memory()
            response = fileService_pb2.ClusterStats(
                cpu_usage=str(psutil.cpu_percent()),
                disk_space=str(psutil.disk_usage('/').percent),
                used_mem=str(stats.percent)
            )
            logging.info(f"Returning ClusterStats: cpu={response.cpu_usage}, disk={response.disk_space}, mem={response.used_mem}")
            return response
        except Exception as e:
            logging.error(f"Error in getClusterStats: {type(e).__name__}: {e}")
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details(f"Exception in getClusterStats: {str(e)}")
            raise

    def UploadFile(self, request_iterator, context):
        if not self.raft_helper.is_leader():
            logging.warning("Upload rejected: Not the leader")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("This node is not the leader")
            return fileService_pb2.ack(success=False, message="Operation failed: Not the leader")

        logging.info("Inside primary upload")
        username, filename = None, None
        data_chunks = []
        seq_nos = set()
        for request in request_iterator:
            if username is None:
                username = request.username
                filename = request.filename
            if not request.data:
                logging.warning(f"Empty chunk received: seqNo={request.seqNo}")
                continue
            if request.seqNo in seq_nos:
                logging.error(f"Duplicate seqNo={request.seqNo} received for {username}_{filename}")
                return fileService_pb2.ack(success=False, message="Duplicate sequence number detected")
            seq_nos.add(request.seqNo)
            data_chunks.append((request.seqNo, request.data))
            logging.info(f"Received chunk: seqNo={request.seqNo}, size={len(request.data)}")

        if not username or not filename:
            logging.error("Upload failed: Missing username or filename")
            return fileService_pb2.ack(success=False, message="Missing username or filename")

        if not data_chunks:
            logging.error(f"Upload failed: No valid data chunks received for {username}_{filename}")
            return fileService_pb2.ack(success=False, message="No valid data chunks received")

        if self.db.keyExists(f"{username}_{filename}"):
            logging.warning(f"File {username}_{filename} already exists")
            return fileService_pb2.ack(success=False, message="File already exists for this user. Please rename or delete file first.")

        sorted_chunks = sorted(data_chunks, key=lambda x: x[0])
        finalData = b""
        for seqNo, chunk in sorted_chunks:
            finalData += chunk
            logging.info(f"Combined chunk: seqNo={seqNo}, chunk_size={len(chunk)}, total_size={len(finalData)}")

        if not finalData:
            logging.error(f"Upload failed: Combined data is empty for {username}_{filename}")
            return fileService_pb2.ack(success=False, message="No data received after combining chunks")

        hashVal = hashlib.md5(finalData).hexdigest()
        logging.info(f"Computed hashVal={hashVal} for {username}_{filename}, data_len={len(finalData)}")
        success = self.shardingHandler.writeShard(username, filename, hashVal, finalData)
        if success:
            self.db.saveUserFile(username, filename)
            self.db.saveMetaData(username, filename, self.node_id, self.node_id)
            logging.info(f"Saved file: {username}_{filename}, Hash={hashVal}, ShardKey=shard_{username}_{filename}_{hashVal}")
            return fileService_pb2.ack(success=True, message="Successfully uploaded to primary.")
        else:
            logging.error(f"Failed to save file: {username}_{filename}")
            return fileService_pb2.ack(success=False, message="Failed to upload to primary.")

    def DownloadFile(self, request, context):
        if not self.raft_helper.is_leader():
            logging.warning("Download rejected: Not the leader")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("This node is not the leader")
            return fileService_pb2.FileData()

        username = request.username
        filename = request.filename
        logging.info(f"DownloadFile: {username}_{filename}")
        if not self.db.keyExists(f"{username}_{filename}"):
            logging.warning(f"File {username}_{filename} does not exist")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("File does not exist")
            return fileService_pb2.FileData()

        data = self.shardingHandler.getShard(username, filename)
        if data is None:
            logging.error(f"Shard not found for {username}_{filename}, checked key pattern=shard_{username}_{filename}_*")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Shard not found")
            return fileService_pb2.FileData()

        logging.info(f"Data retrieved: {len(data)} bytes for {username}_{filename}")
        CHUNK_SIZE = 1024 * 1024
        seqNo = 0
        for i in range(0, len(data), CHUNK_SIZE):
            chunk = data[i:i + CHUNK_SIZE]
            yield fileService_pb2.FileData(
                username=username,
                filename=filename,
                data=chunk,
                seqNo=seqNo
            )
            seqNo += 1
        logging.info(f"Download successful: {username}_{filename}")

    def FileSearch(self, request, context):
        username = request.username
        filename = request.filename
        logging.info(f"FileSearch: {username}_{filename}")
        if not username or not filename:
            logging.error("FileSearch: Username or filename is empty")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Username and filename cannot be empty")
            return fileService_pb2.ack(success=False, message="Username and filename cannot be empty")
        
        exists = self.db.keyExists(f"{username}_{filename}")
        message = f"File '{filename}' exists for user '{username}'" if exists else f"File '{filename}' does not exist for user '{username}'"
        logging.info(f"FileSearch result: exists={exists}, message={message}")
        return fileService_pb2.ack(success=exists, message=message)

    def FileDelete(self, request, context):
        logging.info(f"FileDelete: {request.username}_{request.filename}, NodeRole={'Leader' if self.raft_helper.is_leader() else 'Follower'}")
        if not self.raft_helper.is_leader():
            logging.warning("Delete rejected: Not the leader")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("This node is not the leader")
            return fileService_pb2.ack(success=False, message="Operation failed: Not the leader")

        username = request.username
        filename = request.filename
        if not self.db.keyExists(f"{username}_{filename}"):
            logging.warning(f"File {username}_{filename} does not exist")
            return fileService_pb2.ack(success=False, message="File does not exist")

        fileMeta = self.db.parseMetaData(username, filename)
        if not fileMeta:
            logging.error(f"No metadata found for {username}_{filename}")
            return fileService_pb2.ack(success=False, message="Metadata not found")

        try:
            self.delete_helper.deleteFileChunksAndMetaFromNodes(username, filename, [fileMeta])
            self.db.deleteEntry(f"{username}_{filename}")
            self.shardingHandler.deleteShard(username, filename)
            logging.info(f"File {username}_{filename} deleted successfully")
            return fileService_pb2.ack(success=True, message="Successfully deleted")
        except Exception as e:
            logging.error(f"FileDelete failed: {type(e).__name__}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Delete failed: {str(e)}")
            return fileService_pb2.ack(success=False, message=f"Delete failed: {str(e)}")

    def FileList(self, request, context):
        username = request.username
        logging.info(f"FileList: username={username}, NodeRole={'Leader' if self.raft_helper.is_leader() else 'Follower'}")
        if not self.raft_helper.is_leader():
            logging.warning("FileList rejected: Not the leader")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("This node is not the leader")
            return fileService_pb2.FileListResponse(Filenames="")
        
        if not username:
            logging.error("FileList: Username is empty")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Username cannot be empty")
            return fileService_pb2.FileListResponse(Filenames="")
        
        files = self.db.getUserFiles(username)
        logging.info(f"FileList result: username={username}, files={files}")
        return fileService_pb2.FileListResponse(Filenames=str(files) if files else "")

    def getLeaderInfo(self, request, context):
        success = self.db.setData(f"leader_{request.clusterName}", f"{request.ip}:{request.port}")
        logging.info(f"Leader info updated: Cluster={request.clusterName}, Leader={request.ip}:{request.port}, Success={success}")
        message = "Leader updated" if success else "Failed to update leader"
        return fileService_pb2.ack(success=success, message=message)

    def UpdateFile(self, request_iterator, context):
        if not self.raft_helper.is_leader():
            logging.warning("Update rejected: Not the leader")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("This node is not the leader")
            return fileService_pb2.ack(success=False, message="Operation failed: Not the leader")

        logging.info("Inside primary update")
        username, filename = None, None
        data_chunks = []
        seq_nos = set()
        for request in request_iterator:
            if username is None:
                username = request.username
                filename = request.filename
            if not request.data:
                logging.warning(f"Empty chunk received: seqNo={request.seqNo}")
                continue
            if request.seqNo in seq_nos:
                logging.error(f"Duplicate seqNo={request.seqNo} received for {username}_{filename}")
                return fileService_pb2.ack(success=False, message="Duplicate sequence number detected")
            seq_nos.add(request.seqNo)
            data_chunks.append((request.seqNo, request.data))
            logging.info(f"Received chunk: seqNo={request.seqNo}, size={len(request.data)}")

        if not username or not filename:
            logging.error("Update failed: Missing username or filename")
            return fileService_pb2.ack(success=False, message="Missing username or filename")

        if not data_chunks:
            logging.error(f"Update failed: No valid data chunks received for {username}_{filename}")
            return fileService_pb2.ack(success=False, message="No valid data chunks received")

        if not self.db.keyExists(f"{username}_{filename}"):
            logging.warning(f"File {username}_{filename} does not exist")
            return fileService_pb2.ack(success=False, message="File does not exist. Cannot update.")

        sorted_chunks = sorted(data_chunks, key=lambda x: x[0])
        finalData = b""
        for seqNo, chunk in sorted_chunks:
            finalData += chunk
            logging.info(f"Combined chunk: seqNo={seqNo}, chunk_size={len(chunk)}, total_size={len(finalData)}")

        if not finalData:
            logging.error(f"Update failed: Combined data is empty for {username}_{filename}")
            return fileService_pb2.ack(success=False, message="No data received after combining chunks")

        newHashVal = hashlib.md5(finalData).hexdigest()
        logging.info(f"Computed new hashVal={newHashVal} for {username}_{filename}, data_len={len(finalData)}")

        self.shardingHandler.deleteShard(username, filename)
        success = self.shardingHandler.writeShard(username, filename, newHashVal, finalData)
        if success:
            self.db.saveMetaData(username, filename, self.node_id, self.node_id)
            logging.info(f"Updated file: {username}_{filename}, New Hash={newHashVal}")
            return fileService_pb2.ack(success=True, message="Successfully updated the file.")
        else:
            logging.error(f"Failed to update file: {username}_{filename}")
            return fileService_pb2.ack(success=False, message="Failed to update the file.")