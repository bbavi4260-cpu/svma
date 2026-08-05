import socket

def start_udp_server(host='0.0.0.0', port=39001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[UDP SERVER] In-Game Realtime Sync Listening on {host}:{port}")

    while True:
        try:
            data, addr = sock.recvfrom(2048)
            # Echo back ping packet to keep player connected
            sock.sendto(data, addr)
        except Exception as e:
            print(f"[UDP ERROR]: {e}")
          
