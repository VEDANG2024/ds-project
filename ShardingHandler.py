import sys
import os
import grpc
import time
import yaml
import threading
import hashlib
import logging
from concurrent import futures

project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    logging.info(f"ShardingHandler.py: Added {project_dir} to sys.path")

try:
    import fileService_pb2
    import fileService_pb2_grpc
    import heartbeat_pb2
    import heartbeat_pb2_grpc
except ImportError as e:
    logging.error(f"Import error in ShardingHandler.py: {e}")
    raise

from db import DB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | ShardingHandler | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

class ShardingHandler:
    def __init__(self, activeNodesChecker):
        self.active_ip_channel_dict = activeNodesChecker.get_active_channels()
        self.db = DB()
        logging.info("ShardingHandler initialized with ActiveNodesChecker and DB")

    def writeShard(self, username, filename, hashVal, data):
        try:
            if not data:
                logging.error(f"writeShard: Empty data for username={username}, filename={filename}")
                return False
            logging.info(f"writeShard: username={username}, filename={filename}, hashVal={hashVal}, data_len={len(data)}")
            key = f"shard_{username}_{filename}_{hashVal}"
            if not isinstance(data, bytes):
                logging.error(f"writeShard: Expected bytes, got {type(data)}")
                return False
            success = self.db.setData(key, data)
            if success:
                logging.info(f"writeShard: Stored shard at key={key}, data_len={len(data)}")
            else:
                logging.error(f"writeShard: Failed to store shard at key={key}")
            return success
        except Exception as e:
            logging.error(f"writeShard error: {type(e).__name__}: {e}")
            return False

    def getShard(self, username, filename):
        try:
            logging.info(f"getShard: username={username}, filename={filename}")
            key_pattern = f"shard_{username}_{filename}_*"
            keys = self.db.client.keys(key_pattern)
            logging.info(f"getShard: Found keys={keys}")
            if not keys:
                logging.warning(f"getShard: No shard found for pattern={key_pattern}")
                return None
            # Take the first key (should only be one shard per file)
            key = keys[0].decode('utf-8') if isinstance(keys[0], bytes) else keys[0]
            data = self.db.getData(key)
            if data:
                logging.info(f"getShard: Retrieved key={key}, data_len={len(data)}")
            else:
                logging.warning(f"getShard: No data found for key={key}")
            return data
        except Exception as e:
            logging.error(f"getShard error: {type(e).__name__}: {e}")
            return None

    def deleteShard(self, username, filename):
        try:
            logging.info(f"deleteShard: username={username}, filename={filename}")
            key_pattern = f"shard_{username}_{filename}_*"
            keys = self.db.client.keys(key_pattern)
            logging.info(f"deleteShard: Found keys={keys}")
            if not keys:
                logging.info(f"deleteShard: No shards found for {username}_{filename}")
                return True
            for key in keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                self.db.deleteEntry(key_str)
                logging.info(f"deleteShard: Deleted key={key_str}")
            logging.info(f"deleteShard: Deleted {len(keys)} shards")
            return True
        except Exception as e:
            logging.error(f"deleteShard error: {type(e).__name__}: {e}")
            return False

    def fileExists(self, username, filename):
        try:
            logging.info(f"fileExists: username={username}, filename={filename}")
            key_pattern = f"shard_{username}_{filename}_*"
            keys = self.db.client.keys(key_pattern)
            exists = len(keys) > 0
            logging.info(f"fileExists: Result={exists}, keys={keys}")
            return exists
        except Exception as e:
            logging.error(f"fileExists error: {type(e).__name__}: {e}")
            return False

    def leastUtilizedNode(self):
        logging.info("Inside leastUtilizedNode method")
        return self.leastUtilizedNodeHelper()

    def leastUtilizedNodeHelper(self):
        logging.info("Inside leastUtilizedNodeHelper")
        minVal, minVal2 = float('inf'), float('inf')
        leastLoadedNode, leastLoadedNode2 = "", ""
        for ip, channel in self.active_ip_channel_dict.items():
            if self.isChannelAlive(channel):
                stub = heartbeat_pb2_grpc.HearBeatStub(channel)
                try:
                    stats = stub.isAlive(heartbeat_pb2.NodeInfo(ip="", port=""))
                    total = float(stats.cpu_usage) + float(stats.disk_space) + float(stats.used_mem)
                    avg = total / 3
                    logging.info(f"Node {ip}: cpu={stats.cpu_usage}, disk={stats.disk_space}, mem={stats.used_mem}, avg={avg}")
                    if avg < minVal:
                        minVal2 = minVal
                        minVal = avg
                        leastLoadedNode2 = leastLoadedNode
                        leastLoadedNode = ip
                    elif avg < minVal2:
                        minVal2 = avg
                        leastLoadedNode2 = ip
                except grpc.RpcError as e:
                    logging.warning(f"Failed to get stats for {ip}: {str(e)}")
        if not leastLoadedNode:
            logging.warning("No active nodes found")
            return -1
        logging.info(f"Selected nodes: Primary={leastLoadedNode}, Replica={leastLoadedNode2}")
        return leastLoadedNode, leastLoadedNode2

    def isChannelAlive(self, channel):
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
            return True
        except grpc.FutureTimeoutError:
            return False