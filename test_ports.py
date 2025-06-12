import socket
import time

ports = [3001, 4001, 5001, 6001, 7001, 8001]
print(f"Testing Raft ports at {time.ctime()}")
for port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', port))
    if result == 0:
        print(f"Port {port} is open")
    else:
        print(f"Port {port} is closed or unreachable (error code: {result})")
    sock.close()