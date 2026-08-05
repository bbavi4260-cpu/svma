import socket
import threading
import json
import time
import sqlite3
import datetime

DB_FILE = 'accounts.db'

def log_message(tag, message):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] [{tag}] {message}")

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
        log_message("DB", "Database initialized successfully.")
    except Exception as e:
        log_message("DB ERROR", str(e))

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

def update_player_nickname(new_nickname):
    if not new_nickname or len(new_nickname.strip()) == 0:
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET nickname = ? WHERE open_id = ?", (new_nickname, "GUEST_100000001"))
        conn.commit()
        conn.close()
        log_message("DB UPDATE", f"Nickname successfully updated to: {new_nickname}")
    except Exception as e:
        log_message("DB ERROR", str(e))

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
    log_message("TCP CONNECT", f"Connection established from {addr[0]}:{addr[1]}")
    try:
        client_socket.settimeout(15.0)
        while True:
            raw_data = client_socket.recv(8192)
            if not raw_data:
                break
            
            req_str = raw_data.decode('utf-8', errors='ignore')
            first_line = req_str.splitlines()[0] if req_str.splitlines() else "GET /"
            
            # Print complete request log for debugging
            log_message("TCP REQ", f"From {addr[0]} -> {first_line}")
            
            # Capture nickname if sent in body
            if "nickname" in req_str.lower() or "name" in req_str.lower():
                try:
                    if "\r\n\r\n" in req_str:
                        body_part = req_str.split("\r\n\r\n")[1]
                        if "{" in body_part:
                            body_json = json.loads(body_part)
                            if "nickname" in body_json:
                                update_player_nickname(body_json["nickname"])
                            elif "name" in body_json:
                                update_player_nickname(body_json["name"])
                except Exception as ex:
                    log_message("PARSE ERROR", str(ex))

            player = get_player()
            base_url = "https://sigma-private-server.onrender.com/"

            # Response Payload
            response_payload = {
                "code": 0,
                "ret": 0,
                "status": 0,
                "msg": "success",
                "message": "success",
                "is_server_open": True,
                "is_firewall_open": True,
                "has_role": True,
                "is_created": True,
                "need_role": False,
                "token": "MASTER_TOKEN_BYPASS_100",
                "access_token": "MASTER_TOKEN_BYPASS_100",
                "refresh_token": "MASTER_REFRESH_BYPASS_100",
                "uid": str(player["account_id"]),
                "open_id": player["open_id"],
                "server_url": base_url,
                "cdn_url": base_url,
                "gate_ip": base_url,
                "data": {
                    "account_id": player["account_id"],
                    "uid": str(player["account_id"]),
                    "open_id": player["open_id"],
                    "nickname": player["nickname"],
                    "level": player["level"],
                    "exp": 99999,
                    "gold": player["gold"],
                    "diamond": player["diamond"],
                    "avatar_id": 1,
                    "gender": 1,
                    "character_id": 101,
                    "has_role": True,
                    "is_created": True,
                    "in_lobby": True,
                    "server_time": int(time.time()),
                    "unlocked_characters": [101, 102, 103, 104, 105],
                    "unlocked_weapons": [201, 202, 203, 204]
                },
                "config": {
                    "remote_version": "1.0.1",
                    "remote_option_version": "1.0.1",
                    "is_review_server": False
                }
            }

            packet = create_http_json_response(response_payload)
            client_socket.sendall(packet)
            log_message("TCP RES", f"Sent success response to {addr[0]}")

    except Exception as e:
        log_message("SOCKET ERROR", f"With {addr[0]} -> {str(e)}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        log_message("TCP DISCONNECT", f"Connection closed for {addr[0]}")

def start_tcp_server(host='0.0.0.0', port=8080):
    init_database()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)
    log_message("TCP SERVER", f"Server successfully started and listening on port {port}")

    while True:
        try:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client, addr))
            thread.daemon = True
            thread.start()
        except Exception as e:
            log_message("ACCEPT ERROR", str(e))

if __name__ == '__main__':
    start_tcp_server()
