import socket
import threading
import json
import os
import re
import struct

def create_raw_http_response(raw_bytes, content_type="application/octet-stream"):
    response = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        "Server: nginx/1.18.0\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS, PUT, DELETE\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(raw_bytes)}\r\n\r\n"
    ).encode('utf-8') + raw_bytes
    return response

def create_http_json_response(data_dict):
    body = json.dumps(data_dict, separators=(',', ':'))
    return create_raw_http_response(body.encode('utf-8'), content_type="application/json; charset=utf-8")

def encode_varint(value):
    out = bytearray()
    while True:
        towrite = value & 0x7f
        value >>= 7
        if value:
            out.append(towrite | 0x80)
        else:
            out.append(towrite)
            break
    return bytes(out)

def encode_field_varint(field_number, value):
    key = (field_number << 3) | 0
    return encode_varint(key) + encode_varint(value)

def encode_field_string(field_number, text):
    key = (field_number << 3) | 2
    raw_str = text.encode('utf-8')
    return encode_varint(key) + encode_varint(len(raw_str)) + raw_str

def build_mono_major_login_payload():
    pb = bytearray()
    pb.extend(encode_field_varint(1, 0))          # Code = 0 (Success)
    pb.extend(encode_field_varint(2, 100000001))  # Account ID
    pb.extend(encode_field_string(3, "GUEST_TOKEN_PERMANENT_BYPASS")) # Token
    pb.extend(encode_field_string(4, "127.0.0.1:10000")) # Lobby IP
    pb.extend(encode_field_string(5, "IN"))       # Region
    pb.extend(encode_field_varint(6, 31536000))   # TTL
    
    raw_pb = bytes(pb)
    header = struct.pack('>HHI', 0xFEFF, 1002, len(raw_pb))
    return header + raw_pb

def handle_client(client_socket, addr, port):
    try:
        client_socket.settimeout(5.0)
        try:
            raw_data = client_socket.recv(16384)
        except socket.timeout:
            client_socket.close()
            return
            
        if not raw_data:
            client_socket.close()
            return

        # Pure Raw TCP Packet check
        if not raw_data.startswith(b"GET") and not raw_data.startswith(b"POST") and not raw_data.startswith(b"OPTIONS"):
            print(f"\n[TCP SOCKET] Raw Client Handshake Received ({len(raw_data)} bytes)")
            # Return Basic OK Ack Frame
            response_frame = struct.pack('>HHI', 0xFEFF, 1002, 0)
            client_socket.sendall(response_frame)
            return

        req_str = raw_data.decode('utf-8', errors='ignore')
        lines = req_str.splitlines()
        first_line = lines[0] if lines else ""
        
        request_path = first_line.split(" ")[1] if len(first_line.split(" ")) > 1 else first_line
        request_path_clean = request_path.lower()

        print(f"\n================ [REQUEST DETECTED] ================")
        print(f"[REQ] From {addr} -> {first_line}")
        print(f"[PARSED PATH] {request_path}")

        base_url = f"http://127.0.0.1:{port}/"

        # 1. VERSION CHECK ROUTE
        if "ver.php" in request_path_clean or "version" in request_path_clean:
            print("[ACTION] Sending Version Check Response")
            response_payload = {
                "code": 0, "ret": 0, "msg": "success", "status": "ok",
                "is_server_open": True, "is_firewall_open": True,
                "remote_version": "1.0.1", "remote_option_version": "1.0.1",
                "server_url": base_url, "cdn_url": base_url, "backup_cdn_url": base_url,
                "is_review_server": False, "force_to_restart_app": False,
                "country_code": "IN", "client_ip": addr[0]
            }
            packet = create_http_json_response(response_payload)

        # 2. MAJOR LOGIN ROUTE
        elif "majorlogin" in request_path_clean or "major" in request_path_clean:
            print("[ACTION] Sending MajorLogin Binary Response")
            binary_payload = build_mono_major_login_payload()
            packet = create_raw_http_response(binary_payload, content_type="application/octet-stream")

        # 3. NICKNAME / ROLE CREATION & INITIALIZATION ROUTE
        elif any(path in request_path_clean for path in ["createrole", "getrole", "initdata", "role", "user"]):
            print("[ACTION] Sending Nickname & Character Role Initialization")
            response_payload = {
                "code": 0,
                "ret": 0,
                "result": 0,
                "msg": "success",
                "status": "ok",
                "data": {
                    "account_id": 100000001,
                    "nickname": "Master",
                    "level": 70,
                    "exp": 99999,
                    "gold": 999999,
                    "diamond": 999999,
                    "head_id": 1,
                    "body_id": 1,
                    "has_role": True,
                    "is_created": True,
                    "in_lobby": True,
                    "is_server_open": True
                },
                "has_role": True,
                "is_created": True,
                "in_lobby": True,
                "is_server_open": True,
                "server_url": base_url,
                "cdn_url": base_url
            }
            packet = create_http_json_response(response_payload)

        # 4. FALLBACK ROUTE
        else:
            print("[ACTION] Sending Default Bypass Response")
            response_payload = {
                "code": 0, "ret": 0, "result": 0, "msg": "success", "status": "ok",
                "is_server_open": True, "is_firewall_open": True,
                "has_role": True, "is_created": True, "in_lobby": True,
                "server_url": base_url, "cdn_url": base_url
            }
            packet = create_http_json_response(response_payload)

        client_socket.sendall(packet)

    except Exception as e:
        print(f"[HANDLER ERROR] {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def start_tcp_server(host='0.0.0.0'):
    port = int(os.environ.get("PORT", 10000))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)
    
    print("==================================================")
    print(" [FIXED SERVER] Nickname & Role Creation Active")
    print(" [PORT] :", port)
    print("==================================================")

    while True:
        try:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr, port))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"[ACCEPT ERROR] {e}")

if __name__ == '__main__':
    start_tcp_server()
