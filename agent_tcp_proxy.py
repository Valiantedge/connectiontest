import socket
import threading

LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 2222
FORWARD_HOST = 'PRIVATE_SERVER_IP'  # Replace with your private server IP
FORWARD_PORT = 22  # SSH port

def handle_client(client_socket):
    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote.connect((FORWARD_HOST, FORWARD_PORT))
    def forward(src, dst):
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    threading.Thread(target=forward, args=(client_socket, remote)).start()
    threading.Thread(target=forward, args=(remote, client_socket)).start()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(5)
    print(f"Proxy listening on {LISTEN_HOST}:{LISTEN_PORT}, forwarding to {FORWARD_HOST}:{FORWARD_PORT}")
    while True:
        client_sock, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == "__main__":
    main()
