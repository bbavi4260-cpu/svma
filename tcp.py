import socket
import threading
import json
import time
import sqlite3

DB_FILE = 'accounts.db'

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
        cursor.execute("SELECT id FROM players WHERE open_id = ?", ("GUEST_100000001",))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO players (open_id, nickname, level, gold, diamond)
                VALUES (?, ?, ?, ?, ?)
            ''', ("GUEST_100000001", "Master", 60, 999999, 999999))
            conn.commit()
        conn.close()
        print("[DB] Initialized successfully.")
    except Exception as e:
        print(f"[DB ERROR] {e}")

def get_player():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, open_id, nickname, level, gold, diamond FROM players WHERE open_id = ?", ("GUEST_100000001",))
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
        "open_id": "GUEST_100000001",
        "nickname": "Master",
        "level": 60,
        "gold": 999999,
        "diamond": 999999
    }

def create_http_json_response(data_dict):
    body = json.dumps(data_dict)
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: *\r\n"
        "Connection: keep-alive\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n"
        f"{body}"
    )
    return response.encode('utf-8')

def handle_client(client_socket, addr):
    try:
        client_socket.settimeout(10.0)
        while True:
            raw_data = client_socket.recv(8192)
            if not raw_data:
                break
            
            req_str = raw_data.decode('utf-8', errors='ignore')
            print(f"[PACKET RECEIVED] from {addr}: {req_str[:100]}...")

            player = get_player()
            base_url = "https://sigma-private-server.onrender.com/"
            
            # Universal Success JSON for all game endpoints
            response_payload = {
                "code": 0,
                "ret": 0,
                "status": "ok",
                "msg": "success",
                "server_online": True,
                "is_server_open": True,
                "is_firewall_open": True,
                "has_role": True,
                "is_created": True,
                "need_role": False,
                "server_url": base_url,
                "cdn_url": base_url,
                "gate_ip": base_url,
                "data": {
                    "account_id": player["account_id"],
                    "open_id": player["open_id"],
                    "nickname": player["nickname"],
                    "level": player["level"],
                    "gold": player["gold"],
                    "diamond": player["diamond"],
                    "has_role": True,
                    "is_created": True,
                    "in_lobby": True,
                    "server_time": int(time.time()),
                    "unlocked_characters": [101, 102, 103, 104, 105],
                    "unlocked_weapons": [201, 202, 203, 204]
                },
                "config": {
                    "remote_version": "1.0.1",
                    "is_review_server": False
                }
            }

            packet = create_http_json_response(response_payload)
            client_socket.sendall(packet)

    except Exception as e:
        print(f"[SOCKET ERROR] {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def start_server(host='0.0.0.0', port=8080):
    init_database()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)
    print(f"[HYBRID SERVER] Running on port {port}")

    while True:
        try:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"[ACCEPT ERROR] {e}")

if __name__ == '__main__':
    start_server()
