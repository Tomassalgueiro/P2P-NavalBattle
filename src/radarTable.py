from typing import List,Optional
from table import EMPTY, HIT, MISS, TABLE_SIZE


class RadarTable:
    def __init__(self, size: int = TABLE_SIZE) -> None:
            self.size = TABLE_SIZE
            self.grid = [[EMPTY for _ in range(size)]for _ in range(size)]
            self.sunk_ships = []

    def can_fire_at(self, x: int, y: int) -> bool:
        if  x < 0 or x >= self.size or y < 0 or y >= self.size:
            return False
        return self.grid[x][y] == EMPTY 
    
    def record_result(self, x: int, y: int, status: str, sunk_ship: Optional[str] = None) -> None:
        if status in (MISS, "MISS"):
            self.grid[x][y] = MISS
        elif status in (HIT, "HIT"):
            self.grid[x][y] = HIT

        if sunk_ship:
            self.sunk_ships.append(sunk_ship)
