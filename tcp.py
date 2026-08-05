import socket
import threading
import json
import time
import sqlite3
import os
import sys
import struct
import base64
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# MAIN CONFIGURATION & CONSTANTS
# ==============================================================================
RENDER_URL = "https://svmx.onrender.com"
PRIMARY_HTTP_PORT = 8080
SECONDARY_TCP_PORT = 8085
DB_FILE = "init_db.py"

# Master Account Hardcoded Fallbacks
DEFAULT_OPEN_ID = "GUEST_100000001"
DEFAULT_NICKNAME = "Master"
DEFAULT_LEVEL = 60
DEFAULT_DIAMONDS = 999999
DEFAULT_GOLD = 999999

# ==============================================================================
# 1. DATABASE MANAGEMENT SYSTEM (SQLite Persistent Storage)
# ==============================================================================
def init_database():
    """Initializes sqlite database for user profiles, inventory, and stats."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Table 1: Account Profiles
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

        # Table 2: User Inventories & Characters
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                open_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                amount INTEGER DEFAULT 1,
                FOREIGN KEY(open_id) REFERENCES accounts(open_id)
            )
        ''')

        # Default Master Account Seeding
        cursor.execute("SELECT open_id FROM accounts WHERE open_id = ?", (DEFAULT_OPEN_ID,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO accounts (open_id, nickname, level, exp, gold, diamond, vip_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (DEFAULT_OPEN_ID, DEFAULT_NICKNAME, DEFAULT_LEVEL, 999999, DEFAULT_GOLD, DEFAULT_DIAMONDS, 10))
            conn.commit()
            print(f"[DB INIT] Created default master account '{DEFAULT_NICKNAME}' successfully.")
            
        conn.close()
        print("[DB INIT] Database structure initialized successfully.")
    except Exception as e:
        print(f"[DB ERROR] Database initialization failed: {e}")

def fetch_or_create_account(open_id=DEFAULT_OPEN_ID):
    """Retrieves account info or auto-registers new client requests."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT uid, open_id, nickname, level, exp, gold, diamond, vip_level FROM accounts WHERE open_id = ?", (open_id,))
        row = cursor.fetchone()
        
        if row:
            account_data = {
                "uid": row[0],
                "open_id": row[1],
                "nickname": row[2],
                "level": row[3],
                "exp": row[4],
                "gold": row[5],
                "diamond": row[6],
                "vip_level": row[7]
            }
        else:
            # Auto-register new guest
            cursor.execute('''
                INSERT INTO accounts (open_id, nickname, level, exp, gold, diamond, vip_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (open_id, f"Guest_{open_id[-4:]}", 1, 0, 1000, 100, 0))
            conn.commit()
            account_data = {
                "uid": cursor.lastrowid,
                "open_id": open_id,
                "nickname": f"Guest_{open_id[-4:]}",
                "level": 1,
                "exp": 0,
                "gold": 1000,
                "diamond": 100,
                "vip_level": 0
            }
        conn.close()
        return account_data
    except Exception as e:
        print(f"[DB FETCH ERROR] {e}")
        return {
            "uid": 100000001,
            "open_id": DEFAULT_OPEN_ID,
            "nickname": DEFAULT_NICKNAME,
            "level": DEFAULT_LEVEL,
            "exp": 999999,
            "gold": DEFAULT_GOLD,
            "diamond": DEFAULT_DIAMONDS,
            "vip_level": 10
        }

# ==============================================================================
# 2. PROTOBUF & BINARY PAYLOAD GENERATOR
# ==============================================================================
def generate_majorlogin_protobuf_stream():
    """Dynamically builds protobuf config binary stream pointing to Render Gateway."""
    # Custom Netty Protobuf Byte Stream Template
    header = b"\x08\xc4\xd2\xd1\xd1\x02\x12\x02BR\x1a\x02BR\"\x02BR*\x04liveB\x05EAAcX1780855974140HENRRI63pku98nH\xc4\x80\x01R\x1b"
    url_bytes = RENDER_URL.encode('utf-8')
    middle = b"`\x00z\x02\x08\x01\xea\x01\x13"
    trailer = b"\xa0\x01\x00\xd5\x01\x00\xbb\x01\xdf\xa9\xd1\xd1\x06\xe1\x01\x13" + url_bytes + b"\xe9\x01\x0c\x02BR\x10\x01(\x010\x018\x01"
    
    return header + url_bytes + middle + url_bytes + trailer

def generate_netty_binary_packet(data_dict):
    """Wraps dictionary payloads inside custom Netty Magic Framing for Raw TCP."""
    json_bytes = json.dumps(data_dict).encode('utf-8')
    payload_len = len(json_bytes)
    # Magic Header: 0x08, 0x00, Length High Byte, Length Low Byte
    header = bytearray([0x08, 0x00, (payload_len >> 8) & 0xFF, payload_len & 0xFF])
    return header + json_bytes

# ==============================================================================
# 3. UNIVERSAL PAYLOAD BUILDERS
# ==============================================================================
def get_master_universal_payload(account=None):
    if not account:
        account = fetch_or_create_account(DEFAULT_OPEN_ID)

    current_time = int(time.time())
    
    return {
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
        "need_role": False,
        "open_id": account["open_id"],
        "nickname": account["nickname"],
        "account_id": account["uid"],
        "server_url": RENDER_URL + "/",
        "gate_ip": RENDER_URL + "/",
        "cdn_url": RENDER_URL + "/",
        "backup_cdn_url": RENDER_URL + "/",
        "login_download_optionalpack": "",
        "use_background_download": False,
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
            "unlocked_skins": [301, 302, 303],
            "rank_points": 2400,
            "rank_tier": "Master",
            "guild_id": 88888,
            "guild_name": "Sigma Master Clan"
        },
        "config": {
            "remote_version": "1.0.1",
            "remote_option_version": "1.0.1",
            "is_review_server": False,
            "force_to_restart_app": False,
            "country_code": "IN",
            "gdpr_version": 0,
            "sigma_login": True,
            "sigma_switch": True,
            "space_required_in_GB": 0
        }
    }

def get_server_info_payload():
    return {
        "code": 0,
        "ret": 0,
        "server_name": "RENDER MAIN GATEWAY",
        "region": "GLOBAL",
        "server_online": True,
        "maintenance": False,
        "status": "ONLINE",
        "load": "NORMAL",
        "online_players": 1250,
        "max_capacity": 50000,
        "ping_ms": 12,
        "gateway_url": RENDER_URL,
        "time_stamp": int(time.time())
    }

# ==============================================================================
# 4. ADVANCED HTTP REQUEST HANDLER (REST / OAUTH / CONFIG / LOBBY)
# ==============================================================================
class FullMasterHttpGateway(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Clean logging format for Render console terminal
        print(f"[HTTP] {self.client_address[0]} -> {self.path} - {format % args}")

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '86400')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        self.process_incoming_request()

    def do_GET(self):
        self.process_incoming_request()

    def do_PUT(self):
        self.process_incoming_request()

    def process_incoming_request(self):
        clean_path = self.path.lower().split('?')[0]
        query_string = self.path.split('?')[1] if '?' in self.path else ""
        print(f"[GATEWAY ROUTE]: Method={self.command} Path={clean_path}")

        # Extract Client IP
        client_ip = self.headers.get('X-Forwarded-For', self.client_address[0])

        # -------------------------------------------------------------
        # ROUTE 1: /Majorlogin (Protobuf Config Binary Engine)
        # -------------------------------------------------------------
        if "majorlogin" in clean_path:
            print("[DISPATCH] Handling Majorlogin -> Injecting Protobuf Octet Binary Payload")
            binary_payload = generate_majorlogin_protobuf_stream()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(binary_payload)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(binary_payload)
            return

        # -------------------------------------------------------------
        # ROUTE 2: Server Info / Health Endpoint
        # -------------------------------------------------------------
        if "server_info" in clean_path or "status" in clean_path or "health" in clean_path:
            print("[DISPATCH] Handling Server Info Endpoint")
            self.reply_json(get_server_info_payload())
            return

        # -------------------------------------------------------------
        # ROUTE 3: Server Config / Client Version Check
        # -------------------------------------------------------------
        if any(k in clean_path for k in ["config", "version", "client", "check", "ver"]):
            print("[DISPATCH] Handling Config Verification Request")
            response = get_master_universal_payload()
            response["msg"] = "config match"
            self.reply_json(response)
            return

        # -------------------------------------------------------------
        # ROUTE 4: Authentication & OAuth (Guest / Account Login)
        # -------------------------------------------------------------
        if any(k in clean_path for k in ["auth", "guest", "login", "oauth", "token", "session"]):
            print("[DISPATCH] Handling User Auth -> Bypassing Credentials to Master Account")
            account = fetch_or_create_account(DEFAULT_OPEN_ID)
            auth_response = {
                "code": 0,
                "ret": 0,
                "msg": "login success",
                "status": "ok",
                "server_online": True,
                "maintenance": False,
                "open_id": account["open_id"],
                "access_token": "MASTER_TOKEN_SIGMA_DIRECT_PASS_99831",
                "refresh_token": "REFRESH_MASTER_TOKEN_99831",
                "expiry_time": int(time.time()) + 86400 * 30,
                "platform": 4,
                "uid": str(account["uid"]),
                "has_role": True,
                "is_created": True,
                "action": "go_to_lobby"
            }
            self.reply_json(auth_response)
            return

        # -------------------------------------------------------------
        # ROUTE 5: Role Creation / Nickname Verification
        # -------------------------------------------------------------
        if any(k in clean_path for k in ["role", "nickname", "create", "name", "player"]):
            print("[DISPATCH] Handling Role Verification -> Forcing Role Active")
            response = get_master_universal_payload()
            response["msg"] = "role found"
            response["has_role"] = True
            response["is_created"] = True
            self.reply_json(response)
            return

        # -------------------------------------------------------------
        # ROUTE 6: Lobby Sync / Inventory / Matchmaking Gateways
        # -------------------------------------------------------------
        if any(k in clean_path for k in ["lobby", "sync", "inventory", "match", "shop", "item", "user"]):
            print("[DISPATCH] Syncing User Stats -> Sending Full Lobby Payload")
            self.reply_json(get_master_universal_payload())
            return

        # -------------------------------------------------------------
        # CATCH-ALL ROUTE: Any Unmapped Endpoint -> Force Online & Lobby
        # -------------------------------------------------------------
        print(f"[DISPATCH FALLBACK] Intercepting {clean_path} -> Returning Universal Lobby Response")
        self.reply_json(get_master_universal_payload())

    def reply_json(self, data_dict):
        """Helper function to cleanly serialize JSON and write response."""
        json_bytes = json.dumps(data_dict, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(json_bytes)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(json_bytes)

# ==============================================================================
# 5. HIGH-PERFORMANCE TCP SOCKET GATEWAY (Netty Binary Protocol Engine)
# ==============================================================================
def handle_tcp_socket_client(client_socket, client_addr):
    """Processes persistent TCP socket connections from native C++ game client."""
    print(f"[TCP NETTY] Connected: {client_addr[0]}:{client_addr[1]}")
    try:
        client_socket.settimeout(10.0) # 10 seconds recv timeout
        
        while True:
            try:
                raw_data = client_socket.recv(8192)
                if not raw_data:
                    print(f"[TCP NETTY] Client disconnected cleanly: {client_addr[0]}")
                    break

                print(f"[TCP REQ RECV] {len(raw_data)} bytes from {client_addr[0]}: {raw_data[:20]}")

                # Build Netty Binary Packet forcing lobby redirect
                account = fetch_or_create_account(DEFAULT_OPEN_ID)
                payload = get_master_universal_payload(account)
                
                # Encode binary frame header
                response_binary = generate_netty_binary_packet(payload)
                client_socket.sendall(response_binary)
                print(f"[TCP RESP SENT] Sent Netty Binary Framed Lobby Payload ({len(response_binary)} bytes)")

            except socket.timeout:
                # Send heart-beat keep-alive ping
                ping_packet = generate_netty_binary_packet({"code": 0, "msg": "heartbeat", "server_online": True})
                client_socket.sendall(ping_packet)
                print("[TCP KEEP-ALIVE] Ping sent.")
            except Exception as e:
                print(f"[TCP RECV ERROR] {e}")
                break

    except Exception as general_error:
        print(f"[TCP GATEWAY ERROR] Client thread error: {general_error}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        print(f"[TCP CLOSED] Connection closed for {client_addr[0]}")

def launch_raw_tcp_gateway(host='0.0.0.0', port=SECONDARY_TCP_PORT):
    """Forks background daemon thread listening for Netty socket game connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(100)
        print(f"[TCP GATEWAY ONLINE] Background Socket Server Listening on {host}:{port}")
        
        while True:
            try:
                client, addr = server_socket.accept()
                client_thread = threading.Thread(target=handle_tcp_socket_client, args=(client, addr))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"[TCP ACCEPT ERROR] {e}")
                time.sleep(0.1)
    except Exception as bind_error:
        print(f"[TCP BIND FATAL] Failed to start raw TCP socket on port {port}: {bind_error}")

# ==============================================================================
# 6. APPLICATION ENTRY POINT (Supports both server.py Import & Direct Launch)
# ==============================================================================
def start_tcp_server(host='0.0.0.0', port=PRIMARY_HTTP_PORT):
    """
    Main entry point function called by server.py
    Line 16 in server.py calls: tcp.start_tcp_server('0.0.0.0', port)
    """
    print("\n" + "="*70)
    print("   MASTER SINGLE-ENGINE GAME SERVER (HTTP + TCP GATEWAY) RUNNING")
    print("="*70)
    print(f" -> Active Render Endpoint : {RENDER_URL}")
    print(f" -> Main HTTP Gateway Port : {port}")
    print(f" -> Socket Gateway Port   : {SECONDARY_TCP_PORT}")
    print("="*70 + "\n")

    # Step 1: Initialize Database
    init_database()

    # Step 2: Spawn Background TCP Raw Socket Thread
    tcp_thread = threading.Thread(target=launch_raw_tcp_gateway, args=(host, SECONDARY_TCP_PORT))
    tcp_thread.daemon = True
    tcp_thread.start()

    # Step 3: Run Primary Blocking HTTP Server on Main Port
    print(f"[HTTP GATEWAY ONLINE] Listening for Game Requests on {host}:{port}")
    try:
        httpd = HTTPServer((host, port), FullMasterHttpGateway)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER SHUTDOWN] Stopping services gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"[SERVER CRASH] Fatal server error: {e}")

if __name__ == '__main__':
    # Default fallback for standalone CLI execution
    server_port = PRIMARY_HTTP_PORT
    if len(sys.argv) > 1:
        try:
            server_port = int(sys.argv[1])
        except ValueError:
            pass
            
    start_tcp_server('0.0.0.0', server_port)
