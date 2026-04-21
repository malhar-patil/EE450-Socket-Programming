import socket
import os
import sys

HOST = "127.0.0.1"
UDP_PORT = 21860

def validate_user_credentials(user_credentials, udp_sock, addr):

    user_credentials = user_credentials.split(":")
    
    with open("users.txt","rt") as file:
        for user in file:
            hash_credentials = user.rstrip().split(" ")
            
            if user_credentials[0] == hash_credentials[0] and user_credentials[1] == hash_credentials[1]:
                print(f"Authentication succeeded for a user with hash suffix: {user_credentials[0][-5:]}.")
                udp_sock.sendto("AUTH_SUCCESS".encode(), addr)
                return

    print(f"Authentication failed for a user with hash suffix: {user_credentials[0][-5:]}.")
    udp_sock.sendto("AUTH_FAIL".encode(), addr)

def main():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind((HOST, UDP_PORT))

    print(f"Authentication Server is up and running using UDP on port {UDP_PORT}.")

    try:
        while True:
            data, addr = udp_sock.recvfrom(1024)
            user_credentials = data.decode()
            print(f"Authentication Server has received an authentication request for a user with hash suffix: {user_credentials.split(':')[0][-5:]}.")

            validate_user_credentials(user_credentials, udp_sock, addr)
            print(f"The Authentication Server has sent the authentication result to the Hospital Server.")
    except KeyboardInterrupt:
        udp_sock.close()


if __name__ == "__main__":
    main()