from __future__ import print_function
import psutil
import grpc
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from heartbeat_pb2 import *
from heartbeat_pb2_grpc import *
from db import DB

class Heartbeat(HearBeatServicer):
    def __init__(self):
        try:
            primary_status = DB().getData("primaryStatus")
            self.primary = int(primary_status) if primary_status else 0
            print(f"Heartbeat initialized, primary={self.primary}")
        except Exception as e:
            print(f"Error initializing Heartbeat: {type(e).__name__}: {e}")
            self.primary = 0

    def isAlive(self, request, context):
        try:
            cpu_usage = str(psutil.cpu_percent())
            disk_space = str(psutil.virtual_memory()[2])
            used_mem = str(psutil.disk_usage('/')[3])
            stats = Stats(cpu_usage=cpu_usage, disk_space=disk_space, used_mem=used_mem)
            return stats
        except Exception as e:
            print(f"isAlive error: {type(e).__name__}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get stats: {str(e)}")
            return Stats()

    def getCPUusage(self):
        try:
            print('CPU % used', psutil.cpu_percent())
            print('physical memory % used:', psutil.virtual_memory()[2])
            print('Secondary memory % used', psutil.disk_usage('/')[3])
        except Exception as e:
            print(f"getCPUusage error: {type(e).__name__}: {e}")