import sys
import pygame

import sys
import pygame

# Board tile definitions matching your model
EMPTY = 'E'
SHIP = 'S'
HIT = 'H'
MISS = 'M'
RESTRICT = 'R'

# UI Constants
CELL_SIZE = 36
MARGIN = 2
BOARD_SIZE = 10
BOARD_PIXEL_SPAN = BOARD_SIZE * (CELL_SIZE + MARGIN)

# Window layout
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 560
MY_BOARD_ORIGIN = (50, 80)
RADAR_BOARD_ORIGIN = (490, 80)

# Palette
COLOR_BG = (24, 28, 36)
COLOR_TEXT = (220, 220, 230)
COLOR_WATER = (45, 85, 125)
COLOR_SHIP = (110, 120, 135)
COLOR_RESTRICT = (60, 45, 55)
COLOR_HIT = (210, 50, 45)
COLOR_MISS = (200, 210, 225)
COLOR_GRID_BORDER = (15, 20, 25)

COLOR_MAP = {
    EMPTY: COLOR_WATER,
    SHIP: COLOR_SHIP,
    RESTRICT: COLOR_RESTRICT,
    HIT: COLOR_HIT,
    MISS: COLOR_MISS,
}


def get_grid_coordinates(mouse_pos, board_origin):
    """
    Translates screen (mx, my) to board (gx, gy).
    Returns (gx, gy) if inside the 10x10 grid, otherwise None.
    """
    mx, my = mouse_pos
    ox, oy = board_origin

    # Check outer bounding box
    if not (ox <= mx < ox + BOARD_PIXEL_SPAN and oy <= my < oy + BOARD_PIXEL_SPAN):
        return None

    gx = (mx - ox) // (CELL_SIZE + MARGIN)
    gy = (my - oy) // (CELL_SIZE + MARGIN)

    if 0 <= gx < BOARD_SIZE and 0 <= gy < BOARD_SIZE:
        return int(gx), int(gy)
    return None


def draw_board(surface, grid, origin, title, font):
    """Renders a 10x10 matrix onto the Pygame surface."""
    ox, oy = origin

    # Title label
    label = font.render(title, True, COLOR_TEXT)
    surface.blit(label, (ox, oy - 35))

    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            px = ox + x * (CELL_SIZE + MARGIN)
            py = oy + y * (CELL_SIZE + MARGIN)

            tile_state = grid[x][y]
            cell_color = COLOR_MAP.get(tile_state, COLOR_WATER)

            # Draw cell background
            rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, cell_color, rect)
            pygame.draw.rect(surface, COLOR_GRID_BORDER, rect, 1)


def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Naval Battle - P2P")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20, bold=True)

    # Dummy boards for testing rendering
    my_grid = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    radar_grid = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    # Mock ship & shot markers
    my_grid[1][1] = SHIP
    my_grid[2][1] = SHIP
    my_grid[3][1] = HIT
    radar_grid[4][4] = MISS
    radar_grid[7][2] = HIT

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                # Check click on radar (offensive target board)
                radar_cell = get_grid_coordinates(mouse_pos, RADAR_BOARD_ORIGIN)
                if radar_cell:
                    gx, gy = radar_cell
                    print(f"Fired at Radar grid -> x: {gx}, y: {gy}")

                # Check click on fleet (placement board)
                fleet_cell = get_grid_coordinates(mouse_pos, MY_BOARD_ORIGIN)
                if fleet_cell:
                    gx, gy = fleet_cell
                    print(f"Clicked Fleet grid -> x: {gx}, y: {gy}")

        # 2. Rendering
        screen.fill(COLOR_BG)
        draw_board(screen, my_grid, MY_BOARD_ORIGIN, "YOUR FLEET", font)
        draw_board(screen, radar_grid, RADAR_BOARD_ORIGIN, "RADAR / TARGET", font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
