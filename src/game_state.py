from enum import Enum, auto
from table import Table, FLEET_CONFIG
from radarTable import RadarTable
from typing import Optional, Tuple

class GamePhase(Enum):
    SETUP = auto()
    WAITING_READY = auto()
    MY_TURN = auto()
    WAITING_FOR_RESULT = auto()
    OPPONENT_TURN = auto()
    GAME_OVER = auto()

class Game():
    def __init__(self, isHost: bool = False) -> None:
        self.myTable = Table()
        self.enemyTable = RadarTable()
        self.isHost = isHost
        self.phase = GamePhase.SETUP
        self.myReady = False
        self.opponentReady = False
        self.winner : Optional[str] = None

    def player_ready(self) -> bool:
        if self.phase != GamePhase.SETUP:
            return False

        if len(self.myTable.ships) != len(FLEET_CONFIG):
            return False

        self.myTable.cleanup_buffers()
        self.myReady = True

        if self.opponentReady:
            self._start_battle()
        else:
            self.phase = GamePhase.WAITING_READY

        return True

    def opponent_ready_received(self) -> None:
        self.opponentReady = True
        if self.myReady:
            self._start_battle()

    def _start_battle(self) -> None:
        if self.isHost:
            self.phase = GamePhase.MY_TURN
        else:
            self.phase = GamePhase.OPPONENT_TURN

    def fire(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        if self.phase != GamePhase.MY_TURN:
            return None

        if not self.enemyTable.can_fire_at(x, y):
            return None

        self.phase = GamePhase.WAITING_FOR_RESULT
        return (x, y)

    def record_shot_result(
        self,
        x: int,
        y: int,
        status: str,
        sunk_ship: Optional[str] = None,
        game_over: bool = False
    ) -> None:
        self.enemyTable.record_result(x, y, status, sunk_ship)

        if game_over:
            self.phase = GamePhase.GAME_OVER
            self.winner = "ME"
        elif status == "ALREADY_SHOT" or status == "INVALID":
            self.phase = GamePhase.MY_TURN
        else:
            self.phase = GamePhase.OPPONENT_TURN

    def handle_incoming_shot(self, x: int, y: int) -> dict:
        if self.phase != GamePhase.OPPONENT_TURN:
            return {"valid": False, "status": "INVALID_PHASE", "sunk": None, "game_over": False}

        result = self.myTable.receive_shot(x, y)

        if not result["valid"]:
            return result

        if result["game_over"]:
            self.phase = GamePhase.GAME_OVER
            self.winner = "OPPONENT"
        else:
            self.phase = GamePhase.MY_TURN

        return result
