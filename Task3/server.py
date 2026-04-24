
import socket
import threading
import random
import time

HOST          = '0.0.0.0'
TCP_PORT      = 6000
UDP_PORT      = 6001
BUFFER_SIZE   = 1024
FORMAT        = 'utf-8'
MIN_PLAYERS   = 2
MAX_PLAYERS   = 4
GUESS_RANGE   = (1, 100)
ROUND_TIMEOUT = 60
VOTE_TIMEOUT  = 15

lock            = threading.RLock()
tcp_clients     = {}
udp_clients     = {}
round_active    = False
awaiting_vote   = False
continue_votes  = {}

def broadcast_tcp(msg: str):
    with lock:
        for sock in list(tcp_clients.values()):
            try:
                sock.sendall(msg.encode(FORMAT))
            except:
                pass


def decide_after_votes():
    global awaiting_vote, round_active
    end_game = any(v != "yes" for v in continue_votes.values())
    if end_game:
        round_active = False
        broadcast_tcp("no winner\n")
    else:
        broadcast_tcp("Continuing game with remaining players...\n")

    awaiting_vote  = False
    continue_votes.clear()


# ────────────────────────────────────────────────────────────────────────────────
def handle_tcp_client(conn: socket.socket, addr):

    global round_active, awaiting_vote, continue_votes

    username = None
    try:
        conn.sendall("Welcome! Please join with: JOIN <username>\n".encode(FORMAT))
        data = conn.recv(BUFFER_SIZE).decode(FORMAT).strip()
        if not data.startswith("JOIN "):
            conn.sendall("Invalid command. Use: JOIN <username>\n".encode(FORMAT))
            conn.close()
            return

        username = data.split()[1]

        with lock:
            if (round_active or awaiting_vote or len(tcp_clients) >= MAX_PLAYERS
                    or username in tcp_clients):
                conn.sendall("Cannot join now.\n".encode(FORMAT))
                conn.close()
                return
            tcp_clients[username] = conn

        conn.sendall(
            f"Hello {username}! Waiting for {MIN_PLAYERS}-{MAX_PLAYERS} players...\n"
            .encode(FORMAT)
        )
        print(f"[TCP] {username} joined from {addr}")

        with lock:
            if len(tcp_clients) >= MIN_PLAYERS and not round_active:
                threading.Thread(target=game_udp_phase, daemon=True).start()

        while True:
            try:
                raw = conn.recv(BUFFER_SIZE)
            except:
                break
            if not raw:
                break
            msg = raw.decode(FORMAT).strip().lower()

            with lock:
                if awaiting_vote and msg in ("yes", "no"):
                    continue_votes[username] = msg
                    if len(continue_votes) == len(tcp_clients):
                        decide_after_votes()
                    continue

    except Exception as e:
        print(f"[ERROR] TCP {addr}: {e}")

    finally:
        with lock:
            tcp_clients.pop(username, None)
            aborted = round_active
        conn.close()

        if aborted:
            print(f"[DISCONNECT] {username} disconnected during round.")
            with lock:
                awaiting_vote  = True
                continue_votes = {}
            broadcast_tcp(
                f"{username} disconnected. Continue game with remaining players? (yes/no)\n"
            )

            deadline = time.time() + VOTE_TIMEOUT
            while True:
                time.sleep(0.5)
                with lock:
                    if not awaiting_vote:
                        break
                if time.time() > deadline:
                    with lock:
                        for u in tcp_clients:
                            continue_votes.setdefault(u, "no")
                        decide_after_votes()
                    break


# ────────────────────────────────────────────────────────────────────────────────
def game_udp_phase():
    global round_active, udp_clients

    with lock:
        round_active = True
        udp_clients  = {}

    secret = random.randint(*GUESS_RANGE)
    print(f"[GAME] secret = {secret}")

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    udp_sock.settimeout(ROUND_TIMEOUT)

    broadcast_tcp(f"Game starting with: {', '.join(tcp_clients.keys())}\n")
    broadcast_tcp(f"Switching to UDP on port {UDP_PORT}. REGISTER <username>\n")

    start = time.time()
    while (time.time() - start < ROUND_TIMEOUT and
           len(udp_clients) < len(tcp_clients)):
        try:
            data, addr = udp_sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            break
        parts = data.decode(FORMAT).strip().split()
        if parts[0] == "REGISTER":
            user = parts[1]
            with lock:
                if user in tcp_clients and user not in udp_clients:
                    udp_clients[user] = addr
                    udp_sock.sendto("REGISTERED\n".encode(FORMAT), addr)
                    print(f"[UDP] Registered {user}")

    for addr in udp_clients.values():
        udp_sock.sendto(
            f"ROUND_START {GUESS_RANGE[0]} {GUESS_RANGE[1]}\n".encode(FORMAT), addr
        )

    winner = None
    start = time.time()
    while round_active and not winner and time.time() - start < ROUND_TIMEOUT:
        try:
            data, addr = udp_sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            break
        parts = data.decode(FORMAT).strip().split()
        if parts[0] == "GUESS" and len(parts) >= 3:
            user, val = parts[1], parts[2]
            with lock:
                if udp_clients.get(user) != addr:
                    continue
            try:
                guess = int(val)
            except ValueError:
                continue
            if guess < GUESS_RANGE[0] or guess > GUESS_RANGE[1]:
                udp_sock.sendto(
                    "Warning: Out of the range, miss your chance\n".encode(FORMAT), addr
                )
                continue
            fb = ("Correct" if guess == secret
                  else "Higher" if guess < secret
                  else "Lower")
            udp_sock.sendto(f"{fb}\n".encode(FORMAT), addr)
            print(f"[GUESS] {user}: {guess} -> {fb}")
            if fb == "Correct":
                winner = user
                break

    if round_active:
        if winner:
            broadcast_tcp(f"WINNER {winner}\n")
        else:
            broadcast_tcp("No winner this round. Time's up!\n")

    udp_sock.close()
    with lock:
        round_active = False


if __name__ == "__main__":
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((HOST, TCP_PORT))
    server_sock.listen()
    print(f"[TCP] listening on {TCP_PORT}")
    try:
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()
    finally:
        server_sock.close()
