import socket
import threading
import sqlite3
import json

DB_FILE = 'accounts.db'

def init_accounts_db():
    """Initializes SQLite database for player persistence."""
    try:
        conn = sqlite3.connect(DB_FILE)
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
        # Insert default master profile if not exists
        cursor.execute("SELECT id FROM players WHERE username = ?", ("Master",))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO players (username, level, diamonds, gold)
                VALUES (?, ?, ?, ?)
            ''', ("Master", 60, 999999, 999999))
            conn.commit()
        conn.close()
        print("[DB] Accounts database initialized successfully.")
    except Exception as e:
        print(f"[DB ERROR] {e}")

def get_player_data(username="Master"):
    """Fetches player stats from the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, level, diamonds, gold FROM players WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "account_id": row[0],
                "open_id": f"GUEST_{row[0]}",
                "nickname": row[1],
                "level": row[2],
                "diamond": row[3],
                "gold": row[4]
            }
    except Exception as e:
        print(f"[DB FETCH ERROR] {e}")
    
    # Fallback default
    return {
        "account_id": 100000001,
        "open_id": "GUEST_100000001",
        "nickname": "Master",
        "level": 60,
        "diamond": 999999,
        "gold": 999999
    }

def build_http_response(json_data):
    body = json.dumps(json_data)
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n"
        f"{body}"
    )
    return response.encode('utf-8')

def handle_client(client_socket, addr):
    print(f"[TCP] New Connection from: {addr}")
    try:
        client_socket.settimeout(5.0)
        raw_data = client_socket.recv(8192)
        if not raw_data:
            return
            
        req_str = raw_data.decode('utf-8', errors='ignore')
        first_line = req_str.splitlines()[0] if req_str else ""
        print(f"[TCP REQ LINE]: {first_line}")

        base_url = "https://sigma-private-server.onrender.com/"
        req_lower = req_str.lower()
        player = get_player_data("Master")

        # 1. MAIN CONFIG RESPONSE
        if any(k in req_lower for k in ["config", "ver", "client", "check"]):
            print("[SERVER MATCH] Handshaking Main Config")
            sigma_config = {
                "code": 0, "ret": 0,
                "is_server_open": True, "is_firewall_open": True,
                "need_track_hotupdate": False,
                "remote_version": "1.0.1", "remote_option_version": "1.0.1",
                "cdn_url": base_url, "backup_cdn_url": base_url, "server_url": base_url,
                "is_review_server": False, "force_to_restart_app": False,
                "country_code": "IN", "client_ip": addr[0],
                "network_log_server": base_url, "web_log_server": base_url,
                "test_url": base_url, "img_cdn_url": base_url, "core_url": base_url,
                "is_update_btn_show": False, "sigma_login": True, "sigma_switch": True,
                "space_required_in_GB": 0, "sigma_backup_url": base_url,
                "login_download_optionalpack": ""
            }
            client_socket.sendall(build_http_response(sigma_config))

        # 2. GUEST & LOGIN REQUESTS
        elif any(k in req_lower for k in ["guest", "oauth", "login"]):
            print("[SERVER MATCH] Handling Guest Login")
            guest_payload = {
                "open_id": player["open_id"],
                "access_token": "GUEST_TOKEN_MASTER_99831",
                "refresh_token": "REFRESH_TOKEN_MASTER_99831",
                "expiry_time": 1817401047,
                "platform": 4,
                "uid": str(player["account_id"]),
                "ret": 0, "code": 0,
                "msg": "success",
                "has_role": True, "is_created": True
            }
            client_socket.sendall(build_http_response(guest_payload))

        # 3. PLAYER PROFILE / ROLE / LOBBY SYNC
        elif any(k in req_lower for k in ["role", "name", "create", "nickname", "player", "profile", "user", "major", "lobby"]):
            print("[SERVER MATCH] Direct Player & Lobby Sync")
            lobby_sync_payload = {
                "code": 0, "ret": 0, "msg": "success",
                "has_role": True, "is_created": True,
                "data": {
                    "account_id": player["account_id"],
                    "open_id": player["open_id"],
                    "nickname": player["nickname"],
                    "level": player["level"],
                    "exp": 99999,
                    "gold": player["gold"],
                    "diamond": player["diamond"],
                    "avatar_id": 1, "gender": 1, "character_id": 101,
                    "has_role": True, "is_created": True,
                    "unlocked_characters": [101, 102, 103, 104, 105]
                }
            }
            client_socket.sendall(build_http_response(lobby_sync_payload))

        # 4. FILEINFO & ASSET CHECKS
        elif any(k in req_lower for k in ["fileinfo", "android", "version"]):
            print("[SERVER MATCH] Asset FileInfo Check")
            fileinfo_payload = {
                "code": 0, "ret": 0, "msg": "success",
                "files": [], "total_size": 0, "version": "1.0.1"
            }
            client_socket.sendall(build_http_response(fileinfo_payload))

        # DEFAULT FALLBACK
        else:
            print("[SERVER MATCH] Initial Startup Match -> Config Returned")
            sigma_config = {
                "code": 0, "ret": 0,
                "server_url": base_url, "cdn_url": base_url,
                "is_server_open": True, "maintenance": False
            }
            client_socket.sendall(build_http_response(sigma_config))

    except socket.timeout:
        print("[TCP WARNING] Connection timeout.")
    except Exception as e:
        print(f"[TCP ERROR]: {e}")
    finally:
        client_socket.close()

def start_tcp_server(host='0.0.0.0', port=8080):
    init_accounts_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(50)
    print(f"[TCP SERVER] Running on {host}:{port}")

    while True:
        try:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"[SERVER ACCEPT ERROR] {e}")

if __name__ == '__main__':
    start_tcp_server()
