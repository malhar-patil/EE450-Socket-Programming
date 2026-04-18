import socket
import os
import sys
import hashlib

HOST = "127.0.0.1"
HOSPITAL_TCP_PORT = 26860

def sha256_hash(text: str) -> str:
    text = text.strip()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((HOST, HOSPITAL_TCP_PORT))

    print(f"The client is up and running.")

    # Get client credentials
    username = sha256_hash(sys.argv[1])
    password = sha256_hash(sys.argv[2])
    user_credentials = (f"{username}:{password}")

    tcp_sock.sendall(user_credentials.encode())


    try:
        while True:
            command = input()
    except KeyboardInterrupt:
        tcp_sock.close()


if __name__ == "__main__":
    main()
