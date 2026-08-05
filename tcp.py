import socket
import threading
import json
import sqlite3
import time

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
        print("[DATABASE] Accounts database initialized successfully.")
    except Exception as e:
        print(f"[DATABASE ERROR] {e}")

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

def build_binary_tcp_response(json_data):
    json_bytes = json.dumps(json_data).encode('utf-8')
    packet_len = len(json_bytes)
    # Magic Header Frame (Length + Standard Response Marker)
    header = bytearray([0x00, 0x00, (packet_len >> 8) & 0xFF, packet_len & 0xFF, 0x00, 0x00, 0x00, 0x00])
    return header + json_bytes

def handle_client(client_socket, addr):
    print(f"[TCP CLIENT CONNECTED] IP: {addr[0]}:{addr[1]}")
    try:
        raw_data = client_socket.recv(8192)
        if not raw_data:
            return

        req_text = raw_data.decode('utf-8', errors='ignore')
        first_line = req_text.splitlines()[0] if req_text else "RAW BINARY SOCKET PACKET"
        print(f"[REQUEST] {first_line}")

        base_url = "https://svmx.onrender.com/"

        # 1. Global Master Payload (Full Server Open + Lobby Bypass Data)
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

        # 2. Server Main Configuration Payload
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
            "cdn_url": base_url,
            "backup_cdn_url": base_url,
            "server_url": base_url,
            "is_review_server": False,
            "appstore_url": "",
            "force_to_restart_app": False,
            "country_code": "IN",
            "gdpr_version": 0,
            "client_ip": addr[0] if addr else "127.0.0.1",
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

        # 3. Guest Authorization Payload
        guest_auth_payload = {
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

        req_lower = req_text.lower()

        # HTTP REST Standard Requests
        if req_text.startswith("GET") or req_text.startswith("POST") or req_text.startswith("OPTIONS"):
            if any(k in req_lower for k in ["config", "ver", "client"]):
                print("[ROUTING] Main Config Match -> Sending Server Config")
                client_socket.sendall(build_http_response(config_payload))
            elif any(k in req_lower for k in ["guest", "oauth", "login"]):
                print("[ROUTING] Guest Auth Match -> Authorizing Session")
                client_socket.sendall(build_http_response(guest_auth_payload))
            elif any(k in req_lower for k in ["role", "nickname", "create", "name", "player", "major", "lobby", "user"]):
                print("[ROUTING] Lobby / Role Request -> Sending Master Lobby Payload")
                client_socket.sendall(build_http_response(master_lobby_payload))
            else:
                print("[ROUTING] Universal Match -> Sending Universal Master Payload")
                client_socket.sendall(build_http_response(master_lobby_payload))
        else:
            # Direct Netty TCP Socket Binary Streams
            print("[ROUTING] Netty Binary Stream Detected -> Sending Framing Binary Header + Payload")
            client_socket.sendall(build_binary_tcp_response(master_lobby_payload))

    except Exception as e:
        print(f"[SOCKET ERROR] {e}")
    finally:
        client_socket.close()

def start_tcp_server(host='0.0.0.0', port=8080):
    init_accounts_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(50)
        print(f"==================================================")
        print(f"[SERVER STARTED] Full Big Master TCP/HTTP Listening on {host}:{port}")
        print(f"==================================================")
        
        while True:
            client_socket, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.daemon = True
            client_thread.start()

    except Exception as e:
        print(f"[FATAL SERVER ERROR] {e}")
    finally:
        server.close()

if __name__ == '__main__':
    start_tcp_server()
