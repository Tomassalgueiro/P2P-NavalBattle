import sys
import time
from game_state import Game, GamePhase
from network import NetworkManager
from table import FLEET_CONFIG


def auto_place_fleet(game: Game) -> None:
    """Quickly places all 5 ships in legal, non-adjacent rows for testing."""
    row = 0
    for ship_name in FLEET_CONFIG:
        placed = game.myTable.place_ship(ship_name, x=0, y=row, horizontal=True)
        if not placed:
            raise RuntimeError(f"Failed to auto-place {ship_name} at row {row}")
        row += 2


def print_boards(game: Game) -> None:
    """Displays your fleet and your radar board side-by-side."""
    print("\n--- YOUR FLEET (Left) --------- RADAR / SHOTS FIRED (Right) ---")
    print("   0 1 2 3 4 5 6 7 8 9            0 1 2 3 4 5 6 7 8 9")
    for y in range(game.myTable.size):
        my_row = " ".join(game.myTable.grid[x][y] for x in range(game.myTable.size))
        radar_row = " ".join(game.enemyTable.grid[x][y] for x in range(game.enemyTable.size))
        print(f"{y}  {my_row}        {y}  {radar_row}")
    print("----------------------------------------------------------------")


def process_network_inbox(game: Game, net: NetworkManager) -> None:
    """Drains and processes all queued network messages."""
    msg = net.get_message()
    while msg:
        mtype = msg.get("type")
        if mtype == "READY":
            print("\n[!] Opponent is READY!")
            game.opponent_ready_received()

        elif mtype == "FIRE":
            tx, ty = msg["x"], msg["y"]
            res = game.handle_incoming_shot(tx, ty)
            print(f"\n[!] Opponent fired at ({tx}, {ty}) -> {res['status']}")
            if res.get("sunk"):
                print(f"[!] Opponent SUNK your {res['sunk']}!")

            net.send_message({
                "type": "RESULT",
                "x": tx,
                "y": ty,
                "status": res["status"],
                "sunk": res["sunk"],
                "game_over": res["game_over"]
            })

        elif mtype == "RESULT":
            rx, ry = msg["x"], msg["y"]
            status = msg["status"]
            sunk = msg["sunk"]
            is_over = msg["game_over"]

            game.record_shot_result(rx, ry, status, sunk, is_over)
            print(f"\n[!] Shot at ({rx}, {ry}) resulted in: {status}")
            if sunk:
                print(f"[!] You SUNK their {sunk}!")

        msg = net.get_message()


def main():
    print("=== NAVAL BATTLE CLI ===")
    role = input("Host or Join? (h/j): ").strip().lower()
    is_host = (role == "h")

    net = NetworkManager()
    game = Game(isHost=is_host)

    if is_host:
        print("[*] Starting host on port 55555... waiting for opponent...")
        net.start_host(port=55555)
        while not net.isConnected:
            time.sleep(0.2)
        print("[+] Player connected!")
    else:
        host_ip = input("Enter Host IP (leave blank for 127.0.0.1): ").strip()
        if not host_ip:
            host_ip = "127.0.0.1"
        print(f"[*] Connecting to {host_ip}:55555...")
        net.connect_to_host(host_ip, port=55555)
        while not net.isConnected:
            time.sleep(0.2)
        print("[+] Connected to host!")

    # 1. Setup phase: auto-place ships and notify opponent
    auto_place_fleet(game)
    game.player_ready()
    net.send_message({"type": "READY"})
    print("[*] Fleet auto-placed and READY signal sent.")

    # 2. Wait for both peers to be ready
    while game.phase in (GamePhase.WAITING_READY, GamePhase.SETUP):
        process_network_inbox(game, net)
        time.sleep(0.1)

    print("\n[+] BATTLE COMMENCED!")

    # 3. Game loop
    try:
        while game.phase != GamePhase.GAME_OVER:
            process_network_inbox(game, net)

            if game.phase == GamePhase.MY_TURN:
                print_boards(game)
                valid_input = False
                while not valid_input:
                    try:
                        raw = input("Enter target 'x y' (e.g., 3 4) or 'q' to quit: ").strip()
                        if raw.lower() == "q":
                            net.close()
                            return

                        coords = raw.split()
                        if len(coords) != 2:
                            print("Please provide exactly two numbers separated by a space.")
                            continue

                        tx, ty = int(coords[0]), int(coords[1])
                        target = game.fire(tx, ty)
                        if target:
                            net.send_message({"type": "FIRE", "x": tx, "y": ty})
                            valid_input = True
                        else:
                            print("Invalid coordinates or tile already targeted! Try again.")
                    except ValueError:
                        print("Invalid input format. Numbers only.")

            elif game.phase == GamePhase.OPPONENT_TURN:
                print("\rWaiting for opponent move...", end="", flush=True)
                time.sleep(0.2)

        # 4. End screen
        print_boards(game)
        if game.winner == "ME":
            print("\n🎉 VICTORY! You completely destroyed the enemy fleet! 🎉")
        else:
            print("\n💀 DEFEAT! All your ships were sunk. 💀")

    finally:
        net.close()
        print("\nSession closed.")


if __name__ == "__main__":
    main()
