import socket
import threading
import json
import time
import sqlite3
import datetime

DB_FILE = 'accounts.db'

def log_msg(tag, msg):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] [{tag}] {msg}")

# --- DATABASE SETUP ---
def init_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                open_id TEXT UNIQUE NOT NULL,
                nickname TEXT NOT NULL,
                level INTEGER DEFAULT 60,
                gold INTEGER DEFAULT 999999,
                diamond INTEGER DEFAULT 999999
            )
        ''')
        cursor.execute("SELECT id FROM players WHERE open_id = ?", ("100000001",))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO players (open_id, nickname, level, gold, diamond)
                VALUES (?, ?, ?, ?, ?)
            ''', ("100000001", "Master", 60, 999999, 999999))
            conn.commit()
        conn.close()
        log_msg("DB", "Database initialized successfully.")
    except Exception as e:
        log_msg("DB ERROR", str(e))

def get_player():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, open_id, nickname, level, gold, diamond FROM players WHERE open_id = ?", ("100000001",))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "account_id": row[0],
                "open_id": row[1],
                "nickname": row[2],
                "level": row[3],
                "gold": row[4],
                "diamond": row[5]
            }
    except:
        pass
    return {
        "account_id": 100000001,
        "open_id": "100000001",
        "nickname": "Master",
        "level": 60,
        "gold": 999999,
        "diamond": 999999
    }

# --- HTTP RESPONSE BUILDER ---
def create_http_response(data_dict, status_code=200):
    body = json.dumps(data_dict)
    response = (
        f"HTTP/1.1 {status_code} OK\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Connection: keep-alive\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n"
        f"{body}"
    )
    return response.encode('utf-8')

# --- TCP REQUEST HANDLER & ROUTER ---
def handle_client(client_socket, addr):
    log_msg("TCP CONNECT", f"Incoming connection from {addr[0]}:{addr[1]}")
    try:
        client_socket.settimeout(15.0)
        while True:
            raw_data = client_socket.recv(8192)
            if not raw_data:
                break
            
            req_str = raw_data.decode('utf-8', errors='ignore')
            first_line = req_str.splitlines()[0] if req_str.splitlines() else "GET /"
            log_msg("TCP REQ", f"From {addr[0]} -> {first_line}")

            path = "/"
            try:
                parts = first_line.split(" ")
                if len(parts) >= 2:
                    path = parts[1].split("?")[0]
            except:
                pass

            player = get_player()
            host_url = f"http://{addr[0]}:8080"
            
            # --- ROUTING ENGINE ---

            # 1. GUEST OAUTH LOGIN ROUTE (Exact requested format)
            if "oauth/guest" in path.lower() or "guest/login" in path.lower():
                log_msg("ROUTE", f"Handling Guest OAuth -> {path}")
                response_payload = {
                    "open_id": player["open_id"],
                    "access_token": "TOKEN",
                    "ret": 0,
                    "msg": "success"
                }

            # 2. APP INFO ROUTE (Exact requested format)
            elif "app/info/get" in path.lower() or "app/info" in path.lower():
                log_msg("ROUTE", f"Handling App Info -> {path}")
                response_payload = {
                    "ret": 0,
                    "result": 0,
                    "msg": "success",
                    "data": {
                        "app_id": 100067,
                        "app_name": "Sigma",
                        "status": 1,
                        "update_url": "",
                        "version": "1.0.0"
                    },
                    "client_log": False,
                    "overlay_config_url": host_url + "/rct/ver.php"
                }

            # 3. VERSION CHECK ROUTE
            elif "ver.php" in path.lower():
                log_msg("ROUTE", f"Handling Version Check -> {path}")
                response_payload = {
                    "code": 0,
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
                    "remote_version": "1.0.0",
                    "remote_option_version": "1.0.0",
                    "cdn_url": host_url + "/",
                    "backup_cdn_url": host_url + "/",
                    "server_url": host_url + "/",
                    "is_review_server": False,
                    "appstore_url": host_url + "/",
                    "force_to_restart_app": False,
                    "country_code": "IN",
                    "gdpr_version": 0,
                    "client_ip": addr[0],
                    "maintenance_announcement": "",
                    "maintenance_region": "",
                    "need_check_ip_list": [],
                    "network_log_server": host_url + "/",
                    "web_log_server": host_url + "/",
                    "login_failed_count": 0,
                    "test_url": host_url + "/",
                    "img_cdn_url": host_url + "/",
                    "core_url": host_url + "/",
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
                    "sigma_backup_url": host_url + "/",
                    "login_download_optionalpack": ""
                }

            # 4. MAJOR LOGIN ROUTE
            elif "majorlogin" in path.lower() or "login" in path.lower():
                log_msg("ROUTE", f"Handling MajorLogin -> {path}")
                response_payload = {
                    "ret": 0,
                    "msg": "success",
                    "data": {
                        "account_id": player["account_id"],
                        "uid": str(player["account_id"]),
                        "open_id": player["open_id"],
                        "nickname": player["nickname"],
                        "level": player["level"],
                        "exp": 99999,
                        "gold": player["gold"],
                        "diamond": player["diamond"],
                        "token": "TOKEN",
                        "has_role": True,
                        "is_created": True,
                        "in_lobby": True,
                        "server_time": int(time.time()),
                        "server_url": host_url,
                        "cdn_url": host_url
                    }
                }

            # 5. CATCH-ALL DEFAULT ROUTE
            else:
                log_msg("ROUTE", f"Handling Default/Root Path -> {path}")
                response_payload = {
                    "ret": 0,
                    "msg": "success",
                    "data": {}
                }

            packet = create_http_response(response_payload)
            client_socket.sendall(packet)
            log_msg("TCP RES", f"Response successfully sent for [{path}] to {addr[0]}")

    except Exception as e:
        log_msg("SOCKET ERROR", f"With {addr[0]} -> {str(e)}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        log_msg("TCP DISCONNECT", f"Connection closed for {addr[0]}")

def start_tcp_server(host='0.0.0.0', port=8080):
    init_database()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)
    log_msg("TCP SERVER", f"Raw TCP Server started successfully and listening on port {port}")

    while True:
        try:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr))
            thread.daemon = True
            thread.start()
        except Exception as e:
            log_msg("ACCEPT ERROR", str(e))

if __name__ == '__main__':
    start_tcp_server()
