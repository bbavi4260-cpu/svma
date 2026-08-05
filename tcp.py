from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SigmaServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[HTTP LOG] {self.address_string()} - {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def send_json_response(self, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def process_request(self):
        path = self.path.lower()
        print(f"[REQ PATH]: {path}")

        base_url = "https://svmx.onrender.com/"

        # Fully Dynamic Ready Payload (Forces "Tap to Begin" to pass into Lobby)
        server_ready_payload = {
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
                "exp": 99999,
                "gold": 999999,
                "diamond": 999999,
                "avatar_id": 1,
                "gender": 1,
                "character_id": 101,
                "has_role": True,
                "is_created": True,
                "unlocked_characters": [101, 102]
            }
        }

        # Main Server Config Protocol Response
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
            "client_ip": self.client_address[0] if self.client_address else "127.0.0.1",
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

        # Routing Logic
        if any(k in path for k in ["config", "ver", "client"]):
            print("[MATCH] Config Check Response")
            self.send_json_response(config_payload)
        elif any(k in path for k in ["guest", "oauth", "login"]):
            print("[MATCH] Guest Login Response")
            guest_payload = {
                "open_id": "GUEST_100000001",
                "access_token": "GUEST_TOKEN_1785865047",
                "refresh_token": "GUEST_TOKEN_1785865047",
                "expiry_time": 1817401047,
                "platform": 4,
                "uid": "100000001",
                "ret": 0,
                "code": 0,
                "msg": "success",
                "has_role": True,
                "is_created": True
            }
            self.send_json_response(guest_payload)
        else:
            # Captures all Tap to Begin / Role / Server Check requests
            print("[MATCH] Active Handshake -> Universal Ready Response Sent")
            self.send_json_response(server_ready_payload)

    def do_GET(self):
        self.process_request()

    def do_POST(self):
        self.process_request()

def start_tcp_server(host='0.0.0.0', port=8080):
    server_address = (host, port)
    httpd = HTTPServer(server_address, SigmaServerHandler)
    print(f"[HTTP SERVER] Listening on {host}:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    start_tcp_server()
