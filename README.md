# Socket Programming

---

## Team Members


|---|
| Abdulrahman Sawalmeh |
| Kareem Hamza |
| Sameh Abu-Latifeh |

---

## Project Overview

This project covers three tasks in socket programming and computer networking:

- **Task 1** – Network command analysis and Wireshark DNS packet capture
- **Task 2** – A raw HTTP web server built using Python socket programming, serving bilingual (English/Arabic) HTML pages with images and video
- **Task 3** – A TCP/UDP hybrid multiplayer number-guessing game

All tasks are implemented in Python using only the standard library. No third-party packages are required.

---

## Repository Structure

```
T045_Project1/
│
├── README.md
│
├── docs/
│   ├── T045_Report.pdf          ← full project report
│   └── ProjectSpecifcations.pdf ← original project specification
│
├── Task1/
│   └── NetworksTask1.pcapng
│
├── Task2/
│   ├── server.py
│   ├── main_en.html
│   ├── main_ar.html
│   ├── mySite_1221574_en.html
│   ├── mySite_1221574_ar.html
│   ├── styles.css
│   ├── request_styles.css
│   ├── images/
│   │   ├── ENCS3320.png
│   │   ├── Member_image.png
│   │   ├── DDOS_Attack.png
│   │   ├── ip_spoofing.jpg
│   │   └── NetworkFirewall.png
│   └── Videos/
│       └── NetworkAttacks.mp4
│
└── Task3/
    ├── server.py
    └── client.py
```

---

## Task 1 – Network Commands & Wireshark

No code to run. All results are documented in `docs/T045_Report.pdf`.

The Wireshark DNS capture file is located at:
```
Task1/NetworksTask1.pcapng
```
Open it with [Wireshark](https://www.wireshark.org/) to inspect the DNS query and response for `gaia.cs.umass.edu`.

---

## Task 2 – HTTP Web Server

A simple HTTP web server built from scratch using Python's `socket` library. It serves bilingual HTML pages, handles images and video, and redirects to Google search when a requested file is not found on the server.

### Requirements

- Python 3.x
- No external libraries needed

### How to Run

> **Important:** You must run the server from **inside the `Task2/` folder** so it can locate the HTML, CSS, image, and video files correctly.

```bash
cd Task2
python server.py
```

The server will start on port **9954** and print:
```
Server is waiting for connection on port 9954...
```

### Accessing the Server

**From the same machine:**
```
http://localhost:9954
```

**From another device on the same local network:**
1. Find your machine's local IP address using `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. Open a browser on the other device and navigate to:
```
http://<your-local-ip>:9954
```
> You may need to allow port 9954 through your firewall. On Windows: *Windows Defender Firewall → Advanced Settings → Inbound Rules → New Rule → Port → TCP → 9954 → Allow*.

### Supported Routes

| URL | Response |
|---|---|
| `/` or `/en` or `/index.html` or `/main_en.html` | Main English page |
| `/ar` or `/main_ar.html` | Main Arabic page |
| `/mySite_1221574_en.html` | File request page (English) |
| `/mySite_1221574_ar.html` | File request page (Arabic) |
| `/images/<filename>` | Serves image from `images/` folder |
| `/Videos/<filename>` | Serves video from `Videos/` folder |
| `/request-file?filename=X&fileType=image\|video` | Serves file or redirects to Google search |
| Any other path | 404 error page with client IP and port |

### File Request Feature

On the file request page (`mySite_1221574_en.html`), users can enter a filename and select a type:

- If the file **exists** on the server → it is displayed directly in the browser
- If the file **does not exist**:
  - Image request → redirects to Google Images search
  - Video request → redirects to Google Videos search

### Server Behavior

- Prints every incoming HTTP request to the terminal
- Returns correct `Content-Type` headers (`text/html`, `text/css`, `image/png`, `image/jpeg`, `video/mp4`)
- CSS is inlined into HTML at startup so pages render correctly even without separate CSS requests

---

## Task 3 – TCP/UDP Hybrid Guessing Game

A multiplayer number-guessing game where players connect via TCP for registration and game control, then switch to UDP for fast-paced guessing rounds.

### Requirements

- Python 3.x
- No external libraries needed

### Game Settings

| Parameter | Value |
|---|---|
| TCP Port | 6000 |
| UDP Port | 6001 |
| Minimum Players | 2 |
| Maximum Players | 4 |
| Guess Range | 1 – 100 |
| Round Timeout | 60 seconds |
| Vote Timeout | 15 seconds |

### How to Run

**Step 1 – Start the server** (in one terminal):
```bash
cd Task3
python server.py
```

**Step 2 – Connect clients** (each player in a separate terminal):
```bash
python client.py
```
Or pass the username directly as an argument:
```bash
python client.py Sawalmeh_Abdulrahman
```

### Game Flow

1. Each client connects and sends `JOIN <username>`
2. The server waits until at least 2 players have joined
3. When enough players are connected, the game starts automatically
4. The server generates a secret number and switches all clients to UDP
5. Each client registers via UDP (`REGISTER <username>`)
6. The round begins — players send guesses and receive `Higher`, `Lower`, or `Correct` feedback
7. The first player to guess correctly wins; the result is broadcast to all players via TCP

### Disconnection Handling

If a player disconnects mid-game, the server asks remaining players to vote:
- All vote **yes** → game continues with remaining players
- Any player votes **no** → game ends with no winner
- No response within 15 seconds → game ends automatically

### Test Cases

| Scenario | Expected Result |
|---|---|
| 2 players, one guesses correctly | Winner announced to both players |
| Player guesses outside 1–100 | `Warning: Out of the range, miss your chance` |
| Player disconnects mid-round | Vote prompt sent to remaining players |
| No one guesses within 60s | `No winner this round. Time's up!` |

---

## Dependencies

No external packages are required. The following Python standard library modules are used:

| Module | Used In |
|---|---|
| `socket` | Task 2 & Task 3 |
| `os` | Task 2 |
| `threading` | Task 3 |
| `random` | Task 3 |
| `time` | Task 3 |
| `sys` | Task 3 (client) |

---

## Docs

All project documentation is in the `docs/` folder:

| File | Description |
|---|---|
| `docs/T045_Report.pdf` | Full project report — theory, procedure, screenshots, flowcharts, test results, and team contribution chart |
| `docs/Project1.pdf` | Original project specification issued by the instructor |

---

## References

1. Kurose, J. & Ross, K. — *Computer Networking: A Top-Down Approach*, 8th Edition
2. https://www.geeksforgeeks.org/differences-between-tcp-and-udp/
3. https://davisgitonga.dev/blog/request-response-cycle
