import threading
import os
import tcp
import udp2

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("==================================================")
    print("        SIGMA PRIVATE SERVER ONLINE (24/7)        ")
    print("==================================================")
    print(f" [*] TCP Server Port  : {port}")
    print(f" [*] UDP Server Port  : 39001")
    print("==================================================\n")
    
    # TCP Server Thread
    tcp_thread = threading.Thread(target=tcp.start_tcp_server, args=('0.0.0.0', port))
    tcp_thread.daemon = True
    tcp_thread.start()

    # UDP Server Thread
    udp_thread = threading.Thread(target=udp2.start_udp_server, args=('0.0.0.0', 39001))
    udp_thread.daemon = True
    udp_thread.start()

    tcp_thread.join()
