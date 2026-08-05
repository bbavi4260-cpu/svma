import socket
import threading
import sqlite3
import json

DB_FILE = 'accounts.db'

def init_accounts_db():
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
        cursor.execute("SELECT id FROM players WHERE username = ?", ("Master",))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO players (username, level, diamonds, gold)
                VALUES (?, ?, ?, ?)
            ''', ("Master", 60, 999999, 999999))
            conn.commit()
        conn.close()
        print("[DB] Database initialized.")
    except Exception as e:
        print(f"[DB ERROR] {e}")

def get_player_data():
    return {
        "account_id": 100000001,
        "open_id": "GUEST_100000001",
        "nickname": "GGDEV",
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
    try:
        client_socket.settimeout(5.0)
        raw_data = client_socket.recv(8192)
        if not raw_data:
            return
            
        req_str = raw_data.decode('utf-8', errors='ignore')
        first_line = req_str.splitlines()[0] if req_str else ""
        print(f"[INCOMING REQ]: {first_line}")

        base_url = "https://sigma-private-server.onrender.com/"
        req_lower = req_str.lower()
        player = get_player_data()

        # 1. Config / Version / Startup Check
        if any(k in req_lower for k in ["config", "ver", "client", "check"]):
            print("[MATCH] Config Handshake Sent")
            payload = {
                "code": 0, "ret": 0,
                "is_server_open": True, "is_firewall_open": True,
                "remote_version": "1.0.1", "remote_option_version": "1.0.1",
                "cdn_url": base_url, "backup_cdn_url": base_url, "server_url": base_url,
                "is_review_server": False, "force_to_restart_app": False,
                "country_code": "IN", "client_ip": addr[0],
                "network_log_server": base_url, "web_log_server": base_url,
                "test_url": base_url, "img_cdn_url": base_url, "core_url": base_url,
                "is_update_btn_show": False, "sigma_login": True, "sigma_switch": True
            }
            client_socket.sendall(build_http_response(payload))

        # 2. Login / Guest / Auth
        elif any(k in req_lower for k in ["guest", "oauth", "login", "auth"]):
            print("[MATCH] Guest Login Session Granted")
            payload = {
                "open_id": player["open_id"],
                "access_token": "MASTER_TOKEN_BYPASS_99831",
                "refresh_token": "MASTER_REFRESH_99831",
                "expiry_time": 1817401047,
                "platform": 4,
                "uid": str(player["account_id"]),
                "ret": 0, "code": 0, "msg": "success",
                "has_role": True, "is_created": True
            }
            client_socket.sendall(build_http_response(payload))

        # 3. Nickname / Role / Lobby / Player Sync (Fixes 'Server will be ready soon' error)
        elif any(k in req_lower for k in ["role", "name", "create", "nickname", "player", "profile", "user", "major", "lobby", "register"]):
            print("[MATCH] Lobby & Role Entry Authorized")
            payload = {
                "code": 0, "ret": 0, "msg": "success",
                "status": "ok",
                "has_role": True, "is_created": True,
                "need_role": False,
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
                    "in_lobby": True,
                    "unlocked_characters": [101, 102, 103, 104, 105]
                }
            }
            client_socket.sendall(build_http_response(payload))

        # 4. Universal Catch-All (Prevents any unhandled route from throwing 404 or Server Error)
        else:
            print("[MATCH] Universal Bypass Fallback Triggered")
            payload = {
                "code": 0,
                "ret": 0,
                "msg": "success",
                "status": "ok",
                "has_role": True,
                "is_created": True,
                "server_url": base_url,
                "cdn_url": base_url,
                "data": {
                    "account_id": player["account_id"],
                    "open_id": player["open_id"],
                    "nickname": player["nickname"],
                    "gold": player["gold"],
                    "diamond": player["diamond"]
                }
            }
            client_socket.sendall(build_http_response(payload))

    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        client_socket.close()

def start_tcp_server(host='0.0.0.0', port=8080):
    init_accounts_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(50)
    print(f"[TCP SERVER] Running on port {port}")

    while True:
        try:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"[ACCEPT ERROR] {e}")

if __name__ == '__main__':
    start_tcp_server()
