import socket
import os
import sys

HOST = "127.0.0.1"
UDP_PORT = 23860

# get list of available doctors
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

# get available time slots of a doctor
def get_available_time_slots(doctor):
    
    available = ["LOOKUP_DR|"]
    total_time_slots = 8
    is_doctor_present = False

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
            elif(is_doctor_present and len(line.split()) != 1):
                total_time_slots-=1
 
    
    if(len(available) == 9):
        print(f"All time blocks are available for {doctor}.")
    elif(len(available) == 1):
        available.append("NO_SLOT")
        print(f"{doctor} has no time slots available.")
    else:
        print(f"{doctor} has some time slots available.")

    return " ".join(available)

def check_input_format(schedule_argument):
    hour, minute = schedule_argument[1].split(":")
    hour = int(hour)
    minute = int(minute)
    if not ((hour >= 9 and hour <=16) and minute == 0):
        return False
    return True

# schedule appointment
def schedule_appointment(schedule_arguments):
    available_slots = ["SCHEDULE|"]
    if not check_input_format(schedule_arguments):
        available_slots.append("INCORRECT_INPUT_FORMAT")
        return " ".join(available_slots)

    is_doctor_present = False
    total_time_slots = 8
    appointment_scheduled_successfully = False

    lines = None
    with open("appointments.txt", "rt") as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        if total_time_slots == 0:
            break
        if line == schedule_arguments[0]:
            is_doctor_present = True
            continue
        
        if is_doctor_present:
            line_contents = line.split(" ")
            if line_contents[0] == schedule_arguments[1] and len(line_contents) == 3:
                print(f"The requested appointment time is not available.")
                break
            elif line_contents[0] == schedule_arguments[1] and len(line_contents) == 1:
                lines[i] = f"{schedule_arguments[1]} {schedule_arguments[3]} {schedule_arguments[2]}\n"
                print(f"Appointment has been scheduled successfully for user {schedule_arguments[3][-5:]} with {schedule_arguments[0]}.")
                appointment_scheduled_successfully = True
                available_slots.append("APPOINTMENT_SCHEDULED_SUCCESSFULLY")
                break
            total_time_slots -= 1
    

    if not appointment_scheduled_successfully:
        total_time_slots = 8
        is_doctor_present = False

        with open("appointments.txt", "rt") as file:
            for line in file:
                line  = line.strip()
                if(total_time_slots == 0):
                    break
                if(line.startswith(schedule_arguments[0])):
                    is_doctor_present = True
                    continue
                if(is_doctor_present and len(line.split()) == 1):
                    available_slots.append(line)
                    total_time_slots-=1
                elif (is_doctor_present and len(line.split()) != 1):
                    total_time_slots-=1
                
        
        if len(available_slots) == 1:
            available_slots.append("NO_SLOT")

    with open ("appointments.txt", "w") as file:
        file.writelines(lines)

    return " ".join(available_slots)

def view_appointment(username_hash):
    result = ["VIEW_APPOINTMENT|"]
    doctor = None
    with open("appointments.txt", "rt") as file:
        for line in file:
            if(line.startswith("Dr")):
                doctor = line
                continue

            appointment_info = line.strip().split(" ")
            if(len(appointment_info) == 3 and appointment_info[1] == username_hash):
                result.append(doctor)
                result.append(appointment_info[0])
                print(f"Returning details regarding the appointment for the user with hash suffix {username_hash[-5:]}.")
                return " ".join(result)
    
    result.append("NO_APPOINTMENT_FOUND")
    print(f"The user with hash suffix {username_hash[-5:]} has no appointment in the system.")
    return " ".join(result)

def view_appointment_doctor(doctor_name):
    result = ["VIEW_APPOINTMENT_DR|"]
    has_appointment = False
    is_doctor_present = False
    total_time_slots = 8

    with open("appointments.txt", "rt") as file:
        for line in file:
            if(total_time_slots <= 0):
                break
            if(line.startswith(doctor_name)):
                is_doctor_present = True
                continue

            if is_doctor_present:
                appointment_info = line.split(" ")
                if(len(appointment_info) == 3):
                    has_appointment = True
                    result.append(appointment_info[0])
                total_time_slots -= 1  
                 
    
    if not has_appointment:
        result.append("NO_APPOINTMENT_FOUND")
        print(f"No appointments have been made for {doctor_name}.")
        return " ".join(result)
    print(f"Returning the scheduled appointments for {doctor_name}.")
    return " ".join(result)

def cancel_appointment(username):
    result = ["CANCEL|"]
    doctor = None
    with open("appointments.txt", "rt") as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines):
        if(line.startswith("Dr.")):
            doctor = line.strip()
            continue
        appointment_info = line.strip().replace("\n", "").split(" ")
        if len(appointment_info) == 3 and appointment_info[1] == username:
            lines[i] = f"{appointment_info[0]}\n"
            result.append(doctor)
            result.append(appointment_info[0])
            with open("appointments.txt", "wt") as file:
                file.writelines(lines)
            print(f"Successfully cancelled appointment.")
            return " ".join(result)
        
    with open("appointments.txt", "wt") as file:
        file.writelines(lines)
    result.append("NO_APPOINTMENT_FOUND") 
    print(f"Error: Failed to find appointment.")
    return " ".join(result)


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
            elif command_type == "SCHEDULE":
                schedule_arguments = payload.split(" ")
                print(f"Appointment scheduling request received (time: {schedule_arguments[1]}, doctor: {schedule_arguments[0]}, patient hash suffix: {schedule_arguments[3][-5:]}, illness: {schedule_arguments[2]}).")
                result = schedule_appointment(schedule_arguments)
                udp_sock.sendto(result.encode(), addr)
            elif command_type == "VIEW_APPOINTMENT":
                username_hash = payload.strip().split(" ")[1]
                print(f"Appointment Server has received a view appointment command for the user with hash suffix {username_hash[-5:]}.")
                result = view_appointment(username_hash)
                udp_sock.sendto(result.encode(), addr)
            elif command_type == "VIEW_APPOINTMENT_DR":
                doctor_name = payload.rstrip().split(" ")[1]
                print(f"Appointment Server has received a request to view appointments scheduled for {doctor_name}.")
                result = view_appointment_doctor(doctor_name)
                udp_sock.sendto(result.encode(), addr)
            elif command_type == "CANCEL":
                username = payload.rstrip().split(" ")[1]
                print(f"Appointment Server has received a cancel appointment command for the user with hash suffix: {username[-5:]}.")
                result = cancel_appointment(username)
                udp_sock.sendto(result.encode(), addr)


                

    except KeyboardInterrupt:
        udp_sock.close()


if __name__ == "__main__":
    main()
    