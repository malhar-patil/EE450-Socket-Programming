import socket
import os
import sys

HOST = "127.0.0.1"
UDP_PORT = 22860

def save_treatment_details(payload):
    lines =None
    treatment_details = payload.strip().split(" ")
    with open("prescriptions.txt", "rt") as file:
        lines = [line.strip() for line in file.readlines()]
    

    lines.append(f"{treatment_details[0]} {treatment_details[1]} {treatment_details[4]} {treatment_details[3]}")
    with open("prescriptions.txt", "wt") as file:
        file.writelines("\n".join(lines))

def check_prescription_record(patient_hash):
    result = ["VIEW_PRESCRIPTION_DR|"]
    with open("prescriptions.txt", "rt") as file:
        for line in file:
            prescription_details = line.replace("\n","").strip().split(" ")
            if len(prescription_details) == 4 and prescription_details[1] == patient_hash:
                result.append(prescription_details[2])
                result.append(prescription_details[3])
                result.append(prescription_details[0])
                print(f"A prescription exists for this user.")
                return " ".join(result)
    
    result.append("NO_PRESCRIPTION_RECORD_FOUND")
    print(f"There are no current prescriptions for this user.")
    return " ".join(result)

def get_prescription_record(patient_hash):
    result = ["VIEW_PRESCRIPTION|"]
    with open("prescriptions.txt", "rt") as file:
        for line in file:
            prescription_details = line.replace("\n","").strip().split(" ")
            if len(prescription_details) == 4 and prescription_details[1] == patient_hash:
                result.append(prescription_details[2])
                result.append(prescription_details[3])
                result.append(prescription_details[0])
                if(prescription_details[3] == "None"):
                    print(f"There are no current prescriptions for this user.")
                else:
                    print(f"A prescription exists for this user.")
                return " ".join(result)
    
    result.append("NO_PRESCRIPTION_RECORD_FOUND")
    print(f"There are no current prescriptions for this user.")
    return " ".join(result)

def main():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind((HOST, UDP_PORT))

    print(f"Prescription Server is up and running using UDP on port {UDP_PORT}.")

    try:
        while True:
            data, addr = udp_sock.recvfrom(1024)
            command_type, _ , payload = data.decode().partition("|")

            if command_type == "PRESCRIBE":
                print(f"Prescription Server has received a request from {payload.strip().split(' ')[0]} to prescribe the user with hash suffix {payload.strip().split(' ')[1][-5:]}.")
                save_treatment_details(payload)
                udp_sock.sendto((f"PRESCRIBE_SAVE| {payload.strip().split(' ')[4]} {payload.strip().split(' ')[3]}").encode(), addr)
                print(f"Successfully saved the prescription details for user with hash suffix: {payload.strip().split(' ')[1][-5:]}.")
            
            elif command_type == "VIEW_PRESCRIPTION_DR":
                print(f"The prescription server has received a request to view the prescription for the user with hash suffix: {payload.strip().split(' ')[1][-5:]}.")
                result = check_prescription_record(payload.strip().split(" ")[1])
                udp_sock.sendto(result.encode(), addr)
            
            elif command_type == "VIEW_PRESCRIPTION":
                print(f"The prescription server has received a request to view the prescription for the user with hash suffix: {payload.strip().split(' ')[0][-5:]}.")
                result = get_prescription_record(payload.strip().split(" ")[0])
                udp_sock.sendto(result.encode(), addr)
    except KeyboardInterrupt:
        udp_sock.close()


if __name__ == "__main__":
    main()