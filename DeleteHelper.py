import sys
import os
import grpc
import time
import yaml
import threading
import hashlib
import logging
import concurrent.futures

# Add project directory to sys.path
project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    logging.info(f"DeleteHelper.py: Added {project_dir} to sys.path")

try:
    import fileService_pb2
    import fileService_pb2_grpc
    import heartbeat_pb2
    import heartbeat_pb2_grpc
    import fluffy_pb2
    import fluffy_pb2_grpc
except ImportError as e:
    logging.error(f"Import error in DeleteHelper.py: {e}")
    raise

from db import DB
from ShardingHandler import ShardingHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | DeleteHelper | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

class DeleteHelper:
    def __init__(self, hostname, server_port, activeNodesChecker):
        self.serverAddress = f"{hostname}:{server_port}"
        self.activeNodesChecker = activeNodesChecker
        self.db = DB()
        self.sharding_handler = ShardingHandler(self.activeNodesChecker)
        logging.info(f"DeleteHelper initialized for {self.serverAddress}")

    def deleteFileChunksAndMetaFromNodes(self, username, filename, metaData):
        logging.info(f"deleteFileChunksAndMetaFromNodes: username={username}, filename={filename}, metaData={metaData}")
        active_ip_channel_dict = self.activeNodesChecker.get_active_channels()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for meta in metaData:
                node, replicaNode = meta[0], meta[1]
                futures.append(executor.submit(self.deleteDataAndMetaFromIndividualChunk, node, replicaNode, username, filename))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    success, message = future.result()
                    logging.info(message)
                except Exception as e:
                    logging.error(f"Thread execution failed: {type(e).__name__}: {str(e)}")

        logging.info("All deletion tasks completed")

    def deleteDataAndMetaFromIndividualChunk(self, node, replicaNode, username, filename):
        logging.info(f"deleteDataAndMetaFromIndividualChunk: node={node}, replicaNode={replicaNode}, username={username}, filename={filename}")
        metaDataKey = f"{username}_{filename}"
        active_ip_channel_dict = self.activeNodesChecker.get_active_channels()
        success = True
        messages = []

        # Delete local metadata if this is the current node
        if node == self.serverAddress or replicaNode == self.serverAddress:
            if self.db.keyExists(metaDataKey):
                self.db.deleteEntry(metaDataKey)
                messages.append(f"Deleted metadata {metaDataKey} from local node {self.serverAddress}")
            else:
                messages.append(f"No metadata {metaDataKey} found on local node {self.serverAddress}")

        # Delete shards locally
        if self.sharding_handler.fileExists(username, filename):
            if self.sharding_handler.deleteShard(username, filename):
                messages.append(f"Deleted shards for {username}_{filename} from local node {self.serverAddress}")
            else:
                success = False
                messages.append(f"Failed to delete shards for {username}_{filename} from local node {self.serverAddress}")
        else:
            messages.append(f"No shards found for {username}_{filename} on local node {self.serverAddress}")

        # Delete from remote node
        if node != self.serverAddress and node in active_ip_channel_dict:
            try:
                with grpc.insecure_channel(node) as channel:
                    stub = fileService_pb2_grpc.FileserviceStub(channel)
                    response = stub.FileDelete(fileService_pb2.FileInfo(username=username, filename=filename))
                    if response.success:
                        messages.append(f"Successfully deleted file from node {node}")
                    else:
                        success = False
                        messages.append(f"Failed to delete file from node {node}: {response.message}")
            except grpc.RpcError as e:
                success = False
                messages.append(f"gRPC error deleting from node {node}: {str(e)}")

        # Delete from replica node
        if replicaNode != self.serverAddress and replicaNode in active_ip_channel_dict:
            try:
                with grpc.insecure_channel(replicaNode) as channel:
                    stub = fileService_pb2_grpc.FileserviceStub(channel)
                    response = stub.FileDelete(fileService_pb2.FileInfo(username=username, filename=filename))
                    if response.success:
                        messages.append(f"Successfully deleted file from replica node {replicaNode}")
                    else:
                        success = False
                        messages.append(f"Failed to delete file from replica node {replicaNode}: {response.message}")
            except grpc.RpcError as e:
                success = False
                messages.append(f"gRPC error deleting from replica node {replicaNode}: {str(e)}")

        return success, "; ".join(messages)