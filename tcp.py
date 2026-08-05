import socket
import threading
import json
import time
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler

# Base Configuration
RENDER_URL = "https://svmx.onrender.com"

# -------------------------------------------------------------
# 1. DATABASE INITIALIZATION
# -------------------------------------------------------------
def init_accounts_db():
    try:
        conn = sqlite3.connect('accounts.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                level INTEGER DEFAULT 60,
                diamonds INTEGER DEFAULT 999999,
                gold INTEGER DEFAULT 999999
            )
        ''')
        conn.commit()
        conn.close()
        print("[DATABASE] Player database initialized.")
    except Exception as e:
        print(f"[DATABASE ERROR] {e}")

# -------------------------------------------------------------
# 2. HTTP HANDLER (Always Force Lobby & Server Online Response)
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
        print(f"[HTTP REQ PATH]: {path}")

        # Config Binary Payload: Hardcoded Render Redirect
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

        # UNIVERSAL LOBBY BYPASS RESPONSE (Always Says Server Online, Maintenance False & Go to Lobby)
        universal_online_payload = {
            "code": 0,
            "ret": 0,
            "status": "ok",
            "msg": "server online",
            "server_online": True,
            "is_server_open": True,
            "is_firewall_open": True,
            "server_status": 1,
            "maintenance": False,
            "service_status_maintenance": False,
            "lobby_status": "entered",
            "action": "go_to_lobby",
            "has_role": True,
            "is_created": True,
            "open_id": "GUEST_100000001",
            "nickname": "Master",
            "server_url": RENDER_URL + "/",
            "gate_ip": RENDER_URL + "/",
            "cdn_url": RENDER_URL + "/",
            "data": {
                "account_id": 100000001,
                "open_id": "GUEST_100000001",
                "nickname": "Master",
                "level": 60,
                "exp": 999999,
                "gold": 999999,
                "diamond": 999999,
                "avatar_id": 1,
                "gender": 1,
                "character_id": 101,
                "has_role": True,
                "is_created": True,
                "in_lobby": True,
                "server_online": True,
                "maintenance": False,
                "server_time": int(time.time())
            }
        }

        # Majorlogin Binary Stream Check
        if "majorlogin" in path:
            print("[ROUTING] Majorlogin -> Sending Octet Binary Config")
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(binary_config)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(binary_config)
        else:
            # HAR DOOSRI REQ KO DRECT ONLINE & LOBBY WALA RESPONSE DENA
            print(f"[ROUTING] {path} -> Force Server Online, Maintenance False & Enter Lobby")
            self.send_json_response(universal_online_payload)

    def send_json_response(self, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

# -------------------------------------------------------------
# 3. RAW TCP SOCKET GATEWAY (Force Direct Lobby Packet)
# -------------------------------------------------------------
def handle_tcp_client(client_socket, addr):
    print(f"[TCP CONNECTED]: {addr[0]}:{addr[1]}")
    try:
        client_socket.settimeout(5.0)
        data = client_socket.recv(8192)
        if not data:
            return

        print(f"[TCP RAW REQ]: {data[:30]}")

        # Direct TCP Lobby Payload
        tcp_lobby_payload = {
            "code": 0,
            "ret": 0,
            "msg": "server online",
            "status": "ok",
            "server_online": True,
            "is_server_open": True,
            "maintenance": False,
            "service_status_maintenance": False,
            "lobby_status": "entered",
            "has_role": True,
            "is_created": True,
            "nickname": "Master",
            "data": {
                "nickname": "Master", 
                "level": 60,
                "gold": 999999,
                "diamond": 999999,
                "in_lobby": True,
                "server_online": True,
                "maintenance": False
            }
        }
        json_bytes = json.dumps(tcp_lobby_payload).encode('utf-8')
        
        # Binary Framing Header
        header = bytearray([0x08, 0x00, (len(json_bytes) >> 8) & 0xFF, len(json_bytes) & 0xFF])
        client_socket.sendall(header + json_bytes)
        print("[TCP RESPONSE] Online & Lobby Packet Sent")
    except Exception as e:
        print(f"[TCP ERROR]: {e}")
    finally:
        client_socket.close()

# -------------------------------------------------------------
# 4. ENTRY POINT
# -------------------------------------------------------------
def start_tcp_server(host='0.0.0.0', port=8080):
    init_accounts_db()
    
    tcp_port = 8085
    def run_raw_socket():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, tcp_port))
        server.listen(50)
        print(f"[TCP SOCKET SERVER] Listening on {host}:{tcp_port}")
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

    print(f"[HTTP SERVER] Listening on {host}:{port}")
    httpd = HTTPServer((host, port), MajorLoginHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    start_tcp_server()
