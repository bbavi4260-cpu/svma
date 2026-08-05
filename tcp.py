import socket
import threading
import json

def build_raw_http_response(body_bytes, content_type="application/json; charset=utf-8"):
    headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body_bytes)}\r\n\r\n"
    )
    return headers.encode('utf-8') + body_bytes

def handle_client(client_socket, addr):
    print(f"[TCP LOG] Connected: {addr}")
    try:
        raw_data = client_socket.recv(4096)
        if not raw_data:
            return

        # Request parsing
        req_text = raw_data.decode('utf-8', errors='ignore')
        print(f"[REQ HEADER]: {req_text.splitlines()[0] if req_text else 'BINARY PACKET'}")

        # Universal 100% Ready JSON Data Payload
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
            "open_id": "GUEST_100000001",
            "nickname": "Master",
            "data": {
                "account_id": 100000001,
                "open_id": "GUEST_100000001",
                "nickname": "Master",
                "level": 60,
                "gold": 999999,
                "diamond": 999999,
                "has_role": True,
                "is_created": True
            }
        }

        json_bytes = json.dumps(ready_payload).encode('utf-8')

        # Checks if request is standard HTTP or Raw TCP Binary
        if req_text.startswith("GET") or req_text.startswith("POST") or req_text.startswith("OPTIONS"):
            # Standard Web HTTP Handshake
            response = build_raw_http_response(json_bytes)
            client_socket.sendall(response)
            print("[SERVER RESPONSE] HTTP OK Sent")
        else:
            # Game Raw TCP/Protobuf Socket Handshake
            # Creates a binary magic header (Length + Ret Code 0 + Binary Payload)
            packet_len = len(json_bytes)
            binary_header = bytearray([0x00, 0x00, (packet_len >> 8) & 0xFF, packet_len & 0xFF, 0x00, 0x00, 0x00, 0x00])
            binary_response = binary_header + json_bytes
            client_socket.sendall(binary_response)
            print("[SERVER RESPONSE] Raw TCP Binary Payload Sent")

    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        client_socket.close()

def start_server(host='0.0.0.0', port=8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(15)
    print(f"[TCP RAW/HTTP SERVER] Active on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client_socket, addr))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    start_server()
