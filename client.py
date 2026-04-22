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
    # Define tcp socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((HOST, HOSPITAL_TCP_PORT))
    client_port = tcp_sock.getsockname()[1]

    print(f"The client is up and running.")

    # Get client credentials
    username = sys.argv[1]
    username_hash = sha256_hash(sys.argv[1])
    password_hash = sha256_hash(sys.argv[2])
    user_credentials = (f"{username_hash}:{password_hash}")

    # Send authentication request to hospital server
    print(f"{username} sent an authentication request to the hospital server.")
    tcp_sock.sendall(user_credentials.encode())

    # Receive authentication response from hospital server
    user = tcp_sock.recv(1024).decode()

    # Check user status
    if(user == "PATIENT"):
        print(f"{username} received the authentication result. Authentication successful. You have been granted patient access.")
    elif(user == "DOCTOR"):
        print(f"{username} received the authentication result. Authentication successful. You have been granted doctor access.")
    else:
        print(f"The credentials are incorrect. Please try again.")
        tcp_sock.close()
        return


    try:
        while True:
            # Wait for command input from the user
            command = input()
            command_list = command.strip().split(" ")

            if(len(command_list) == 1 and command_list[0] == "lookup"):
                print(f"{username} sent a lookup request to the hospital server")
                tcp_sock.sendall("LOOKUP|lookup".encode())
                list_of_doctors = tcp_sock.recv(1024).decode().strip().split(" ")
                print(f"The client received the response from the hospital server using TCP over port {client_port}.\nThe Following doctors are available: ")
                for doctor in list_of_doctors:
                    print(f"{doctor}")
            
            elif(len(command_list) == 2 and command_list[0] == "lookup" and command_list[1].startswith("Dr.")):
                print(f"Patient {username} sent a lookup request to the hospital server for {command_list[1]}.")
                tcp_sock.sendall((f"LOOKUP_DR|{command_list[1]}").encode())
                available_timeslots = tcp_sock.recv(1024).decode().strip().split(" ")
                if len(available_timeslots) == 8:
                    print(f"The client received the response from the hospital server using TCP over port {client_port}. All time blocks are available for {command_list[1]}.")
                elif len(available_timeslots) == 1 and available_timeslots[0] == "NO_SLOT":
                    print(f"The client received the response from the Hospital Server using TCP over port {client_port}. {command_list[1]} has no time slots available.")
                else:
                    print(f"The client received the response from the Hospital Server using TCP over port {client_port}.\n{command_list[1]} is available at times: ")
                    for slot in available_timeslots:
                        print(f"{slot}")


                
    except KeyboardInterrupt:
        tcp_sock.close()


if __name__ == "__main__":

    main()
