# P2P Battleship (Pygame)

A peer-to-peer 2-player Battleship game written in Python using raw sockets (`socket`) and `pygame-ce`.

## Features

- Local network automatic room discovery via UDP broadcast.
- Turn-based gameplay over raw TCP sockets with newline framing.
- Interactive ship placement with rotation and placement buffer enforcement.
- Dual-board rendering: player fleet on the left, radar/attack board on the right.

## Requirements

- Python 3.10+
- `pygame-ce`

Install the dependency:

```bash
pip install -r requirements.txt
```
