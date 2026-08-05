import socket
import threading
import json
import time

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

def build_protobuf_binary_response(json_data):
    # Generates strict Protobuf framing header for Netty Socket Client
    json_bytes = json.dumps(json_data).encode('utf-8')
    body_length = len(json_bytes)
    
    # Header: 2-byte Magic Tag (0x08, 0x00) + 2-byte Payload Length + Data
    header = bytearray([
        0x08, 0x00, 
        (body_length >> 8) & 0xFF, 
        body_length & 0xFF
    ])
    return header + json_bytes

def handle_client(client_socket, addr):
    print(f"[TCP LOG] Connected from: {addr[0]}:{addr[1]}")
    try:
        client_socket.settimeout(5.0)
        raw_data = client_socket.recv(8192)
        if not raw_data:
            return

        req_text = raw_data.decode('utf-8', errors='ignore')
        first_line = req_text.splitlines()[0] if req_text else "BINARY PACKET"
        print(f"[CLIENT REQ]: {first_line}")

        base_url = "https://svmx.onrender.com/"

        # Master Response Data - Unlocks Server, Removes Maintenance, Grants Full Lobby Access
        master_data = {
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
            "level": 60,
            "exp": 999999,
            "gold": 999999,
            "diamond": 999999,
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

        # Config Payload
        config_data = {
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

        # Handle HTTP standard calls
        if req_text.startswith("GET") or req_text.startswith("POST") or req_text.startswith("OPTIONS"):
            req_lower = req_text.lower()
            if any(k in req_lower for k in ["config", "ver", "client"]):
                print("[RESPONSE] Config Sent")
                client_socket.sendall(build_http_response(config_data))
            else:
                print("[RESPONSE] Universal Master HTTP Sent")
                client_socket.sendall(build_http_response(master_data))
        else:
            # Handle Direct Binary Netty Stream
            print("[RESPONSE] Binary Protobuf Frame Sent")
            client_socket.sendall(build_protobuf_binary_response(master_data))

    except Exception as e:
        print(f"[CLIENT HANDLER ERROR]: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def start_tcp_server(host='0.0.0.0', port=8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(50)
    print(f"[MASTER SERVER] Running on {host}:{port}")

    while True:
        try:
            client_socket, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            print(f"[ACCEPT ERROR]: {e}")

if __name__ == '__main__':
    start_tcp_server()
