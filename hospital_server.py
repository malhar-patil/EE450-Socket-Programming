import socket
import os
import sys
import select

AUTHENTICATION_SERVER_ADDRESS = "127.0.0.1"
AUTHENTICATION_SERVER_PORT = 21860

HOST = "127.0.0.1"
UDP_PORT = 25860
TCP_PORT = 26860
BACKLOG = 5

def get_list_of_doctors():
    list_of_doctors = ""
    with open("hospital.txt", "rt") as file:
        for line in file:
            doctor_information = line.strip().split(" ")
            if(doctor_information[0] == "[Treatments]"):
                break
            if(len(doctor_information) == 2 and doctor_information[0].startswith("Dr.")):
                list_of_doctors = list_of_doctors + " " + doctor_information[0]
    return list_of_doctors
            


def validate_user_credentials_as_doctor(user_credentials):
    user_credentials = user_credentials.split(":")
    with open ("hospital.txt", "rt") as file:
        for line in file:
            doctor_information = line.strip().split(" ")
            if len(doctor_information) == 1:
                continue
            if user_credentials[0] == doctor_information[1]:
                print(f"User with hash suffix {user_credentials[0][-5:]} will be granted doctor access.")
                return "DOCTOR"
    
    print(f"User with hash {user_credentials[0][-5:]} will be granted patient access.")
    return "PATIENT"
            


def get_user_access(authentication_response, user_credentials, client_sock):
    if authentication_response == "AUTH_SUCCESS":
        print(f"User with a hash suffix {user_credentials.split(':')[0][-5:]} has been granted access to the system. Determining the access of the user.")
        user = validate_user_credentials_as_doctor(user_credentials)
        client_sock.sendall(user.encode())
    else:
        client_sock.sendall("AUTH_FAIL".encode())
    print(f"Hospital Server has sent the response from Authentication Server to the client using TCP over port {TCP_PORT}.")

    

def validate_user_credentials(user_credentials, udp_sock):
    udp_sock.sendto(user_credentials.encode(), (AUTHENTICATION_SERVER_ADDRESS, AUTHENTICATION_SERVER_PORT))
    print(f"Hospital Server has sent an authentication request to the Authentication Server.")

def main():

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind((HOST, UDP_PORT))

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen(5)

    print(f"Hospital Server is up and running using UDP on port {UDP_PORT}.")
    user_credentials = None
    client_sock = None
    try:
        sockets = [udp_sock, tcp_sock]
        while True:
            read_socks, _, _ = select.select(sockets, [], [])
            for sock in read_socks:
                if sock is udp_sock:
                    data, addr = udp_sock.recvfrom(1024)

                    authentication_response = data.decode()
                    print(f"Hospital server has received the response from the authentication server using UDP over port {UDP_PORT}.")
                    get_user_access(authentication_response, user_credentials, client_sock)

                elif sock is tcp_sock:
                    new_fd, addr = tcp_sock.accept()
                    user_credentials = new_fd.recv(1024).decode()
                    client_sock = new_fd
                    sockets.append(client_sock)

                    print(f"Hospital Server received an authentication request from a user with hash suffix: {user_credentials.split(':')[0][-5:]}.")
                    validate_user_credentials(user_credentials, udp_sock)   
                
                elif sock is client_sock:
                    data = client_sock.recv(1024).decode()
                    command_list = data.strip().split(" ")
                    if(len(command_list) == 1 and command_list[0] == "lookup"):
                        client_sock.sendall(get_list_of_doctors().encode())
                        


                
    except KeyboardInterrupt:
        tcp_sock.close()
        udp_sock.close()

if __name__ == "__main__":
    main()


