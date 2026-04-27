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

def acquire_illness_treatment(appt_response, udp_sock):
    appt_response_list = ["PRESCRIBE|"]
    appt_response_list.extend(appt_response.strip().split(" "))
    illness = appt_response_list[3]

    with open("hospital.txt", "rt") as file:
        for line in file:
            line_data = line.rstrip().split(" ")
            if len(line_data) == 2 and line_data[0] == illness:
                appt_response_list.append(line_data[1])
                break
    
    udp_sock.sendto(" ".join(appt_response_list).encode(), ("127.0.0.1", 22860))
    print(f"Hospital server has sent the prescription request to the prescription server to prescribe {appt_response_list[len(appt_response_list)-1]}.")

    

    

def main():

    # Define UDP socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind((HOST, UDP_PORT))

    # Define TCP socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen(5)

    print(f"Hospital Server is up and running using UDP on port {UDP_PORT}.")
    # Save user information
    clients = {}
    auth_pending = []
    appt_pending = []
    pres_pending = []

    try:
        sockets = [udp_sock, tcp_sock]
        while True:
            read_socks, _, _ = select.select(sockets, [], [])
            for sock in read_socks:

                if sock is udp_sock:
                    data, addr = udp_sock.recvfrom(1024)
                    response = data.decode()

                    if addr[1] == 21860:
                        client_sock = auth_pending.pop(0)
                        creds = clients[client_sock]
                        print(f"Hospital server has received the response from the authentication server using UDP over port {UDP_PORT}.")
                        get_user_access(response, creds, client_sock)
                    
                    elif addr[1] == 23860:
                        command_type, _, payload = response.partition("|")
                        client_sock = appt_pending.pop(0)
                        if command_type == "LOOKUP":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"Hospital Server has sent the doctor lookup to the client.")
                        elif command_type == "LOOKUP_DR":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The Hospital Server has sent the response to the client.")
                        elif command_type == "SCHEDULE":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        elif command_type == "VIEW_APPOINTMENT":
                            print(f"Hospital Server has received the response from the appointment server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        elif command_type == "VIEW_APPOINTMENT_DR":
                            print(f"Hospital server has received the response from the Appointment server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        elif command_type == "CANCEL":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        elif command_type == "PRESCRIBE":
                            print(f"Hospital Server has received the illness response from the Appointment server using UDP over port {UDP_PORT}.")
                            illness = payload.strip().split(" ")[2]
                            pres_pending.append(client_sock)
                            print(f"Acquiring treatment for {illness} from the database.")
                            acquire_illness_treatment(payload, udp_sock)
                    elif addr[1] == 22860:
                        command_type, _, payload = response.partition("|")
                        if command_type == "PRESCRIBE_SAVE":
                            client_sock = pres_pending.pop(0)
                            print(f"Hospital server has received the response from the prescription server using UDP over port {UDP_PORT}")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        
                        elif command_type == "VIEW_PRESCRIPTION_DR":
                            client_sock = pres_pending.pop(0)
                            print(f"Hospital server has received the response from the prescription server using UDP over port {UDP_PORT}")
                            client_sock.sendall(payload.encode())
                            print(f"Hospital server has sent the response to the client.")
                        
                        elif command_type == "VIEW_PRESCRIPTION":
                            client_sock = pres_pending.pop(0)
                            print(f"Hospital server has received the response from the prescription server using UDP over port {UDP_PORT}")
                            client_sock.sendall(payload.encode())
                            print(f"Hospital server has sent the response to the client.")

                elif sock is tcp_sock:
                    new_fd, addr = tcp_sock.accept()
                    creds = new_fd.recv(1024).decode()
                    clients[new_fd] = creds
                    auth_pending.append(new_fd)
                    sockets.append(new_fd)

                    print(f"Hospital Server received an authentication request from a user with hash suffix {creds.split(':')[0][-5:]}.")
                    validate_user_credentials(creds, udp_sock)   
                
                elif sock in clients:
                    client_sock = sock
                    user_credentials = clients[client_sock]
                    data = client_sock.recv(1024).decode()

                    if not data:
                        sockets.remove(client_sock)
                        del clients[client_sock]
                        client_sock.close()
                        continue

                    command_type, _, payload = data.partition("|")

                    if(command_type == "LOOKUP"):
                        print(f"Hospital Server received a lookup request from a user with a hash suffix {user_credentials.split(':')[0][-5:]} over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), ("127.0.0.1", 23860))
                        print(f"Hospital Server sent the doctor lookup request to the Appointment server.")
                    elif(command_type == "LOOKUP_DR"):
                        print(f"Hospital Server has received a lookup request from a user with hash suffix {user_credentials.split(':')[0][-5:]} to lookup {payload} availability using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), ("127.0.0.1", 23860))
                        print(f"Hospital Server sent the doctor lookup request to the Appointment server.")
                    elif(command_type == "SCHEDULE"):
                        print(f"Hospital Server has received a schedule request from a user with hash suffix: {user_credentials.split(':')[0][-5:]} to book an appointment using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        data = data + " " + user_credentials.split(':')[0]
                        udp_sock.sendto(data.encode(), ("127.0.0.1", 23860))
                        print(f"Hospital Server has sent the schedule request to the appointment server.")
                    elif(command_type == "VIEW_APPOINTMENT"):
                        print(f"Hospital server has received a view appointment request from a user with hash suffix {user_credentials.split(':')[0][-5:]} to view their appointment details using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        data = data + " " + user_credentials.split(':')[0]
                        udp_sock.sendto(data.encode(), ("127.0.0.1", 23860))
                        print(f"Hospital Server has sent the view appointments request to the Appointment Server.")
                    elif(command_type == "VIEW_APPOINTMENT_DR"):
                        print(f"Hospital Server has received a view appointments request from {payload.rstrip().split(' ')[1]} to view their schedule details using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), ("127.0.0.1", 23860))
                        print(f"The hospital server has sent the view appointments request to the Appointment Server.")
                    elif(command_type == "CANCEL"):
                        print(f"Hospital Server has received a cancel request from user with hash suffix: {user_credentials.split(':')[0][-5:]} to cancel their appointment using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        data = data +" "+user_credentials.split(":")[0]
                        udp_sock.sendto(data.encode(), ("127.0.0.1", 23860))
                        print(f"The hospital server has sent the cancel request to the appointment server.")
                    elif(command_type == "PRESCRIBE"):
                        print(f"Hospital Server has received a prescription request from {payload.strip().split(' ')[0]} for a user with hash suffix {payload.strip().split(' ')[1][-5:]} using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), ('127.0.0.1', 23860))
                        print(f"Hospital Server has sent a request to fetch patients with hash suffix {payload.strip().split(' ')[1][-5:]} illness information to the Appointment Server.")
                    elif(command_type == "VIEW_PRESCRIPTION_DR"):
                        print(f"Hospital Server has received a prescription request from {payload.strip().split(' ')[0]} to view a patient with hash suffix {payload.strip().split(' ')[1][-5:]} prescription details using TCP over port {TCP_PORT}.")
                        pres_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), ('127.0.0.1', 22860))
                        print(f"Hospital Server has sent the prescription request to the Prescription Server.")
                    elif(command_type == "VIEW_PRESCRIPTION"):
                        print(f"Hospital Server has received a prescription request from a patient with hash suffix {payload.strip().split(' ')[0][-5:]} to view their prescription details using TCP over port {TCP_PORT}.")
                        pres_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), ('127.0.0.1', 22860))
                        print(f"Hospital Server has sent the prescription request to the Prescription Server.")





                    
                        


                        


                
    except KeyboardInterrupt:
        tcp_sock.close()
        udp_sock.close()

if __name__ == "__main__":
    main()


