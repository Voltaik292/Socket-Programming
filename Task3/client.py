import socket
import threading
import sys
import os

SERVER       = '127.0.0.1'
TCP_PORT     = 6000
UDP_PORT     = 6001
BUFFER_SIZE  = 1024
FORMAT       = 'utf-8'
UDP_TIMEOUT  = 30

PROMPT = "Your guess: "

def async_print(msg: str):

    sys.stdout.write('\r' + ' ' * (len(PROMPT) + 80) + '\r')
    sys.stdout.write(msg.rstrip() + '\n')
    sys.stdout.write(PROMPT)
    sys.stdout.flush()

start_udp = threading.Event()

def listen_tcp(sock: socket.socket):
    while True:
        try:
            msg = sock.recv(BUFFER_SIZE).decode(FORMAT)
            if not msg:
                break

            if msg.startswith("Switching to UDP"):
                start_udp.set()

            async_print(msg)

            if msg.lower().startswith("no winner"):
                async_print("Game aborted by server.")
                os._exit(0)
            if msg.startswith("WINNER"):
                os._exit(0)

        except:
            break

def tcp_phase(username: str) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER, TCP_PORT))

    async_print(sock.recv(BUFFER_SIZE).decode(FORMAT))
    sock.sendall(f"JOIN {username}".encode(FORMAT))

    threading.Thread(target=listen_tcp, args=(sock,), daemon=True).start()
    return sock

def udp_phase(username: str, tcp_sock: socket.socket):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.settimeout(UDP_TIMEOUT)

    try:
        udp.sendto(f"REGISTER {username}".encode(FORMAT), (SERVER, UDP_PORT))
        resp, _ = udp.recvfrom(BUFFER_SIZE)
        async_print(resp.decode(FORMAT).strip() + " -- registered")
    except:
        async_print("[ERROR] Registration failed.")
        return

    while True:
        try:
            data, _ = udp.recvfrom(BUFFER_SIZE)
        except:
            return
        parts = data.decode(FORMAT).strip().split()
        if parts[0] == "ROUND_START":
            async_print(f"Round start: guess between {parts[1]}-{parts[2]}")
            break

    while True:
        user_input = input(PROMPT).strip()

        if user_input.lower() in ('yes', 'no'):
            tcp_sock.sendall(user_input.encode(FORMAT))
            if user_input.lower() == 'no':
                async_print("Game ended by your decision.")
                udp.close()
                return
            continue

        udp.sendto(f"GUESS {username} {user_input}".encode(FORMAT),
                   (SERVER, UDP_PORT))
        try:
            fb, _ = udp.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            async_print("[ERROR] No feedback.")
            continue

        fb = fb.decode(FORMAT).strip()
        if fb.lower().startswith("warning:"):
            async_print(fb)
            continue

        async_print("Feedback: " + fb)
        if fb == "Correct":
            break

    udp.close()

def main():
    username = (sys.argv[1] if len(sys.argv) > 1
                else input("Enter your username: ").strip())

    tcp_sock = tcp_phase(username)

    start_udp.wait()

    udp_phase(username, tcp_sock)

    async_print("Waiting for result...\n")
    while True:
        try:
            data = tcp_sock.recv(BUFFER_SIZE)
        except:
            break
        if not data:
            break
        async_print(data.decode(FORMAT),)
    tcp_sock.close()

if __name__ == '__main__':
    main()
