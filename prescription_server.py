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
    except KeyboardInterrupt:
        udp_sock.close()


if __name__ == "__main__":
    main()