import sys
import time
import grpc
import logging
import threading
from db import DB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | ActiveNodesChecker | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

class ActiveNodesChecker:
    def __init__(self):
        self.channel_ip_map = {}
        self.active_ip_channel_dict = {}
        self.db = DB()
        self.ip_addresses = self.get_all_available_ip_addresses()
        logging.info(f"Initial IPs loaded: {self.ip_addresses}")
        self.create_channel_list_for_available_ips(self.ip_addresses)
        self.db.setData("ip_addresses", self.get_string_from_ip_addresses_list(self.ip_addresses))
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.read_available_ip_addresses, daemon=True)
        self.monitor_thread.start()
        # Wait briefly to ensure initial heartbeats
        time.sleep(1)

    def read_available_ip_addresses(self):
        """Monitor IP addresses and update channels."""
        logging.info("Starting IP address monitoring")
        while True:
            time.sleep(0.5)
            try:
                ip_addresses_old = self.get_ip_address_list_from_string(
                    self.db.getData("ip_addresses") or b""
                )
                self.ip_addresses = self.get_all_available_ip_addresses()
                self.create_channel_list_for_available_ips(self.ip_addresses)
                self.db.setData(
                    "ip_addresses",
                    self.get_string_from_ip_addresses_list(self.ip_addresses)
                )
                if ip_addresses_old != self.ip_addresses:
                    logging.info(f"IP addresses changed: {self.ip_addresses}")
                self.heart_beat_checker()
            except Exception as e:
                logging.error(f"Error in read_available_ip_addresses: {type(e).__name__}: {str(e)}", exc_info=True)

    def get_all_available_ip_addresses(self):
        """Read IP addresses from iptable.txt."""
        ip_addresses = []
        try:
            with open('iptable.txt', 'r') as f:
                for line in f:
                    ip_port = line.strip()
                    if ip_port:
                        ip_addresses.append(ip_port)
            logging.info(f"Loaded IPs from iptable.txt: {ip_addresses}")
            return ip_addresses
        except FileNotFoundError:
            logging.error("iptable.txt not found")
            return []
        except Exception as e:
            logging.error(f"Error reading iptable.txt: {type(e).__name__}: {str(e)}", exc_info=True)
            return []

    def get_ip_address_list_from_string(self, ip_addresses):
        """Convert comma-separated IPs to list."""
        if isinstance(ip_addresses, bytes):
            ip_addresses = ip_addresses.decode('utf-8')
        return ip_addresses.split(',') if ip_addresses else []

    def get_string_from_ip_addresses_list(self, ip_address_list):
        """Convert IP list to comma-separated string."""
        return ','.join(ip_address_list) if ip_address_list else ""

    def create_channel_list_for_available_ips(self, ip_addresses):
        """Create gRPC channels for IPs."""
        self.channel_ip_map = {}
        for ip_address in ip_addresses:
            try:
                channel = grpc.insecure_channel(ip_address)
                self.channel_ip_map[channel] = ip_address
                logging.info(f"Created channel for {ip_address}")
            except Exception as e:
                logging.error(f"Failed to create channel for {ip_address}: {type(e).__name__}: {str(e)}", exc_info=True)

    def heart_beat_checker(self):
        """Check channel liveness."""
        for channel in list(self.channel_ip_map.keys()):
            ip = self.channel_ip_map.get(channel)
            if self.is_channel_alive(channel):
                if ip not in self.active_ip_channel_dict:
                    self.active_ip_channel_dict[ip] = channel
                    logging.info(f"Node active: {ip}")
            else:
                if ip in self.active_ip_channel_dict:
                    del self.active_ip_channel_dict[ip]
                    logging.warning(f"Node inactive: {ip}")

    def is_channel_alive(self, channel):
        """Check if channel is alive."""
        try:
            grpc.channel_ready_future(channel).result(timeout=2)  # Increased timeout
            return True
        except grpc.FutureTimeoutError as e:
            logging.warning(f"Channel timeout for {self.channel_ip_map.get(channel, 'unknown')}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Channel error for {self.channel_ip_map.get(channel, 'unknown')}: {type(e).__name__}: {str(e)}", exc_info=True)
            return False

    def get_active_channels(self):
        """Return active channels."""
        logging.info(f"Active channels: {list(self.active_ip_channel_dict.keys())}")
        return self.active_ip_channel_dict