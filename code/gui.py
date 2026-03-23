## Pygame gui

import pygame
import sys
import math
from game import (
    Game, Piece, State, POSITIONS, NEIGHBORS, MILLS, count_pieces
)

# ─── COLORS ───
BG_COLOR       = (30, 30, 38)
BOARD_BG       = (45, 42, 52)
LINE_COLOR     = (120, 115, 130)
GRID_DOT       = (80, 75, 90)

WHITE_PIECE    = (240, 235, 220)
WHITE_OUTLINE  = (200, 195, 180)
BLACK_PIECE    = (35, 35, 45)
BLACK_OUTLINE  = (90, 85, 100)

HIGHLIGHT      = (100, 220, 180)
HIGHLIGHT_DIM  = (70, 180, 150)
SELECTED       = (255, 200, 80)
REMOVABLE      = (220, 70, 70)

TEXT_COLOR     = (220, 215, 210)
TEXT_DIM       = (140, 135, 145)
LABEL_COLOR    = (190, 185, 200)
ACCENT         = (100, 220, 180)
WARNING        = (220, 70, 70)

# ─── LAYOUT ───
WINDOW_W = 900
WINDOW_H = 850
BOARD_TOP = 90
BOARD_SIZE = 480
PIECE_RADIUS = 19
DOT_RADIUS = 6
INFO_Y = BOARD_TOP + BOARD_SIZE + 35

# Position-to-grid mapping: (column_letter, row_number)
# columns a-g = indices 0-6, rows 0-6
POS_GRID = {
    0:  ('a', 0),  1:  ('g', 0),
    2:  ('b', 1),  3:  ('f', 1),
    4:  ('c', 2),  5:  ('e', 2),
    6:  ('a', 3),  7:  ('b', 3),  8:  ('c', 3),
    9:  ('e', 3),  10: ('f', 3),  11: ('g', 3),
    12: ('c', 4),  13: ('d', 4),  14: ('e', 4),
    15: ('b', 5),  16: ('d', 5),  17: ('f', 5),
    18: ('a', 6),  19: ('d', 6),  20: ('g', 6),
}

# Pre-compute pixel coordinates at module level
_LEFT = (WINDOW_W - BOARD_SIZE) // 2
_TOP = BOARD_TOP
COL_X = {c: _LEFT + int(i * BOARD_SIZE / 6) for i, c in enumerate('abcdefg')}
ROW_Y = {r: _TOP + BOARD_SIZE - int(r * BOARD_SIZE / 6) for r in range(7)}

# Pre-compute board lines from adjacency
BOARD_LINES = list({
    (min(pos, n), max(pos, n))
    for pos, neighs in NEIGHBORS.items()
    for n in neighs
})


def get_pos_pixel(idx):
    """Get pixel (x, y) for a board position index."""
    col, row = POS_GRID[idx]
    return (COL_X[col], ROW_Y[row])


class GUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Nine Men's Morris - Variant E")
        self.clock = pygame.time.Clock()
        self.game = Game()
        self.hovered_pos = None

        # Fonts
        self.font_title = pygame.font.SysFont("Georgia", 28, bold=True)
        self.font_info = pygame.font.SysFont("Georgia", 18)
        self.font_small = pygame.font.SysFont("Consolas", 13)
        self.font_label = pygame.font.SysFont("Consolas", 11)
        self.font_msg = pygame.font.SysFont("Georgia", 20)
        self.font_btn = pygame.font.SysFont("Georgia", 16, bold=True)

        # Animation state
        self.anim_time = 0

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000
            self.anim_time += dt
            self._handle_events()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        self.hovered_pos = self._get_hovered_position()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.deselect_piece()
                elif event.key == pygame.K_r:
                    self.game.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self._reset_button_rect().collidepoint(event.pos):
                        self.game.reset()
                        return
                    pos = self._get_clicked_position(event.pos)
                    if pos is not None:
                        self.game.handle_click(pos)
                elif event.button == 3:  # Right click
                    self.game.deselect_piece()

    def _get_hovered_position(self):
        mx, my = pygame.mouse.get_pos()
        for i in range(21):
            px, py = get_pos_pixel(i)
            dist = math.hypot(mx - px, my - py)
            if dist <= PIECE_RADIUS + 8:
                return i
        return None

    def _get_clicked_position(self, mouse_pos):
        mx, my = mouse_pos
        for i in range(21):
            px, py = get_pos_pixel(i)
            dist = math.hypot(mx - px, my - py)
            if dist <= PIECE_RADIUS + 8:
                return i
        return None

    def _reset_button_rect(self):
        return pygame.Rect(WINDOW_W - 120, 15, 100, 36)

    # ─── Drawing ───

    def _draw(self):
        self.screen.fill(BG_COLOR)
        self._draw_header()
        self._draw_board()
        self._draw_pieces()
        self._draw_info_panel()
        self._draw_reset_button()

    def _draw_header(self):
        title = self.font_title.render("Nine Men's Morris", True, TEXT_COLOR)
        subtitle = self.font_small.render("VARIANT  E", True, TEXT_DIM)
        self.screen.blit(title, (30, 18))
        self.screen.blit(subtitle, (32, 52))

        # Current player indicator
        if self.game.state != State.GAME_OVER:
            color = WHITE_PIECE if self.game.current_player == Piece.WHITE else BLACK_PIECE
            outline = WHITE_OUTLINE if self.game.current_player == Piece.WHITE else BLACK_OUTLINE
            cx = WINDOW_W // 2 + 100
            cy = 33
            pygame.draw.circle(self.screen, outline, (cx, cy), 14)
            pygame.draw.circle(self.screen, color, (cx, cy), 12)
            label = "White" if self.game.current_player == Piece.WHITE else "Black"
            txt = self.font_info.render(f"{label}'s turn", True, TEXT_COLOR)
            self.screen.blit(txt, (cx + 22, cy - 10))

    def _draw_board(self):
        # Board background
        left = (WINDOW_W - BOARD_SIZE) // 2 - 30
        rect = pygame.Rect(left, BOARD_TOP - 25, BOARD_SIZE + 60, BOARD_SIZE + 50)
        pygame.draw.rect(self.screen, BOARD_BG, rect, border_radius=12)

        # Draw lines
        for (a, b) in BOARD_LINES:
            pa = get_pos_pixel(a)
            pb = get_pos_pixel(b)
            pygame.draw.line(self.screen, LINE_COLOR, pa, pb, 2)

        # Highlight mills
        for mill in MILLS:
            if all(self.game.board[p] != Piece.EMPTY for p in mill):
                color = self.game.board[mill[0]]
                if all(self.game.board[p] == color for p in mill):
                    points = [get_pos_pixel(p) for p in mill]
                    c = HIGHLIGHT_DIM if color == Piece.WHITE else (180, 80, 80)
                    for i in range(len(points) - 1):
                        pygame.draw.line(self.screen, c, points[i], points[i+1], 4)

        # Draw position dots for empty spots
        for i in range(21):
            if self.game.board[i] == Piece.EMPTY:
                px, py = get_pos_pixel(i)
                pygame.draw.circle(self.screen, GRID_DOT, (px, py), DOT_RADIUS)

        # Draw valid action highlights
        valid = self.game.get_valid_actions()
        pulse = 0.5 + 0.5 * math.sin(self.anim_time * 3)

        for pos in valid:
            px, py = get_pos_pixel(pos)

            if self.game.state == State.REMOVING:
                alpha = int(40 + 30 * pulse)
                surf = pygame.Surface((PIECE_RADIUS * 2 + 16, PIECE_RADIUS * 2 + 16), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*REMOVABLE, alpha),
                                   (PIECE_RADIUS + 8, PIECE_RADIUS + 8), PIECE_RADIUS + 6)
                self.screen.blit(surf, (px - PIECE_RADIUS - 8, py - PIECE_RADIUS - 8))
            elif self.game.state == State.PLACING:
                alpha = int(100 + 80 * pulse)
                surf = pygame.Surface((DOT_RADIUS * 4 + 4, DOT_RADIUS * 4 + 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*HIGHLIGHT, alpha),
                                   (DOT_RADIUS * 2 + 2, DOT_RADIUS * 2 + 2), DOT_RADIUS * 2)
                self.screen.blit(surf, (px - DOT_RADIUS * 2 - 2, py - DOT_RADIUS * 2 - 2))
            elif self.game.state == State.SELECTING_TARGET:
                alpha = int(120 + 80 * pulse)
                surf = pygame.Surface((PIECE_RADIUS * 2 + 8, PIECE_RADIUS * 2 + 8), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*HIGHLIGHT, alpha),
                                   (PIECE_RADIUS + 4, PIECE_RADIUS + 4), PIECE_RADIUS - 2)
                self.screen.blit(surf, (px - PIECE_RADIUS - 4, py - PIECE_RADIUS - 4))

        # Draw selected piece highlight
        if self.game.selected_piece is not None:
            px, py = get_pos_pixel(self.game.selected_piece)
            pygame.draw.circle(self.screen, SELECTED, (px, py), PIECE_RADIUS + 5, 3)

        # Position labels
        for i in range(21):
            px, py = get_pos_pixel(i)
            label = self.font_label.render(POSITIONS[i], True, LABEL_COLOR)
            lx = px - label.get_width() // 2
            ly = py + PIECE_RADIUS + 6
            # Dark backing for readability over lines
            pad = 2
            bg = pygame.Surface((label.get_width() + pad * 2, label.get_height() + pad), pygame.SRCALPHA)
            bg.fill((*BOARD_BG, 200))
            self.screen.blit(bg, (lx - pad, ly))
            self.screen.blit(label, (lx, ly))

    def _draw_pieces(self):
        for i in range(21):
            if self.game.board[i] == Piece.EMPTY:
                continue
            px, py = get_pos_pixel(i)
            is_white = self.game.board[i] == Piece.WHITE

            # Shadow
            shadow_surf = pygame.Surface((PIECE_RADIUS * 2 + 10, PIECE_RADIUS * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 50),
                               (PIECE_RADIUS + 5, PIECE_RADIUS + 7), PIECE_RADIUS)
            self.screen.blit(shadow_surf, (px - PIECE_RADIUS - 5, py - PIECE_RADIUS - 5))

            # Main piece
            color = WHITE_PIECE if is_white else BLACK_PIECE
            outline = WHITE_OUTLINE if is_white else BLACK_OUTLINE
            pygame.draw.circle(self.screen, outline, (px, py), PIECE_RADIUS + 1)
            pygame.draw.circle(self.screen, color, (px, py), PIECE_RADIUS)

            # Inner shine
            shine_surf = pygame.Surface((PIECE_RADIUS * 2, PIECE_RADIUS * 2), pygame.SRCALPHA)
            if is_white:
                pygame.draw.circle(shine_surf, (255, 255, 255, 60),
                                   (PIECE_RADIUS - 4, PIECE_RADIUS - 4), PIECE_RADIUS // 2)
            else:
                pygame.draw.circle(shine_surf, (100, 100, 120, 40),
                                   (PIECE_RADIUS - 4, PIECE_RADIUS - 4), PIECE_RADIUS // 2)
            self.screen.blit(shine_surf, (px - PIECE_RADIUS, py - PIECE_RADIUS))

            # Hover effect
            if i == self.hovered_pos:
                hover_surf = pygame.Surface((PIECE_RADIUS * 2 + 16, PIECE_RADIUS * 2 + 16), pygame.SRCALPHA)
                pygame.draw.circle(hover_surf, (255, 255, 255, 30),
                                   (PIECE_RADIUS + 8, PIECE_RADIUS + 8), PIECE_RADIUS + 6)
                self.screen.blit(hover_surf, (px - PIECE_RADIUS - 8, py - PIECE_RADIUS - 8))

        # Hover ghost on empty spots
        if self.hovered_pos is not None and self.game.board[self.hovered_pos] == Piece.EMPTY:
            valid = self.game.get_valid_actions()
            if self.hovered_pos in valid:
                px, py = get_pos_pixel(self.hovered_pos)
                color = WHITE_PIECE if self.game.current_player == Piece.WHITE else BLACK_PIECE
                ghost_surf = pygame.Surface((PIECE_RADIUS * 2 + 4, PIECE_RADIUS * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ghost_surf, (*color[:3], 80),
                                   (PIECE_RADIUS + 2, PIECE_RADIUS + 2), PIECE_RADIUS)
                self.screen.blit(ghost_surf, (px - PIECE_RADIUS - 2, py - PIECE_RADIUS - 2))

    def _draw_info_panel(self):
        y = INFO_Y

        # Message
        if self.game.state == State.GAME_OVER:
            color = ACCENT if self.game.winner == Piece.WHITE else WARNING
            msg = self.font_msg.render(self.game.message, True, color)
        elif self.game.state == State.REMOVING:
            msg = self.font_msg.render(self.game.message, True, WARNING)
        else:
            msg = self.font_msg.render(self.game.message, True, TEXT_COLOR)
        self.screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, y))
        y += 36

        # Piece counts
        w_count = count_pieces(Piece.WHITE, self.game.board)
        b_count = count_pieces(Piece.BLACK, self.game.board)
        w_remaining = 9 - self.game.white_placed
        b_remaining = 9 - self.game.black_placed

        info_left = f"White: {w_count} on board"
        if self.game.is_opening and w_remaining > 0:
            info_left += f"  ({w_remaining} to place)"
        info_right = f"Black: {b_count} on board"
        if self.game.is_opening and b_remaining > 0:
            info_right += f"  ({b_remaining} to place)"

        # White info
        pygame.draw.circle(self.screen, WHITE_PIECE, (80, y + 8), 8)
        pygame.draw.circle(self.screen, WHITE_OUTLINE, (80, y + 8), 8, 1)
        txt = self.font_info.render(info_left, True, TEXT_DIM)
        self.screen.blit(txt, (95, y))

        # Black info
        pygame.draw.circle(self.screen, BLACK_PIECE, (WINDOW_W - 350, y + 8), 8)
        pygame.draw.circle(self.screen, BLACK_OUTLINE, (WINDOW_W - 350, y + 8), 8, 1)
        txt = self.font_info.render(info_right, True, TEXT_DIM)
        self.screen.blit(txt, (WINDOW_W - 335, y))
        y += 30

        # Phase
        phase_name = "Opening" if self.game.is_opening else "Midgame"
        if not self.game.is_opening and (w_count == 3 or b_count == 3):
            phase_name = "Endgame"
        phase_txt = self.font_small.render(f"Phase: {phase_name}", True, TEXT_DIM)
        self.screen.blit(phase_txt, (WINDOW_W // 2 - phase_txt.get_width() // 2, y))
        y += 22

        # Board string
        board_str = ''.join(p.value for p in self.game.board)
        bs_txt = self.font_small.render(f"Board: {board_str}", True, TEXT_DIM)
        self.screen.blit(bs_txt, (WINDOW_W // 2 - bs_txt.get_width() // 2, y))

        # Controls hint (pinned to bottom)
        hint = "Left-click: act  |  Right-click/Esc: deselect  |  R: reset"
        hint_txt = self.font_small.render(hint, True, (80, 78, 90))
        self.screen.blit(hint_txt, (WINDOW_W // 2 - hint_txt.get_width() // 2, WINDOW_H - 28))

    def _draw_reset_button(self):
        rect = self._reset_button_rect()
        mx, my = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)

        color = HIGHLIGHT if hovered else TEXT_DIM
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=6)
        txt = self.font_btn.render("New Game", True, color)
        self.screen.blit(txt, (rect.x + rect.w // 2 - txt.get_width() // 2,
                               rect.y + rect.h // 2 - txt.get_height() // 2))


def main():
    gui = GUI()
    gui.run()


if __name__ == '__main__':
    main()