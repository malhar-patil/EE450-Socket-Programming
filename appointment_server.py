import socket
import os
import sys

HOST = "127.0.0.1"
UDP_PORT = 23860

def main():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind((HOST, UDP_PORT))

    print(f"Appointment Server is up and running using UDP on port {UDP_PORT}.")

    try:
        while True:
            data, addr = udp_sock.recvfrom(1024)
    except KeyboardInterrupt:
        udp_sock.close()


if __name__ == "__main__":
    main()
    