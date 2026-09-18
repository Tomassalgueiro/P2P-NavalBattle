from typing import Dict, Set, Tuple

EMPTY = 'E'
SHIP= 'S'
HIT = 'H'
MISS = 'M'

TABLE_SIZE = 10

FLEET_CONFIG = {
        "Carrier": 5,
        "Battleship": 4,
        "Submarine": 3,
        "Cruiser": 3,
        "Destroyer": 2,
        }

class Table:
    def __init__(self, size: int = TABLE_SIZE) -> None:
            self.size = size
            self.grid = [[EMPTY for _ in range(size)]for _ in range(size)]
            self.ships: Dict[str, Set[Tuple[int, int]]] = {}


    def is_valid_coordinate(self, x: int, y: int) -> bool:
        if x > self.size - 1 or y > self.size - 1 or x < 0 or y < 0:
            return False
        return True
    
    # horizontal == 1 means that the ship is sideways
    # otherwise its upwards 
    # placement is always from up to down or left to right, never other way so checking is easier
    # on x + len < self.size, we could add length - 1 and size - 1 but the result will be the same
    def can_place_ship(self, length, x, y, horizontal) -> bool:

        if not self.is_valid_coordinate(x,y):
            return False

        if horizontal:
            if not self.is_valid_coordinate(x+length-1,y):
                return False
            # inside bounds, verify for presence of another ship
            if x + length - 1 < self.size:  
                for i in range(length):
                    if not self.is_valid_coordinate(x+i,y):
                        return False
                    if self.grid[x+i][y] != EMPTY:
                        return False
        else:
            if not self.is_valid_coordinate(x,y+length-1):
                return False
            # inside bounds, verify for presence of another ship
            if y + length - 1 < self.size: 
                for i in range(length):
                    if not self.is_valid_coordinate(x,y+i):
                        return False
                    if self.grid[x][y+i] != EMPTY:
                        return False
        return True

    def place_ship(self, name, x, y, horizontal) -> bool: 
        if name not in FLEET_CONFIG:
            raise ValueError("ship not in config") 

        length = FLEET_CONFIG[name]
         
        if not self.can_place_ship(length,x,y,horizontal):
            return False

        ship_coords: Set[Tuple[int,int]] = set()

        for i in range(length):
            cx = x + i if horizontal else x
            cy = y  if horizontal else y + i
            self.grid[cx][cy] = SHIP
            ship_coords.add((cx,cy))

        self.ships[name] = ship_coords
        return True

    def receive_shot(self, x: int, y: int) -> dict:
        
        if not self.is_valid_coordinate(x,y):
            return { "valid": False, "status": "INVALID", "sunk": None, "game_over": False}

        current = self.grid[x][y]

        if current in (HIT,MISS):
            return { "valid": False, "status": "ALREADY_SHOT", "sunk": None, "game_over": False}

        if current == EMPTY :
            self.grid[x][y] = MISS
            return { "valid": True, "status": "MISS", "sunk": None, "game_over": False}

        self.grid[x][y] = HIT
        sunk_ship_name = None

        for name,coord in self.ships.items():
            if (x,y) in coord:
                coord.remove((x,y))
                if len(coord) == 0:
                    sunk_ship_name = name

        return { "valid": True, "status": "HIT", "sunk": sunk_ship_name, "game_over": self.is_game_over() }


    def is_game_over(self) -> bool:
       return all(len(coords) == 0 for coords in self.ships.values()) 

    #for each line on the grid, print it
    def display(self, hide_ships = False) -> None:
        if hide_ships == True:
            for line in self.grid:
                for c in line:
                    if c == SHIP:
                        print(EMPTY, end='')
                    else:
                        print(c, end='')
        else:
            for line in self.grid:
                print(line)

table = Table()


# 1. Edge test: Carrier (len 5) at x=5 should succeed (occupies 5, 6, 7, 8, 9)
table.place_ship("Carrier", 5, 0, horizontal=True) 
table.place_ship("Battleship", 7, 0, horizontal=True)
table.place_ship("Destroyer", 0, 0, horizontal=False)

table.display()
