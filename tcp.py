import socket
import threading
import sqlite3
import json

def init_accounts_db():
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
        raw_data = client_socket.recv(4096)
        if raw_data:
            req_str = raw_data.decode('utf-8', errors='ignore')
            first_line = req_str.splitlines()[0] if req_str else ""
            print(f"[TCP REQ LINE]: {first_line}")

            # Note: Update this URL to your deployed domain after uploading to Render/VPS
            base_url = "http://0.0.0.0/"

            # 1. Player Info & Lobby Init Sync
            if "player" in req_str or "profile" in req_str or "user" in req_str:
                print("[SERVER MATCH] Handling Player Profile & Lobby Init")
                player_payload = {
                    "code": 0,
                    "ret": 0,
                    "msg": "success",
                    "data": {
                        "account_id": 100000001,
                        "nickname": "Master",
                        "level": 60,
                        "exp": 99999,
                        "gold": 999999,
                        "diamond": 999999,
                        "avatar_id": 1,
                        "gender": 1,
                        "character_id": 101,
                        "unlocked_characters": [101, 102]
                    }
                }
                client_socket.sendall(build_http_response(player_payload))

            # 2. Guest OAuth & Register/Login Request
            elif "guest" in req_str or "oauth" in req_str or "login" in req_str:
                print("[SERVER MATCH] Handling Guest OAuth / Login Request")
                guest_payload = {
                    "open_id": "100000001",
                    "access_token": "GUEST_TOKEN_1785865047",
                    "refresh_token": "GUEST_TOKEN_1785865047",
                    "expiry_time": 1817401047,
                    "platform": 4,
                    "uid": "100000001",
                    "ret": 0,
                    "code": 0,
                    "msg": "success"
                }
                client_socket.sendall(build_http_response(guest_payload))

            # 3. Asset File Info Request (/fileinfo)
            elif "fileinfo" in req_str or "android/1.0.1" in req_str:
                print("[SERVER MATCH] Handling Asset FileInfo Check")
                fileinfo_payload = {
                    "code": 0,
                    "ret": 0,
                    "msg": "success",
                    "files": [],
                    "total_size": 0,
                    "version": "1.0.1"
                }
                client_socket.sendall(build_http_response(fileinfo_payload))

            # 4. Main Config Payload (/ver.php / config)
            else:
                print("[SERVER MATCH] Handling Main Server Config")
                sigma_payload = {
                    "code": 0,
                    "ret": 0,
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
                    "cdn_url": base_url,
                    "backup_cdn_url": base_url,
                    "server_url": base_url,
                    "is_review_server": False,
                    "appstore_url": "",
                    "force_to_restart_app": False,
                    "country_code": "IN",
                    "gdpr_version": 0,
                    "client_ip": addr[0],
                    "maintenance_announcement": "",
                    "maintenance_region": "",
                    "need_check_ip_list": [],
                    "network_log_server": base_url,
                    "web_log_server": base_url,
                    "login_failed_count": 0,
                    "test_url": base_url,
                    "img_cdn_url": base_url,
                    "core_url": base_url,
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
                    "sigma_backup_url": base_url,
                    "login_download_optionalpack": ""
                }
                client_socket.sendall(build_http_response(sigma_payload))

    except Exception as e:
        print(f"[TCP ERROR]: {e}")
    finally:
        client_socket.close()

def start_tcp_server(host='0.0.0.0', port=8080):
    init_accounts_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    print(f"[TCP SERVER] Running on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.daemon = True
        thread.start()
          
