import socket
import threading
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Base Configuration - Your Active Render Service URL
RENDER_URL = "https://svmx.onrender.com"

# -------------------------------------------------------------
# 1. HTTP HANDLER (Handles Vercel /Majorlogin & Web REST APIs)
# -------------------------------------------------------------
class MajorLoginHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[HTTP LOG] {self.address_string()} - {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_POST(self):
        self.process_request()

    def do_GET(self):
        self.process_request()

    def process_request(self):
        path = self.path.lower()
        print(f"[HTTP REQUEST PATH]: {path}")

        # Constructing Binary Protobuf Config File Payload
        # Replaces original local IP (192.168.100.44:8084) with active Render URL
        binary_config = (
            b"\x08\xc4\xd2\xd1\xd1\x02\x12\x02BR\x1a\x02BR\"\x02BR*\x04liveB\x05EAAcX"
            b"1780855974140HENRRI63pku98nH\xc4\x80\x01R\x1b"
            + RENDER_URL.encode('utf-8') + 
            b"`\x00z\x02\x08\x01\xea\x01\x13"
            + RENDER_URL.encode('utf-8') + 
            b"\xa0\x01\x00\xd5\x01\x00\xbb\x01\xdf\xa9\xd1\xd1\x06\xe1\x01\x13"
            + RENDER_URL.encode('utf-8') + 
            b"\xe9\x01\x0c\x02BR\x10\x01(\x010\x018\x01"
        )

        # Standard Master JSON Response (Unlocks Server & Maintenance)
        json_fallback = {
            "code": 0,
            "ret": 0,
            "status": "ok",
            "msg": "success",
            "is_server_open": True,
            "is_firewall_open": True,
            "server_status": 1,
            "maintenance": False,
            "has_role": True,
            "is_created": True,
            "server_url": RENDER_URL,
            "gate_ip": RENDER_URL,
            "data": {
                "account_id": 100000001,
                "open_id": "GUEST_100000001",
                "nickname": "Master",
                "level": 60,
                "gold": 999999,
                "diamond": 999999,
                "has_role": True,
                "is_created": True
            }
        }

        if "majorlogin" in path or "login" in path:
            print("[ROUTING MATCH] Majorlogin -> Sending Binary Config File Payload")
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(binary_config)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(binary_config)
        else:
            print("[ROUTING MATCH] Generic REST -> Sending HTTP JSON Payload")
            body = json.dumps(json_fallback).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)


# -------------------------------------------------------------
# 2. RAW TCP SOCKET GATEWAY (Handles Direct Netty Game Packets)
# -------------------------------------------------------------
def handle_tcp_client(client_socket, addr):
    print(f"[TCP CONNECTED]: {addr[0]}:{addr[1]}")
    try:
        client_socket.settimeout(5.0)
        data = client_socket.recv(4096)
        if not data:
            return

        print(f"[TCP RAW REQ]: {data[:30]}")

        # Master Lobby Bypass Data
        ready_payload = {
            "code": 0,
            "ret": 0,
            "msg": "success",
            "is_server_open": True,
            "has_role": True,
            "is_created": True,
            "data": {
                "nickname": "Master", 
                "level": 60,
                "gold": 999999,
                "diamond": 999999
            }
        }
        json_bytes = json.dumps(ready_payload).encode('utf-8')
        
        # Binary Protobuf Framing Magic Header
        header = bytearray([0x08, 0x00, (len(json_bytes) >> 8) & 0xFF, len(json_bytes) & 0xFF])
        client_socket.sendall(header + json_bytes)
        print("[TCP RESPONSE] Binary Framing Sent Successfully")
    except Exception as e:
        print(f"[TCP ERROR]: {e}")
    finally:
        client_socket.close()

# EXACT FUNCTION NAME EXPECTED BY SERVER.PY
def start_tcp_server(host='0.0.0.0', port=8080):
    # Launch Background Socket Server on Port 8085
    tcp_port = 8085
    def run_raw_socket():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, tcp_port))
        server.listen(50)
        print(f"[TCP GATEWAY ACTIVE] Listening on {host}:{tcp_port}")
        while True:
            try:
                client_socket, addr = server.accept()
                t = threading.Thread(target=handle_tcp_client, args=(client_socket, addr))
                t.daemon = True
                t.start()
            except:
                break

    socket_thread = threading.Thread(target=run_raw_socket)
    socket_thread.daemon = True
    socket_thread.start()

    # Launch HTTP Majorlogin Web Server on Port 8080
    print(f"[HTTP GATEWAY ACTIVE] Listening on {host}:{port}")
    httpd = HTTPServer((host, port), MajorLoginHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    start_tcp_server()
