
### Game implementation logic
# Board positions : (21 total) 0-20
#  0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20
# a0  g0  b1  f1  c2  e2  a3  b3  c3  e3  f3  g3  c4  d4  e4  b5  d5  f5  a6  d6  g6
#
# Board layout (Variant-E):
#
#     Columns:  A    B    C    D     E     F      G
#     Row 7:  18(a6) --------- 19(d6) --------- 20(g6)
#              |                 |                 |
#     Row 6:   |    15(b5) --- 16(d5) --- 17(f5)   |
#              |     |                       |     |
#     Row 5:   |     |  12(c4)-13(d4)-14(e4) |     |
#              |     |   |               |   |     |
#     Row 4:  6(a3)-7(b3)-8(c3)      9(e3)-10(f3)-11(g3)
#              |     |   |               |   |     |
#     Row 3:   |     |   4(c2) ----  5(e2)   |     |
#              |     |                       |     |
#     Row 2:   |     2(b1) -------------  3(f1)    |
#              |                                   |
#     Row 1:   0(a0) -------------------------  1(g0)
###

from enum import Enum
from typing import List, Tuple, Optional
import copy

class Piece(Enum):
    EMPTY = 'x'
    WHITE = 'W'
    BLACK = 'B'

class Phase(Enum):
    OPENING = 'opening'
    MIDGAME = 'midgame'
    ENDGAME_WHITE = 'endgame_white'
    ENDGAME_BLACK = 'endgame_black'

class State(Enum):
    PLACING = 'placing'           # Opening: placing pieces
    MOVING = 'moving'             # Midgame/Endgame: selecting piece to move
    SELECTING_TARGET = 'selecting_target'  # Chose a piece, now pick destination
    REMOVING = 'removing'         # Formed a mill, must remove opponent piece
    GAME_OVER = 'game_over'

def opponent(player: Piece) -> Piece:
    return Piece.BLACK if player == Piece.WHITE else Piece.WHITE

def player_name(player: Piece) -> str:
    return "White" if player == Piece.WHITE else "Black"

# -- Board data --

# Neighbor positions for each position on the board
NEIGHBORS = {
    0:  [1, 2, 6],        # a0 -> g0, b1, a3
    1:  [0, 3, 11],       # g0 -> a0, f1, g3
    2:  [0, 4, 7],        # b1 -> a0, c2, b3
    3:  [1, 5, 10],       # f1 -> g0, e2, f3
    4:  [2, 5, 8],        # c2 -> b1, e2, c3
    5:  [3, 4, 9],        # e2 -> f1, c2, e3
    6:  [0, 7, 18],       # a3 -> a0, b3, a6
    7:  [2, 6, 8, 15],    # b3 -> b1, a3, c3, b5
    8:  [4, 7, 12],       # c3 -> c2, b3, c4
    9:  [5, 10, 14],      # e3 -> e2, f3, e4
    10: [3, 9, 11, 17],   # f3 -> f1, e3, g3, f5
    11: [1, 10, 20],      # g3 -> g0, f3, g6
    12: [8, 13],          # c4 -> c3, d4
    13: [12, 14, 16, 19], # d4 -> c4, e4, d5, d6
    14: [9, 13],          # e4 -> e3, d4
    15: [7, 16],          # b5 -> b3, d5
    16: [13, 15, 17, 19], # d5 -> d4, b5, f5, d6
    17: [10, 16],         # f5 -> f3, d5
    18: [6, 19],          # a6 -> a3, d6
    19: [13, 16, 18, 20], # d6 -> d4, d5, a6, g6
    20: [11, 19],         # g6 -> g3, d6
}

# Winning combinations (mills) 
MILLS = [
    (0, 2, 4),    # a0-b1-c2  (bottom-left diagonal)
    (1, 3, 5),    # g0-f1-e2  (bottom-right diagonal)
    (6, 7, 8),    # a3-b3-c3  (row 3 left)
    (9, 10, 11),  # e3-f3-g3  (row 3 right)
    (12, 13, 14), # c4-d4-e4  (row 4)
    (15, 16, 17), # b5-d5-f5  (row 5)
    (18, 19, 20), # a6-d6-g6  (row 6 / top)
    (0, 6, 18),   # a0-a3-a6  (left column)
    (2, 7, 15),   # b1-b3-b5  (b column)
    (4, 8, 12),   # c2-c3-c4  (c column)
    (13, 16, 19), # d4-d5-d6  (d column)
    (5, 9, 14),   # e2-e3-e4  (e column)
    (3, 10, 17),  # f1-f3-f5  (f column)
    (1, 11, 20),  # g0-g3-g6  (g column)
]

POSITIONS = {
    0: 'a0', 1: 'g0', 2: 'b1', 3: 'f1', 4: 'c2', 5: 'e2', 6: 'a3', 7: 'b3', 8: 'c3', 
    9: 'e3', 10: 'f3', 11: 'g3', 12: 'c4', 13: 'd4', 14: 'e4', 15: 'b5', 16: 'd5',
    17: 'f5', 18: 'a6', 19: 'd6', 20: 'g6'
}

MILLS_FOR_POSITION = {pos: [mill for mill in MILLS if pos in mill] for pos in range(21)}

# -- Board util functions --

def close_mill(pos: int, board: List[Piece]) -> bool:
    """Check if placing/moving a piece at pos creates a mill."""
    piece = board[pos]
    if piece == Piece.EMPTY:
        return False
    return any(all(board[p] == piece for p in mill) for mill in MILLS_FOR_POSITION[pos])


def get_mills(pos: int, board: List[Piece]) -> List[Tuple[int, int, int]]:
    """Return all mills that include the given position."""
    piece = board[pos]
    if piece == Piece.EMPTY:
        return []  
    return [mill for mill in MILLS if pos in mill and all(board[p] == piece for p in mill)]


def get_removable_pieces(opponent: Piece, board: List[Piece]) -> List[int]:
    """Return a list of positions of the player's pieces that can be removed. (isolated pieces can be removed first)"""
    isolated_pieces = []
    in_mill = []
    for pos, piece in enumerate(board):
        if board[pos] == opponent:
            if close_mill(pos, board):
                in_mill.append(pos)
            else:
                isolated_pieces.append(pos)
    return isolated_pieces if isolated_pieces else in_mill


def count_pieces(player: Piece, board: List[Piece]) -> int:
    """Count the number of pieces a player has on the board."""
    return sum(1 for piece in board if piece == player)


def get_possible_moves(pos: int, board: List[Piece], can_hop: bool) -> List[int]:
    """Return a list of valid move positions for a piece at pos."""
    if can_hop:
        return [i for i, piece in enumerate(board) if piece == Piece.EMPTY]
    return [neighbor for neighbor in NEIGHBORS[pos] if board[neighbor] == Piece.EMPTY]


def board_to_string(board: List[Piece]) -> str:
    """Convert the board state to a string representation."""
    return ' '.join(POSITIONS[i] + ':' + piece.name[0] for i, piece in enumerate(board))


def string_to_board(s: str) -> List[Piece]:
    """Convert a string representation back to a board state."""
    mapping = {'x': Piece.EMPTY, 'W': Piece.WHITE, 'B': Piece.BLACK}
    return [mapping[p] for p in s.split()]


## Game controller and logic

class Game:
    def __init__(self):
        self.board: List[Piece] = [Piece.EMPTY] * 21
        self.current_player: Piece = Piece.WHITE
        self.state: State = State.PLACING
        self.white_placed: int = 0
        self.black_placed: int = 0
        self.selected_piece: Optional[int] = None
        self.winner: Optional[Piece] = None
        self.message: str = "White's turn: Place a piece."
        self.board_history: List[str] = []
 
    @property
    def is_opening(self) -> bool:
        return self.white_placed < 9 or self.black_placed < 9
 
    def can_hop(self, player: Piece) -> bool:
        return not self.is_opening and count_pieces(player, self.board) == 3
 
    def get_phase(self) -> Phase:
        if self.is_opening:
            return Phase.OPENING
        if self.can_hop(self.current_player):
            return Phase.ENDGAME
        return Phase.MIDGAME
 
    def get_valid_actions(self) -> List[int]:
        if self.state == State.PLACING:
            return [i for i in range(21) if self.board[i] == Piece.EMPTY]
 
        elif self.state == State.MOVING:
            hop = self.can_hop(self.current_player)
            return [
                i for i in range(21)
                if self.board[i] == self.current_player
                and get_possible_moves(i, self.board, hop)
            ]
 
        elif self.state == State.SELECTING_TARGET:
            return get_possible_moves(
                self.selected_piece, self.board,
                self.can_hop(self.current_player)
            )
 
        elif self.state == State.REMOVING:
            return get_removable_pieces(opponent(self.current_player), self.board)
 
        return []
 
    def handle_click(self, pos: int):
        """Handle a click on the board at the given position."""
        if self.state == State.GAME_OVER:
            return
        if pos not in self.get_valid_actions():
            return
 
        dispatch = {
            State.PLACING: self._place_piece,
            State.MOVING: self._select_piece,
            State.SELECTING_TARGET: self._move_piece,
            State.REMOVING: self._remove_piece,
        }
        handler = dispatch.get(self.state)
        if handler:
            handler(pos)
 
    def _place_piece(self, pos: int):
        self.board[pos] = self.current_player
        if self.current_player == Piece.WHITE:
            self.white_placed += 1
        else:
            self.black_placed += 1
        self._after_placement(pos)
 
    def _select_piece(self, pos: int):
        self.selected_piece = pos
        self.state = State.SELECTING_TARGET
        verb = "Hop" if self.can_hop(self.current_player) else "Move"
        name = player_name(self.current_player)
        self.message = f"{name}: {verb} piece from {POSITIONS[pos]}"
 
    def _move_piece(self, pos: int):
        self.board[self.selected_piece] = Piece.EMPTY
        self.board[pos] = self.current_player
        self.selected_piece = None
        self._after_placement(pos)
 
    def _remove_piece(self, pos: int):
        self.board[pos] = Piece.EMPTY
        self._end_turn()
 
    def _after_placement(self, pos: int):
        """Check for mill after placing/moving, then end turn."""
        if close_mill(pos, self.board):
            removable = get_removable_pieces(opponent(self.current_player), self.board)
            if removable:
                self.state = State.REMOVING
                name = player_name(self.current_player)
                self.message = f"{name} formed a mill! Remove an opponent piece."
                return
        self._end_turn()
 
    def _end_turn(self):
        self.board_history.append(board_to_string(self.board))
        self.current_player = opponent(self.current_player)
        name = player_name(self.current_player)
 
        # Check game-over (only after opening)
        if not self.is_opening:
            opp = opponent(self.current_player)
 
            if count_pieces(self.current_player, self.board) <= 2:
                self._declare_winner(opp, "opponent reduced to 2 pieces")
                return
 
            hop = self.can_hop(self.current_player)
            has_moves = any(
                get_possible_moves(i, self.board, hop)
                for i in range(21)
                if self.board[i] == self.current_player
            )
            if not has_moves:
                self._declare_winner(opp, "opponent has no moves")
                return
 
        # Set up next turn
        if self.is_opening:
            self.state = State.PLACING
            self.message = f"{name}'s turn: Place a piece."
        else:
            self.state = State.MOVING
            verb = "hop" if self.can_hop(self.current_player) else "move"
            self.message = f"{name}'s turn: Select a piece to {verb}."
 
    def _declare_winner(self, winner: Piece, reason: str):
        self.winner = winner
        self.state = State.GAME_OVER
        self.message = f"Game Over! {player_name(winner)} wins! ({reason})"
 
    def deselect_piece(self):
        if self.state == State.SELECTING_TARGET:
            self.selected_piece = None
            self.state = State.MOVING
            name = player_name(self.current_player)
            self.message = f"{name}'s turn: Select a piece to move."
 
    def reset(self):
        self.__init__()