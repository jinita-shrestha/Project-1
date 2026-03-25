# Minmax and alphabeta code for Nine Men's Morris AI search

from typing import List, Optional
from game import (
    Piece, NEIGHBORS, MILLS_FOR_POSITION,
    close_mill, count_pieces, opponent
)

# Board util function

def swap_colors(board: List[Piece]) -> List[Piece]:
    """Swap the colors of the pieces on the board."""
    return [Piece.WHITE if piece == Piece.BLACK else Piece.BLACK if piece == Piece.WHITE else Piece.EMPTY for piece in board]


# Move generators 

def generate_remove(board: List[Piece], target: Piece, moves: List[List[Piece]]):
    """Add moves possible by removing a piece to the list of moves."""
    removed = False
    for i in range(len(board)):
        if board[i] == target and not close_mill(i, board):
            new_board = board.copy()
            new_board[i] = Piece.EMPTY
            moves.append(new_board)
            removed = True
    if not removed:
        for i in range(len(board)):
            if board[i] == target:
                new_board = board.copy()
                new_board[i] = Piece.EMPTY
                moves.append(new_board)
    

def generate_move(board: List[Piece], player: Piece, phase: str) -> List[List[Piece]]:
    """Generate all possible moves for the current board and phase."""
    rival = opponent(player)
    moves = []
    if phase == 'opening':
        for i in range(len(board)):
            if board[i] != Piece.EMPTY:
                continue
            new_board = board.copy()
            new_board[i] = player
            if close_mill(i, new_board):
                generate_remove(new_board, rival, moves)
            else:
                moves.append(new_board)
    else:
        dest = NEIGHBORS if phase == 'midgame' else None
        for i in range(len(board)):
            if board[i] != player:
                continue
            targets = dest[i] if dest else range(len(board))
            for j in targets:
                if board[j] != Piece.EMPTY:
                    continue
                new_board = board.copy()
                new_board[i] = Piece.EMPTY
                new_board[j] = player
                if close_mill(j, new_board):
                    generate_remove(new_board, rival, moves)
                else:
                    moves.append(new_board)
    return moves

def is_opening(board: List[Piece]) -> bool:
    """Check if the board is in the opening phase."""
    return count_pieces(Piece.WHITE, board) < 9 or count_pieces(Piece.BLACK, board) < 9        

def get_phase(board: List[Piece], player: Piece) -> str:
    """Determine the phase of the game based on the board state."""
    return 'endgame' if count_pieces(player, board) ==3 else 'opening' if count_pieces(player, board) < 9 else 'midgame'

def generate_white(board: List[Piece]) -> List[List[Piece]]:
    """Generate all possible opening/midgame/endgame moves for white."""
    return generate_move(board, Piece.WHITE, get_phase(board, Piece.WHITE))

def generate_black(board: List[Piece]) -> List[List[Piece]]:
    """Generate all possible opening/midgame/endgame moves for black."""
    return generate_move(board, Piece.BLACK, get_phase(board, Piece.BLACK))

def validate_turn(board: List[Piece], player: Piece) -> tuple:
    """Validate if it's the correct player's turn based on the board state."""
    white_count = count_pieces(Piece.WHITE, board)
    black_count = count_pieces(Piece.BLACK, board)
    if white_count == 0 and black_count == 0:
        if player == Piece.BLACK:
            return False, "Empty board, white goes first"
        return True, ""
    
    if is_opening(board):
        if white_count == black_count:
            if player == Piece.BLACK:
                return False, f"Invalid board state: {white_count} white pieces and {black_count} black pieces, expected white to move"
        elif white_count > black_count:
            if player == Piece.WHITE:
                return False, f"Invalid board state: {white_count} white pieces and {black_count} black pieces, expected black to move"
        else:
            if player == Piece.BLACK:
                return False, f"Invalid board state: {white_count} white pieces and {black_count} black pieces, expected white to move"
    return True, ""

# Static Est Part 1

def static_estimation_open(board: List[Piece]) -> int:
    """Static estimation for the opening phase."""
    return count_pieces(Piece.WHITE, board) - count_pieces(Piece.BLACK, board)

def static_estimation_mid_end(board: List[Piece]) -> int:
    """Static estimation for the midgame/endgame phase."""
    white_count = count_pieces(Piece.WHITE, board)
    black_count = count_pieces(Piece.BLACK, board)
    black_moves = len(generate_black(board))
    if black_count <= 2:
        return 10000
    elif white_count <= 2:
        return -10000
    elif black_moves == 0:
        return 10000
    else:
        return 1000 * (white_count - black_count) - black_moves
    
# Search Result Class
class SearchResult:
    def __init__(self, estimate: int, board: Optional[List[Piece]], pos_evals: int):
        self.estimate = estimate
        self.board = board
        self.pos_evals = pos_evals

# repeat penalty constants
REPEAT_PENALTY_MAX = -9999
REPEAT_PENALTY_MIN = 9999

def board_key(board: List[Piece]) -> str:
    """Generate a unique key for the board state for use in the history dictionary."""
    return ''.join(str(piece.value) for piece in board)

# Minmax Algo Part 1

def minmax(board: List[Piece], depth: int, is_max: bool, move_gen_white, move_gen_black, static_est, history: dict = None) -> SearchResult:
    if history is None:
        history = {}
    
    if depth == 0:
        return SearchResult(static_est(board), board, 1)
    moves = move_gen_white(board) if is_max else move_gen_black(board)
    if not moves:
        return SearchResult(static_est(board), board, 1)
    
    total_evals = 0
    best_board = None
    if is_max:
        best_val = float('-inf')
        for child in moves:
            child_key = board_key(child)
            child_count = history.get(child_key, 0) + 1
 
            # Penalize repeated states — the mover loses
            if child_count >= 3:
                total_evals += 1
                if REPEAT_PENALTY_MAX > best_val:
                    best_val = REPEAT_PENALTY_MAX
                    best_board = child
                continue
 
            child_history = {**history, child_key: child_count}
            result = minmax(child, depth - 1, False,
                             move_gen_white, move_gen_black,
                             static_est, child_history)
            total_evals += result.pos_evals
            if result.estimate > best_val:
                best_val = result.estimate
                best_board = child
    else:
        best_val = float('inf')
        for child in moves:
            child_key = board_key(child)
            child_count = history.get(child_key, 0) + 1
 
            if child_count >= 3:
                total_evals += 1
                if REPEAT_PENALTY_MIN < best_val:
                    best_val = REPEAT_PENALTY_MIN
                    best_board = child
                continue
 
            child_history = {**history, child_key: child_count}
            result = minmax(child, depth - 1, True,
                             move_gen_white, move_gen_black,
                             static_est, child_history)
            total_evals += result.pos_evals
            if result.estimate < best_val:
                best_val = result.estimate
                best_board = child
    return SearchResult(best_val, best_board, total_evals)


# Alpha-beta Pruning Part 2

def alphabeta(board: List[Piece], depth: int, is_max: bool,
              alpha: float, beta: float,
              move_gen_white, move_gen_black,
              static_estimation,
              history: dict = None) -> SearchResult:

    if history is None:
        history = {}

    # Base case
    if depth == 0:
        return SearchResult(static_estimation(board), board, 1)

    moves = move_gen_white(board) if is_max else move_gen_black(board)
    if not moves:
        return SearchResult(static_estimation(board), board, 1)

    total_evals = 0
    best_board = None

    if is_max:
        best_value = float('-inf')
        for move in moves:
            child_key = board_key(move)
            child_count = history.get(child_key, 0) + 1

            if child_count >= 3:
                total_evals += 1
                if REPEAT_PENALTY_MAX > best_value:
                    best_value = REPEAT_PENALTY_MAX
                    best_board = move
                continue

            child_history = {**history, child_key: child_count}
            result = alphabeta(move, depth - 1, False,
                               alpha, beta,
                               move_gen_white, move_gen_black,
                               static_estimation, child_history)
            total_evals += result.pos_evals
            if result.estimate > best_value:
                best_value = result.estimate
                best_board = move
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        return SearchResult(best_value, best_board, total_evals)

    else:
        best_value = float('inf')
        for move in moves:
            child_key = board_key(move)
            child_count = history.get(child_key, 0) + 1

            if child_count >= 3:
                total_evals += 1
                if REPEAT_PENALTY_MIN < best_value:
                    best_value = REPEAT_PENALTY_MIN
                    best_board = move
                continue

            child_history = {**history, child_key: child_count}
            result = alphabeta(move, depth - 1, True,
                               alpha, beta,
                               move_gen_white, move_gen_black,
                               static_estimation, child_history)
            total_evals += result.pos_evals
            if result.estimate < best_value:
                best_value = result.estimate
                best_board = move
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return SearchResult(best_value, best_board, total_evals)

# part 4 improved static estimation

def static_estimation_opening_improved(board: List[Piece]) -> int:
    raise NotImplementedError("Part 4 Improved opening estimation not yet implemented")
 
 
def static_estimation_midgame_endgame_improved(board: List[Piece]) -> int:
    raise NotImplementedError("Part 4 Improved midgame/endgame estimation not yet implemented")