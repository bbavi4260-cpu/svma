import socket
import threading
import json
import time
import sqlite3
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# MAIN CONFIGURATION & CONSTANTS
# ==============================================================================
RENDER_URL = "https://svmx.onrender.com"
PRIMARY_HTTP_PORT = 8080
SECONDARY_TCP_PORT = 8085
DB_FILE = "server_data.db"

DEFAULT_OPEN_ID = "GUEST_100000001"
DEFAULT_NICKNAME = "Master"
DEFAULT_LEVEL = 60
DEFAULT_DIAMONDS = 999999
DEFAULT_GOLD = 999999

# ==============================================================================
# 1. DATABASE MANAGEMENT SYSTEM
# ==============================================================================
def init_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                open_id TEXT UNIQUE NOT NULL,
                nickname TEXT NOT NULL,
                level INTEGER DEFAULT 60,
                exp INTEGER DEFAULT 999999,
                gold INTEGER DEFAULT 999999,
                diamond INTEGER DEFAULT 999999,
                vip_level INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("SELECT open_id FROM accounts WHERE open_id = ?", (DEFAULT_OPEN_ID,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO accounts (open_id, nickname, level, exp, gold, diamond, vip_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (DEFAULT_OPEN_ID, DEFAULT_NICKNAME, DEFAULT_LEVEL, 999999, DEFAULT_GOLD, DEFAULT_DIAMONDS, 10))
            conn.commit()
        conn.close()
        print("[DB INIT] Database ready.")
    except Exception as e:
        print(f"[DB ERROR] {e}")

def fetch_or_create_account(open_id=DEFAULT_OPEN_ID):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT uid, open_id, nickname, level, exp, gold, diamond, vip_level FROM accounts WHERE open_id = ?", (open_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "uid": row[0], "open_id": row[1], "nickname": row[2],
                "level": row[3], "exp": row[4], "gold": row[5],
                "diamond": row[6], "vip_level": row[7]
            }
    except:
        pass
    return {
        "uid": 100000001, "open_id": DEFAULT_OPEN_ID, "nickname": DEFAULT_NICKNAME,
        "level": DEFAULT_LEVEL, "exp": 999999, "gold": DEFAULT_GOLD,
        "diamond": DEFAULT_DIAMONDS, "vip_level": 10
    }

# ==============================================================================
# 2. PROTOBUF & BINARY PAYLOAD GENERATORS
# ==============================================================================
def generate_majorlogin_protobuf_stream():
    header = b"\x08\xc4\xd2\xd1\xd1\x02\x12\x02BR\x1a\x02BR\"\x02BR*\x04liveB\x05EAAcX1780855974140HENRRI63pku98nH\xc4\x80\x01R\x1b"
    url_bytes = RENDER_URL.encode('utf-8')
    middle = b"`\x00z\x02\x08\x01\xea\x01\x13"
    trailer = b"\xa0\x01\x00\xd5\x01\x00\xbb\x01\xdf\xa9\xd1\xd1\x06\xe1\x01\x13" + url_bytes + b"\xe9\x01\x0c\x02BR\x10\x01(\x010\x018\x01"
    return header + url_bytes + middle + url_bytes + trailer

def generate_netty_binary_packet(data_dict):
    json_bytes = json.dumps(data_dict).encode('utf-8')
    payload_len = len(json_bytes)
    header = bytearray([0x08, 0x00, (payload_len >> 8) & 0xFF, payload_len & 0xFF])
    return header + json_bytes

# ==============================================================================
# 3. LOADING SCREEN & ASSET MANIFEST BYPASS PAYLOADS
# ==============================================================================
def get_master_universal_payload(account=None):
    if not account:
        account = fetch_or_create_account(DEFAULT_OPEN_ID)

    current_time = int(time.time())
    
    return {
        "code": 0,
        "ret": 0,
        "status": "ok",
        "msg": "success",
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
        "need_role": False,
        "open_id": account["open_id"],
        "nickname": account["nickname"],
        "account_id": account["uid"],
        # CDN & Hot-Update Bypasses to clear Loading Screen
        "server_url": RENDER_URL + "/",
        "gate_ip": RENDER_URL + "/",
        "cdn_url": RENDER_URL + "/",
        "backup_cdn_url": RENDER_URL + "/",
        "img_cdn_url": RENDER_URL + "/",
        "core_url": RENDER_URL + "/",
        "test_url": RENDER_URL + "/",
        "network_log_server": RENDER_URL + "/",
        "web_log_server": RENDER_URL + "/",
        "need_track_hotupdate": False,
        "is_update_btn_show": False,
        "use_background_download": False,
        "use_background_download_lobby": False,
        "login_download_optionalpack": "",
        "data": {
            "account_id": account["uid"],
            "open_id": account["open_id"],
            "nickname": account["nickname"],
            "level": account["level"],
            "exp": account["exp"],
            "gold": account["gold"],
            "diamond": account["diamond"],
            "vip_level": account["vip_level"],
            "avatar_id": 1,
            "gender": 1,
            "character_id": 101,
            "has_role": True,
            "is_created": True,
            "in_lobby": True,
            "server_online": True,
            "maintenance": False,
            "server_time": current_time,
            "unlocked_characters": [101, 102, 103, 104, 105],
            "unlocked_weapons": [201, 202, 203, 204],
            "rank_points": 2400,
            "rank_tier": "Master"
        },
        "config": {
            "remote_version": "1.0.1",
            "remote_option_version": "1.0.1",
            "is_review_server": False,
            "force_to_restart_app": False,
            "country_code": "IN"
        }
    }

def get_hotupdate_manifest_payload():
    """Forces game to skip downloading any missing assets and bypass loading screen."""
    return {
        "code": 0,
        "ret": 0,
        "status": "ok",
        "msg": "success",
        "version": "1.0.1",
        "res_version": "1.0.1",
        "need_update": False,
        "is_force_update": False,
        "hot_update_url": RENDER_URL + "/",
        "file_list": [],
        "manifest": {}
    }

# ==============================================================================
# 4. HTTP GATEWAY HANDLER
# ==============================================================================
class FullMasterHttpGateway(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(f"[HTTP LOG] {self.client_address[0]} -> {self.path} - {format % args}")

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        self.process_incoming_request()

    def do_GET(self):
        self.process_incoming_request()

    def process_incoming_request(self):
        clean_path = self.path.lower().split('?')[0]
        print(f"[REQUEST ROUTE]: {clean_path}")

        # 1. Majorlogin Binary Stream
        if "majorlogin" in clean_path:
            binary_payload = generate_majorlogin_protobuf_stream()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(binary_payload)))
            self.end_headers()
            self.wfile.write(binary_payload)
            return

        # 2. Hotupdate / Asset Manifest Requests (Stops Loading Screen Freeze)
        if any(k in clean_path for k in ["hotupdate", "manifest", "res", "asset", "version", "check"]):
            print("[BYPASS] Hotupdate/Asset Manifest Request -> Bypassing download")
            self.reply_json(get_hotupdate_manifest_payload())
            return

        # 3. Config & General App Startup
        if any(k in clean_path for k in ["config", "client", "ver"]):
            print("[BYPASS] Config Request -> Sending Master Config")
            self.reply_json(get_master_universal_payload())
            return

        # 4. Auth / Login / OAuth
        if any(k in clean_path for k in ["auth", "guest", "login", "oauth", "token"]):
            print("[BYPASS] Login Request -> Granting Session")
            account = fetch_or_create_account(DEFAULT_OPEN_ID)
            self.reply_json({
                "code": 0, "ret": 0, "msg": "success", "status": "ok",
                "open_id": account["open_id"],
                "access_token": "MASTER_TOKEN_BYPASS_99831",
                "uid": str(account["uid"]),
                "has_role": True, "is_created": True
            })
            return

        # 5. Default Fallback -> Force Lobby Entry
        print("[BYPASS FALLBACK] Forcing Direct Lobby State")
        self.reply_json(get_master_universal_payload())

    def reply_json(self, data_dict):
        json_bytes = json.dumps(data_dict).encode('utf-8')
        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(json_bytes)))
        self.end_headers()
        self.wfile.write(json_bytes)

# ==============================================================================
# 5. RAW TCP SOCKET GATEWAY
# ==============================================================================
def handle_tcp_socket_client(client_socket, client_addr):
    try:
        client_socket.settimeout(10.0)
        while True:
            raw_data = client_socket.recv(8192)
            if not raw_data:
                break
            payload = get_master_universal_payload()
            response_binary = generate_netty_binary_packet(payload)
            client_socket.sendall(response_binary)
    except:
        pass
    finally:
        try:
            client_socket.close()
        except:
            pass

def launch_raw_tcp_gateway(host='0.0.0.0', port=SECONDARY_TCP_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((host, port))
        server_socket.listen(50)
        while True:
            client, addr = server_socket.accept()
            t = threading.Thread(target=handle_tcp_socket_client, args=(client, addr))
            t.daemon = True
            t.start()
    except:
        pass

# ==============================================================================
# 6. ENTRY POINT
# ==============================================================================
def start_tcp_server(host='0.0.0.0', port=PRIMARY_HTTP_PORT):
    init_database()
    
    tcp_thread = threading.Thread(target=launch_raw_tcp_gateway, args=(host, SECONDARY_TCP_PORT))
    tcp_thread.daemon = True
    tcp_thread.start()

    print(f"[HTTP SERVER ACTIVE] Listening on {host}:{port}")
    httpd = HTTPServer((host, port), FullMasterHttpGateway)
    httpd.serve_forever()

if __name__ == '__main__':
    start_tcp_server('0.0.0.0', PRIMARY_HTTP_PORT)
