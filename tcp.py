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
# 2. HTTP HANDLER (All REST Paths & Majorlogin Binary Handler)
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

        # Config Binary Payload: Replaces original local IP (192.168.100.44:8084) with active Render URL
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

        # Main Server Config Payload
        config_payload = {
            "code": 0,
            "ret": 0,
            "status": "ok",
            "is_server_open": True,
            "is_firewall_open": True,
            "need_track_hotupdate": False,
            "min_hint_size": 0,
            "billboard_cdn_url": "",
            "billboard_msg": "",
            "patchnote_url": "",
            "web_url": "",
            "billboard_bg_url": "",
            "max_store": "",
            "max_web": "",
            "max_video": "",
            "remote_version": "1.0.1",
            "remote_option_version": "1.0.1",
            "cdn_url": RENDER_URL + "/",
            "backup_cdn_url": RENDER_URL + "/",
            "server_url": RENDER_URL + "/",
            "is_review_server": False,
            "appstore_url": "",
            "force_to_restart_app": False,
            "country_code": "IN",
            "gdpr_version": 0,
            "client_ip": self.client_address[0] if self.client_address else "127.0.0.1",
            "maintenance_announcement": "",
            "maintenance_region": "",
            "need_check_ip_list": [],
            "network_log_server": RENDER_URL + "/",
            "web_log_server": RENDER_URL + "/",
            "login_failed_count": 0,
            "test_url": RENDER_URL + "/",
            "img_cdn_url": RENDER_URL + "/",
            "core_url": RENDER_URL + "/",
            "core_ip_list": [],
            "is_update_btn_show": False,
            "is_use_multi_download": False,
            "use_login_optional_download": False,
            "use_background_download": False,
            "use_background_download_lobby": False,
            "use_backgound_download_mem_thredshold": 0,
            "sigma_login": True,
            "sigma_switch": True,
            "enable_clear_mem_when_autopause": False,
            "space_required_in_GB": 0,
            "sigma_backup_url": RENDER_URL + "/",
            "login_download_optionalpack": ""
        }

        # Guest OAuth Response
        guest_payload = {
            "open_id": "GUEST_100000001",
            "access_token": "GUEST_TOKEN_SIGMA_ONLINE_8849301",
            "refresh_token": "GUEST_TOKEN_SIGMA_ONLINE_8849301",
            "expiry_time": 1817401047,
            "platform": 4,
            "uid": "100000001",
            "ret": 0,
            "code": 0,
            "msg": "success",
            "has_role": True,
            "is_created": True,
            "status": "ok"
        }

        # Full Master Lobby Data Payload
        master_lobby_payload = {
            "code": 0,
            "ret": 0,
            "msg": "success",
            "status": "ok",
            "is_server_open": True,
            "is_firewall_open": True,
            "server_status": 1,
            "maintenance": False,
            "has_role": True,
            "is_created": True,
            "open_id": "GUEST_100000001",
            "nickname": "Master",
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
                "unlocked_characters": [101, 102, 103, 104],
                "vip_level": 10,
                "server_time": int(time.time())
            }
        }

        # ROUTING LOGIC BY PATH KEYWORDS
        if "majorlogin" in path:
            print("[ROUTING] Majorlogin -> Sending Octet Binary Stream Config")
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(binary_config)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(binary_config)

        elif any(k in path for k in ["config", "ver", "client", "check"]):
            print("[ROUTING] Config Endpoint -> Sending Main Server Config")
            self.send_json_response(config_payload)

        elif any(k in path for k in ["guest", "oauth", "login"]):
            print("[ROUTING] Guest OAuth Endpoint -> Sending Authorized Guest Payload")
            self.send_json_response(guest_payload)

        elif any(k in path for k in ["role", "nickname", "create", "name", "player", "major", "lobby", "user"]):
            print("[ROUTING] Lobby / Role Sync -> Sending Full Master Lobby Payload")
            self.send_json_response(master_lobby_payload)

        else:
            print("[ROUTING] Fallback Endpoint -> Sending Universal Master Payload")
            self.send_json_response(master_lobby_payload)

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
# 3. RAW TCP SOCKET GATEWAY (Handles Direct Binary Socket Stream)
# -------------------------------------------------------------
def handle_tcp_client(client_socket, addr):
    print(f"[TCP CONNECTED]: {addr[0]}:{addr[1]}")
    try:
        client_socket.settimeout(5.0)
        data = client_socket.recv(8192)
        if not data:
            return

        print(f"[TCP RAW REQ]: {data[:30]}")

        ready_payload = {
            "code": 0,
            "ret": 0,
            "msg": "success",
            "status": "ok",
            "is_server_open": True,
            "is_firewall_open": True,
            "server_status": 1,
            "maintenance": False,
            "has_role": True,
            "is_created": True,
            "account_id": 100000001,
            "open_id": "GUEST_100000001",
            "nickname": "Master",
            "data": {
                "account_id": 100000001,
                "nickname": "Master", 
                "level": 60,
                "gold": 999999,
                "diamond": 999999,
                "has_role": True,
                "is_created": True
            }
        }
        json_bytes = json.dumps(ready_payload).encode('utf-8')
        
        # Binary Framing Header (Magic bytes + length)
        header = bytearray([0x08, 0x00, (len(json_bytes) >> 8) & 0xFF, len(json_bytes) & 0xFF])
        client_socket.sendall(header + json_bytes)
        print("[TCP RESPONSE] Netty Binary Stream Sent")
    except Exception as e:
        print(f"[TCP ERROR]: {e}")
    finally:
        client_socket.close()

# -------------------------------------------------------------
# 4. ENTRY POINT (Compatible with server.py imports)
# -------------------------------------------------------------
def start_tcp_server(host='0.0.0.0', port=8080):
    init_accounts_db()
    
    # Run Background Netty Binary Socket Listener on Port 8085
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

    # Run Main HTTP Handler on Primary Port (8080)
    print(f"[HTTP SERVER] Listening on {host}:{port}")
    httpd = HTTPServer((host, port), MajorLoginHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    start_tcp_server()
