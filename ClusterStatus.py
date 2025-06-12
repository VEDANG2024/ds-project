from concurrent import futures
import grpc
import time
import threading
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import fileService_pb2
    import fileService_pb2_grpc
    import heartbeat_pb2
    import heartbeat_pb2_grpc
    import fluffy_pb2
    import fluffy_pb2_grpc
    print(f"ClusterStatus: fileService_pb2_grpc loaded: {hasattr(fileService_pb2_grpc, 'FileserviceStub')}")
    print(f"ClusterStatus: fileService_pb2 loaded: {hasattr(fileService_pb2, 'ClusterStats')}")
except ImportError as e:
    print(f"Import error in ClusterStatus: {e}")
    raise
from db import *

class ClusterStatus():
    def __init__(self):
        print("ClusterStatus initialized")
        print(f"fileService_pb2_grpc available: {hasattr(fileService_pb2_grpc, 'FileserviceStub')}")

    def leastUtilizedNode(self, clusterList):
        print("In leastUtilizedNode, clusterList:", clusterList)
        minVal, minVal2 = 301.00, 301.00
        leastLoadedNode, leastLoadedNode2 = "", ""
        clusterName, clusterName2 = "", ""
        try:
            for cluster in clusterList:
                print(f"Processing cluster: {cluster}")
                channel = self.isChannelAlive(clusterList[cluster])
                if channel:
                    try:
                        stub = fileService_pb2_grpc.FileserviceStub(channel)
                        print(f"Created stub for {clusterList[cluster]}")
                        stats = stub.getClusterStats(fileService_pb2.Empty())
                        print(f"Stats for {cluster}: cpu={stats.cpu_usage}, disk={stats.disk_space}, mem={stats.used_mem}")
                        total = 300.00 - (float(stats.cpu_usage) + float(stats.disk_space) + float(stats.used_mem))
                        if (total/3) < minVal:
                            minVal2 = minVal
                            minVal = total/3
                            leastLoadedNode2 = leastLoadedNode
                            clusterName2 = clusterName
                            leastLoadedNode = clusterList[cluster]
                            clusterName = cluster
                        elif (total/3) < minVal2:
                            minVal2 = total/3
                            leastLoadedNode2 = clusterList[cluster]
                            clusterName2 = cluster
                    except Exception as e:
                        print(f"Error getting stats for {clusterList[cluster]}: {e}")
                        continue
                    finally:
                        channel.close()
        except Exception as e:
            print(f"Error during cluster iteration: {e}")
            raise
        if leastLoadedNode == "":
            print("No active nodes found")
            return -1, -1, -1, -1
        print(f"Selected nodes: primary={leastLoadedNode}, replica={leastLoadedNode2}")
        return leastLoadedNode, leastLoadedNode2, clusterName, clusterName2

    def isChannelAlive(self, ip_address):
        print(f"Checking if channel is alive for {ip_address}")
        try:
            channel = grpc.insecure_channel('{}'.format(ip_address))
            grpc.channel_ready_future(channel).result(timeout=1)
            print(f"Channel {ip_address} is alive")
            return channel
        except grpc.FutureTimeoutError:
            print(f"Channel {ip_address} timed out")
            return False