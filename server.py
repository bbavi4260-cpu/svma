from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Global player profile state
player_data = {
    "account_id": 100000001,
    "open_id": "GUEST_100000001",
    "nickname": "Master",
    "level": 60,
    "gold": 999999,
    "diamond": 999999
}

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def catch_all(path):
    print(f"[FLASK REQ] Path: /{path} | Method: {request.method}")
    
    # Agar client ne nickname bheja hai toh use capture kar lo
    if request.is_json:
        content = request.get_json(silent=True)
        if content and isinstance(content, dict):
            if "nickname" in content:
                player_data["nickname"] = content["nickname"]
                print(f"[NICKNAME UPDATED]: {player_data['nickname']}")

    base_url = "https://sigma-private-server.onrender.com/"

    # Universal Success Response Structure for Game Clients
    response_payload = {
        "code": 0,
        "ret": 0,
        "msg": "success",
        "status": "ok",
        "is_server_open": True,
        "is_firewall_open": True,
        "has_role": True,
        "is_created": True,
        "need_role": False,
        "server_url": base_url,
        "cdn_url": base_url,
        "gate_ip": base_url,
        "data": {
            "account_id": player_data["account_id"],
            "open_id": player_data["open_id"],
            "nickname": player_data["nickname"],
            "level": player_data["level"],
            "gold": player_data["gold"],
            "diamond": player_data["diamond"],
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

    return jsonify(response_payload), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
            
