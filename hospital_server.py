import socket
import os
import sys
import select

AUTHENTICATION_SERVER_ADDRESS = "127.0.0.1"
AUTHENTICATION_SERVER_PORT = 21860
APPOINTMENT_SERVER_ADDRESS = "127.0.0.1"
APPOINTMENT_SERVER_PORT = 23860
PRESCRIPTION_SERVER_ADDRESS = "127.0.0.1"
PRESCRIPTION_SERVER_PORT = 22860

# Hospital server address/port information
HOST = "127.0.0.1"
UDP_PORT = 25860
TCP_PORT = 26860
BACKLOG = 5

# check if logged-in user is a doctor
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
            
# access validated, check for "DOCTOR" status by calling validate_user_credentials_as_doctor func
def get_user_access(authentication_response, user_credentials, client_sock):
    if authentication_response == "AUTH_SUCCESS":
        print(f"User with a hash suffix {user_credentials.split(':')[0][-5:]} has been granted access to the system. Determining the access of the user.")
        user = validate_user_credentials_as_doctor(user_credentials)
        client_sock.sendall(user.encode())
    else:
        client_sock.sendall("AUTH_FAIL".encode())
    print(f"Hospital Server has sent the response from Authentication Server to the client using TCP over port {TCP_PORT}.")

# check user credentials
def validate_user_credentials(user_credentials, udp_sock):
    udp_sock.sendto(user_credentials.encode(), (AUTHENTICATION_SERVER_ADDRESS, AUTHENTICATION_SERVER_PORT))
    print(f"Hospital Server has sent an authentication request to the Authentication Server.")

# get treatment for illness
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
    
    udp_sock.sendto(" ".join(appt_response_list).encode(), (PRESCRIPTION_SERVER_ADDRESS, PRESCRIPTION_SERVER_PORT))
    print(f"Hospital server has sent the prescription request to the prescription server to prescribe {appt_response_list[len(appt_response_list)-1]}.")

# main
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

    # Create buffers for client making a request
    auth_pending = []
    appt_pending = []
    pres_pending = []

    try:
        # store socket information
        sockets = [udp_sock, tcp_sock]


        while True:

            # select command to check which server is exchanging information with hospital server
            read_socks, _, _ = select.select(sockets, [], [])

            for sock in read_socks:

                # request/response from UDP socket
                if sock is udp_sock:
                    # data contains actual payload and addr contains address and port information
                    data, addr = udp_sock.recvfrom(1024)
                    response = data.decode()

                    # reponse from authentication server
                    if addr[1] == AUTHENTICATION_SERVER_PORT:
                        client_sock = auth_pending.pop(0)
                        creds = clients[client_sock]
                        print(f"Hospital server has received the response from the authentication server using UDP over port {UDP_PORT}.")
                        get_user_access(response, creds, client_sock)
                    
                    # response from appointment server
                    elif addr[1] == APPOINTMENT_SERVER_PORT:
                        # command_type ex. lookup, cancel, schedule, etc., payload has information that client/hospital_server requested 
                        command_type, _, payload = response.partition("|")
                        client_sock = appt_pending.pop(0)

                        # response for lookup command
                        if command_type == "LOOKUP":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"Hospital Server has sent the doctor lookup to the client.")
                        
                        # response for lookup <doctor> command
                        elif command_type == "LOOKUP_DR":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The Hospital Server has sent the response to the client.")

                        # response for schedule command
                        elif command_type == "SCHEDULE":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        
                        # response for view_appointment command for patient
                        elif command_type == "VIEW_APPOINTMENT":
                            print(f"Hospital Server has received the response from the appointment server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        
                        # response for view_appointment command for doctor
                        elif command_type == "VIEW_APPOINTMENT_DR":
                            print(f"Hospital server has received the response from the Appointment server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        
                        # response for cancel command
                        elif command_type == "CANCEL":
                            print(f"Hospital Server has received the response from Appointment Server using UDP over port {UDP_PORT}.")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        
                        # response for prescibe command by requested by doctor
                        elif command_type == "PRESCRIBE":
                            print(f"Hospital Server has received the illness response from the Appointment server using UDP over port {UDP_PORT}.")
                            illness = payload.strip().split(" ")[2]
                            pres_pending.append(client_sock)
                            print(f"Acquiring treatment for {illness} from the database.")
                            acquire_illness_treatment(payload, udp_sock)

                    # response from prescription server
                    elif addr[1] == PRESCRIPTION_SERVER_PORT:
                        command_type, _, payload = response.partition("|")

                        # response for prescription request made doctor
                        if command_type == "PRESCRIBE_SAVE":
                            client_sock = pres_pending.pop(0)
                            print(f"Hospital server has received the response from the prescription server using UDP over port {UDP_PORT}")
                            client_sock.sendall(payload.encode())
                            print(f"The hospital server has sent the response to the client.")
                        
                        # response for view prescription request made by doctor
                        elif command_type == "VIEW_PRESCRIPTION_DR":
                            client_sock = pres_pending.pop(0)
                            print(f"Hospital server has received the response from the prescription server using UDP over port {UDP_PORT}")
                            client_sock.sendall(payload.encode())
                            print(f"Hospital server has sent the response to the client.")
                        
                        # response for view prescription request made by patient
                        elif command_type == "VIEW_PRESCRIPTION":
                            client_sock = pres_pending.pop(0)
                            print(f"Hospital server has received the response from the prescription server using UDP over port {UDP_PORT}")
                            client_sock.sendall(payload.encode())
                            print(f"Hospital server has sent the response to the client.")

                # request/response from TCP socket 
                elif sock is tcp_sock:

                    new_fd, addr = tcp_sock.accept()
                    # get client socket information
                    creds = new_fd.recv(1024).decode()
                    # store client socket information in "clients" list
                    clients[new_fd] = creds

                    # add client info. to authentication list to tract user request
                    auth_pending.append(new_fd)

                    # append client socket info. to client list to track request/responses
                    sockets.append(new_fd)

                    print(f"Hospital Server received an authentication request from a user with hash suffix {creds.split(':')[0][-5:]}.")

                    # check input user credentials
                    validate_user_credentials(creds, udp_sock)   
                
                # request/response from client socket, added to clients list after validating their credentials 
                elif sock in clients:
                    client_sock = sock
                    # get user from the incoming client socket information
                    user_credentials = clients[client_sock]
                    data = client_sock.recv(1024).decode()

                    # check if client has closed their connection with hospital server
                    if not data:
                        sockets.remove(client_sock)
                        del clients[client_sock]
                        client_sock.close()
                        continue
                    
                    # command_type ex. lookup, cancel, schedule, etc., payload has information that client/hospital_server requested 
                    command_type, _, payload = data.partition("|")

                    # request made for lookup command
                    if(command_type == "LOOKUP"):
                        print(f"Hospital Server received a lookup request from a user with a hash suffix {user_credentials.split(':')[0][-5:]} over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"Hospital Server sent the doctor lookup request to the Appointment server.")

                    # request made for lookup <doctor> command
                    elif(command_type == "LOOKUP_DR"):
                        print(f"Hospital Server has received a lookup request from a user with hash suffix {user_credentials.split(':')[0][-5:]} to lookup {payload} availability using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"Hospital Server sent the doctor lookup request to the Appointment server.")
                    
                    # request made for schedule command
                    elif(command_type == "SCHEDULE"):
                        print(f"Hospital Server has received a schedule request from a user with hash suffix: {user_credentials.split(':')[0][-5:]} to book an appointment using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        data = data + " " + user_credentials.split(':')[0]
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"Hospital Server has sent the schedule request to the appointment server.")
                    
                    # request for view_appointment command
                    elif(command_type == "VIEW_APPOINTMENT"):
                        print(f"Hospital server has received a view appointment request from a user with hash suffix {user_credentials.split(':')[0][-5:]} to view their appointment details using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        data = data + " " + user_credentials.split(':')[0]
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"Hospital Server has sent the view appointments request to the Appointment Server.")
                    
                    # request for view_appointment command by doctor
                    elif(command_type == "VIEW_APPOINTMENT_DR"):
                        print(f"Hospital Server has received a view appointments request from {payload.rstrip().split(' ')[1]} to view their schedule details using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"The hospital server has sent the view appointments request to the Appointment Server.")
                    
                    # request for cancel command
                    elif(command_type == "CANCEL"):
                        print(f"Hospital Server has received a cancel request from user with hash suffix: {user_credentials.split(':')[0][-5:]} to cancel their appointment using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        data = data +" "+user_credentials.split(":")[0]
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"The hospital server has sent the cancel request to the appointment server.")
                    
                    # request for prescribe command by doctor
                    elif(command_type == "PRESCRIBE"):
                        print(f"Hospital Server has received a prescription request from {payload.strip().split(' ')[0]} for a user with hash suffix {payload.strip().split(' ')[1][-5:]} using TCP over port {TCP_PORT}.")
                        appt_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), (APPOINTMENT_SERVER_ADDRESS, APPOINTMENT_SERVER_PORT))
                        print(f"Hospital Server has sent a request to fetch patients with hash suffix {payload.strip().split(' ')[1][-5:]} illness information to the Appointment Server.")
                    
                    # request for view_prescription command by doctor
                    elif(command_type == "VIEW_PRESCRIPTION_DR"):
                        print(f"Hospital Server has received a prescription request from {payload.strip().split(' ')[0]} to view a patient with hash suffix {payload.strip().split(' ')[1][-5:]} prescription details using TCP over port {TCP_PORT}.")
                        pres_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), (PRESCRIPTION_SERVER_ADDRESS, PRESCRIPTION_SERVER_PORT))
                        print(f"Hospital Server has sent the prescription request to the Prescription Server.")
                    
                    # request for view_presciption command by user
                    elif(command_type == "VIEW_PRESCRIPTION"):
                        print(f"Hospital Server has received a prescription request from a patient with hash suffix {payload.strip().split(' ')[0][-5:]} to view their prescription details using TCP over port {TCP_PORT}.")
                        pres_pending.append(client_sock)
                        udp_sock.sendto(data.encode(), (PRESCRIPTION_SERVER_ADDRESS, PRESCRIPTION_SERVER_PORT))
                        print(f"Hospital Server has sent the prescription request to the Prescription Server.")
    
    # keyboard interrupt for ctrl+c check          
    except KeyboardInterrupt:
        tcp_sock.close()
        udp_sock.close()

if __name__ == "__main__":
    main()


