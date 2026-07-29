# Hospital Management System (TCP/UDP Sockets)

A multi-process hospital management system built for USC EE450. Five independent Python
processes communicate over localhost using TCP and UDP sockets, with a central hospital
server acting as the hub.

## Overview

The system runs in two phases:

- **Authentication** — The client SHA-256 hashes the username and password and sends them
  to the hospital server over TCP. The hospital server forwards them to the authentication
  server over UDP, which validates against `users.txt` and replies `AUTH_SUCCESS` or
  `AUTH_FAIL`. The hospital server then checks `hospital.txt` to classify the user as a
  `PATIENT` or `DOCTOR`.
- **Commands** — Once authenticated, users issue commands (`lookup`, `schedule`, `cancel`,
  `view_appointment`, `view_prescription`, `prescribe`). Every command flows
  Client → Hospital (TCP) → Appointment/Prescription server (UDP) → Hospital → Client.

The hospital server uses `select()` to multiplex its UDP socket, TCP listener, and all
active client connections at once. No threads or `fork()` are used.

## Architecture

| Process | Protocol | Port | Role |
|---|---|---|---|
| `authentication_server.py` | UDP | 21860 | Validates credentials against `users.txt` |
| `prescription_server.py` | UDP | 22860 | Reads/writes prescription records |
| `appointment_server.py` | UDP | 23860 | Reads/writes appointment slots |
| `hospital_server.py` | UDP / TCP | 25860 / 26860 | Central hub; routes all messages |
| `client.py` | TCP | dynamic | User-facing command-line client |

## Data Files

- `users.txt` — space-separated `<username_hash> <password_hash>` per line
- `hospital.txt` — `[Doctors]` and `[Treatments]` sections
- `appointments.txt` — per-doctor timeslots, with patient hash and illness when booked
- `prescriptions.txt` — saved prescription records

## Setup

This project is meant to run inside the CSCI 104 Docker container, which provides the
standard Ubuntu environment used for grading. Set up Docker and the `ch` container helper
by following the instructions here: https://github.com/csci104/docker/

Once installed, start the container and open a shell into it:

```bash
ch start csci104
ch shell csci104
```

Inside the shell, navigate to this project's directory (mounted from your host machine) and
run the code from there. Exit the shell with `Ctrl+D`, and stop the container when done:

```bash
ch stop csci104
```

## Running

Pure Python, standard library only — no build step. Inside the container shell, open a
separate terminal for each process (`ch shell csci104` in each) and start them in this
order:

```bash
python3 authentication_server.py
python3 prescription_server.py
python3 appointment_server.py
python3 hospital_server.py
python3 client.py '<username>' '<password>'
```

Enclose the username and password in single quotes.

## Notes

- All inter-process communication is over localhost sockets.
- Credentials are hashed with SHA-256; whitespace is stripped before hashing.
- Appointment times use `HH:MM` format within 09:00–16:00.
