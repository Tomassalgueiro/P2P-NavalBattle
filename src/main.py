import sys
import pygame
from game_state import Game, GamePhase
from network import NetworkManager
from table import EMPTY, SHIP, HIT, MISS, RESTRICT, TABLE_SIZE, FLEET_CONFIG

WINDOW_WIDTH = 980
WINDOW_HEIGHT = 640
CELL_SIZE = 36
MARGIN = 2
BOARD_SPAN = TABLE_SIZE * (CELL_SIZE + MARGIN)

MY_ORIGIN = (60, 140)
RADAR_ORIGIN = (540, 140)

COLOR_BG = (18, 22, 30)
COLOR_PANEL = (28, 34, 46)
COLOR_TEXT = (235, 240, 245)
COLOR_TEXT_DIM = (150, 160, 175)
COLOR_WATER = (35, 65, 95)
COLOR_SHIP = (105, 115, 130)
COLOR_RESTRICT = (50, 40, 50)
COLOR_HIT = (215, 50, 45)
COLOR_MISS = (200, 215, 230)
COLOR_GRID_BORDER = (15, 20, 28)
COLOR_VALID_GHOST = (40, 180, 80, 160)
COLOR_INVALID_GHOST = (220, 50, 50, 160)
COLOR_BUTTON = (45, 90, 140)
COLOR_BUTTON_HOVER = (60, 115, 175)

COLOR_MAP = {
    EMPTY: COLOR_WATER,
    SHIP: COLOR_SHIP,
    RESTRICT: COLOR_RESTRICT,
    HIT: COLOR_HIT,
    MISS: COLOR_MISS,
}


class BattleshipGUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Naval Battle - P2P")
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_mid = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)

        self.net = NetworkManager()
        self.game = None

        # Estados de UI: 'MENU', 'CONNECTING', 'PLAYING'
        self.ui_state = "MENU"
        self.host_ip_input = "127.0.0.1"
        self.input_active = False

        # Variáveis da Fase de Setup
        self.fleet_keys = list(FLEET_CONFIG.keys())
        self.current_ship_idx = 0
        self.placement_horizontal = True
        self.status_message = "Bem-vindo! Escolhe Host ou Join."

    def run(self):
        running = True
        while running:
            # 1. Processar Rede
            if self.game and self.net.isConnected:
                self.process_network()

            # 2. Processar Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)

            # 3. Desenhar Ecrã
            self.screen.fill(COLOR_BG)
            if self.ui_state == "MENU":
                self.draw_menu()
            elif self.ui_state == "CONNECTING":
                self.draw_connecting()
            elif self.ui_state == "PLAYING":
                self.draw_gameplay()

            pygame.display.flip()
            self.clock.tick(60)

        self.net.close()
        pygame.quit()
        sys.exit()

    # --- Tratamento de Rede ---
    def process_network(self):
        msg = self.net.get_message()
        while msg:
            mtype = msg.get("type")
            if mtype == "READY":
                self.game.opponent_ready_received()
                self.status_message = "O adversário está PRONTO!"

            elif mtype == "FIRE":
                tx, ty = msg["x"], msg["y"]
                res = self.game.handle_incoming_shot(tx, ty)
                self.net.send_message({
                    "type": "RESULT",
                    "x": tx,
                    "y": ty,
                    "status": res["status"],
                    "sunk": res["sunk"],
                    "game_over": res["game_over"]
                })
                if res.get("sunk"):
                    self.status_message = f"O adversário afundou o teu {res['sunk']}!"

            elif mtype == "RESULT":
                self.game.record_shot_result(
                    msg["x"], msg["y"], msg["status"], msg["sunk"], msg["game_over"]
                )
                if msg.get("sunk"):
                    self.status_message = f"AFUNDASTE o {msg['sunk']} inimigo!"
                else:
                    self.status_message = f"Tiro em ({msg['x']}, {msg['y']}): {msg['status']}!"

            msg = self.net.get_message()

    # --- Conversão de Coordenadas ---
    def screen_to_grid(self, mouse_pos, origin):
        mx, my = mouse_pos
        ox, oy = origin
        if not (ox <= mx < ox + BOARD_SPAN and oy <= my < oy + BOARD_SPAN):
            return None
        gx = (mx - ox) // (CELL_SIZE + MARGIN)
        gy = (my - oy) // (CELL_SIZE + MARGIN)
        if 0 <= gx < TABLE_SIZE and 0 <= gy < TABLE_SIZE:
            return int(gx), int(gy)
        return None

    # --- Gestão de Eventos ---
    def handle_event(self, event):
        if self.ui_state == "MENU":
            self.handle_menu_event(event)
        elif self.ui_state == "PLAYING":
            self.handle_gameplay_event(event)

    def handle_menu_event(self, event):
        host_btn = pygame.Rect(WINDOW_WIDTH // 2 - 160, 220, 320, 50)
        join_btn = pygame.Rect(WINDOW_WIDTH // 2 - 160, 350, 320, 50)
        input_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, 290, 320, 45)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if host_btn.collidepoint(event.pos):
                self.game = Game(isHost=True)
                self.net.start_host(port=55555)
                self.ui_state = "CONNECTING"
            elif join_btn.collidepoint(event.pos):
                self.game = Game(isHost=False)
                self.net.connect_to_host(self.host_ip_input.strip() or "127.0.0.1", port=55555)
                self.ui_state = "CONNECTING"
            elif input_rect.collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False

        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_BACKSPACE:
                self.host_ip_input = self.host_ip_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.input_active = False
            elif len(self.host_ip_input) < 18:
                self.host_ip_input += event.unicode

    def handle_gameplay_event(self, event):
        # 1. Fase de Setup
        if self.game.phase == GamePhase.SETUP:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.placement_horizontal = not self.placement_horizontal
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Botão direito
                self.placement_horizontal = not self.placement_horizontal

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.current_ship_idx < len(self.fleet_keys):
                    grid_pos = self.screen_to_grid(event.pos, MY_ORIGIN)
                    if grid_pos:
                        gx, gy = grid_pos
                        ship_name = self.fleet_keys[self.current_ship_idx]
                        success = self.game.myTable.place_ship(
                            ship_name, gx, gy, self.placement_horizontal
                        )
                        if success:
                            self.current_ship_idx += 1
                            if self.current_ship_idx == len(self.fleet_keys):
                                # Todos posicionados: finalizar e avisar peer
                                self.game.player_ready()
                                self.net.send_message({"type": "READY"})
                                self.status_message = "Pronto! À espera do adversário..."

        # 2. Fase de Batalha (O teu turno)
        elif self.game.phase == GamePhase.MY_TURN:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                grid_pos = self.screen_to_grid(event.pos, RADAR_ORIGIN)
                if grid_pos:
                    gx, gy = grid_pos
                    if self.game.fire(gx, gy):
                        self.net.send_message({"type": "FIRE", "x": gx, "y": gy})
                        self.status_message = f"Fogo disparado em ({gx}, {gy})!"

    # --- Renderização ---
    def draw_menu(self):
        title = self.font_large.render("NAVAL BATTLE P2P", True, COLOR_TEXT)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 120)))

        # Botão Host
        host_btn = pygame.Rect(WINDOW_WIDTH // 2 - 160, 220, 320, 50)
        h_col = COLOR_BUTTON_HOVER if host_btn.collidepoint(pygame.mouse.get_pos()) else COLOR_BUTTON
        pygame.draw.rect(self.screen, h_col, host_btn, border_radius=6)
        h_txt = self.font_mid.render("Criar Sala (Host)", True, COLOR_TEXT)
        self.screen.blit(h_txt, h_txt.get_rect(center=host_btn.center))

        # Input IP
        input_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, 290, 320, 45)
        border_col = (80, 160, 240) if self.input_active else (60, 70, 85)
        pygame.draw.rect(self.screen, COLOR_PANEL, input_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_col, input_rect, 2, border_radius=6)
        ip_txt = self.font_mid.render(f"IP: {self.host_ip_input}", True, COLOR_TEXT)
        self.screen.blit(ip_txt, (input_rect.x + 15, input_rect.y + 10))

        # Botão Join
        join_btn = pygame.Rect(WINDOW_WIDTH // 2 - 160, 350, 320, 50)
        j_col = COLOR_BUTTON_HOVER if join_btn.collidepoint(pygame.mouse.get_pos()) else COLOR_BUTTON
        pygame.draw.rect(self.screen, j_col, join_btn, border_radius=6)
        j_txt = self.font_mid.render("Juntar a Sala (Join)", True, COLOR_TEXT)
        self.screen.blit(j_txt, j_txt.get_rect(center=join_btn.center))

    def draw_connecting(self):
        if self.net.isConnected:
            self.ui_state = "PLAYING"
            self.status_message = "Conectado! Posiciona os teus navios."
            return

        txt = self.font_mid.render("A aguardar ligação do adversário...", True, COLOR_TEXT)
        self.screen.blit(txt, txt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))

    def draw_board(self, grid, origin, title):
        ox, oy = origin
        t_surf = self.font_mid.render(title, True, COLOR_TEXT)
        self.screen.blit(t_surf, (ox, oy - 35))

        for x in range(TABLE_SIZE):
            for y in range(TABLE_SIZE):
                px = ox + x * (CELL_SIZE + MARGIN)
                py = oy + y * (CELL_SIZE + MARGIN)
                val = grid[x][y]
                col = COLOR_MAP.get(val, COLOR_WATER)

                rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, col, rect)
                pygame.draw.rect(self.screen, COLOR_GRID_BORDER, rect, 1)

    def draw_placement_ghost(self):
        """Mostra o navio transparente onde o rato está a pairar."""
        if self.current_ship_idx >= len(self.fleet_keys):
            return

        ship_name = self.fleet_keys[self.current_ship_idx]
        length = FLEET_CONFIG[ship_name]
        grid_pos = self.screen_to_grid(pygame.mouse.get_pos(), MY_ORIGIN)

        if not grid_pos:
            return

        gx, gy = grid_pos
        is_valid = self.game.myTable.can_place_ship(length, gx, gy, self.placement_horizontal)
        ghost_color = COLOR_VALID_GHOST if is_valid else COLOR_INVALID_GHOST

        ghost_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        ghost_surf.fill(ghost_color)

        for i in range(length):
            cx = gx + i if self.placement_horizontal else gx
            cy = gy if self.placement_horizontal else gy + i
            if 0 <= cx < TABLE_SIZE and 0 <= cy < TABLE_SIZE:
                px = MY_ORIGIN[0] + cx * (CELL_SIZE + MARGIN)
                py = MY_ORIGIN[1] + cy * (CELL_SIZE + MARGIN)
                self.screen.blit(ghost_surf, (px, py))

    def draw_gameplay(self):
        # 1. Barra de Estado Superior
        phase_str = ""
        if self.game.phase == GamePhase.SETUP:
            ship = self.fleet_keys[self.current_ship_idx] if self.current_ship_idx < len(self.fleet_keys) else ""
            phase_str = f"COLOCAÇÃO: {ship} (R / Botão Dir. para Rodar)"
        elif self.game.phase == GamePhase.WAITING_READY:
            phase_str = "A aguardar que o adversário termine a colocação..."
        elif self.game.phase == GamePhase.MY_TURN:
            phase_str = "O TEU TURNO: Clica no Radar para disparar!"
        elif self.game.phase == GamePhase.OPPONENT_TURN:
            phase_str = "TURNO DO ADVERSÁRIO: A aguardar disparo..."
        elif self.game.phase == GamePhase.GAME_OVER:
            phase_str = "FIM DE JOGO!"

        status_lbl = self.font_mid.render(phase_str, True, (255, 205, 70))
        self.screen.blit(status_lbl, (60, 40))

        sub_lbl = self.font_small.render(self.status_message, True, COLOR_TEXT_DIM)
        self.screen.blit(sub_lbl, (60, 75))

        # 2. Desenhar os Dois Tabuleiros
        self.draw_board(self.game.myTable.grid, MY_ORIGIN, "A TUA FROTA")
        self.draw_board(self.game.enemyTable.grid, RADAR_ORIGIN, "RADAR (INIMIGO)")

        # 3. Fantasma de Posicionamento (se ainda estiver em setup)
        if self.game.phase == GamePhase.SETUP:
            self.draw_placement_ghost()

        # 4. Banner de Fim de Jogo
        if self.game.phase == GamePhase.GAME_OVER:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 15, 20, 190))
            self.screen.blit(overlay, (0, 0))

            if self.game.winner == "ME":
                win_text = self.font_large.render("VITÓRIA! DESTRUÍSTE A FROTA INIMIGA!", True, (70, 230, 110))
            else:
                win_text = self.font_large.render("DERROTA! TODOS OS TEUS NAVIOS FORAM AFUNDADOS!", True, (230, 60, 60))
            self.screen.blit(win_text, win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))


if __name__ == "__main__":
    app = BattleshipGUI()
    app.run()
