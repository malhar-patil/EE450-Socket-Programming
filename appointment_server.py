import socket
import os
import sys

HOST = "127.0.0.1"
UDP_PORT = 23860

def get_available_doctors():
    available = ["LOOKUP|"]
    current_doctor = None
    has_free_slot = False

    with open("appointments.txt", "rt") as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_doctor and has_free_slot:
                    available.append(current_doctor)
                current_doctor = None
                has_free_slot = False
            elif line.startswith("Dr."):
                current_doctor = line
                has_free_slot = False
            elif len(line.split()) == 1:
                has_free_slot = True

    if current_doctor and has_free_slot:
        available.append(current_doctor)

    return " ".join(available)

def get_available_time_slots(doctor):
    available = ["LOOKUP_DR|"]
    total_time_slots = 8

    with open("appointments.txt", "rt") as file:
        for line in file:
            line  = line.strip()
            if(total_time_slots == 0):
                break
            if(line.startswith(doctor)):
                is_doctor_present = True
                continue
            if(is_doctor_present and len(line.split()) == 1):
                available.append(line)
            total_time_slots-=1
 
    
    if(len(available) == 9):
        print(f"All time blocks are available for {doctor}.")
    elif(len(available) == 1):
        print(f"{doctor} has no time slots available.")
    else:
        print(f"{doctor} has some time slots available.")
    print(available)
    return " ".join(available)


def main():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind((HOST, UDP_PORT))

    print(f"Appointment Server is up and running using UDP on port {UDP_PORT}.")

    try:
        while True:
            data, addr = udp_sock.recvfrom(1024)
            command_type,_, payload = data.decode().partition("|")
            if command_type == "LOOKUP":
                print(f"The Appointment Server has received a doctor availability request.")
                result = get_available_doctors()
                udp_sock.sendto(result.encode(), addr)
                print(f"The Appointment Server has sent the lookup result to the Hospital Server.")
            elif command_type == "LOOKUP_DR":
                print(f"The Appointment Server has received a doctor availability request.")
                result = get_available_time_slots(payload)
                udp_sock.sendto(result.encode(), addr)
                print(f"The Appointment Server has sent the lookup result to the Hospital Server.")

                

    except KeyboardInterrupt:
        udp_sock.close()


if __name__ == "__main__":
    main()
    