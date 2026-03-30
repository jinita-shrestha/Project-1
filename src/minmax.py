# Minmax and alphabeta code for Nine Men's Morris AI search

from typing import List, Optional
from game import (
    MILLS, Piece, NEIGHBORS, MILLS_FOR_POSITION,
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
    return count_pieces(Piece.WHITE, board) < 9 and count_pieces(Piece.BLACK, board) < 9        

def get_phase(board: List[Piece], player: Piece) -> str:
    rival = opponent(player)
    n = count_pieces(player, board)
    rival_n = count_pieces(rival, board)
    still_placing = n < 9 and rival_n < 9
    
    if still_placing:
        return 'opening'
    if n == 3:
        return 'endgame'
    return 'midgame'

def generate_white(board: List[Piece]) -> List[List[Piece]]:
    """Generate all possible opening/midgame/endgame moves for white."""
    if not is_opening(board) and count_pieces(Piece.WHITE, board) <= 2:
        return []
    return generate_move(board, Piece.WHITE, get_phase(board, Piece.WHITE))

def generate_black(board: List[Piece]) -> List[List[Piece]]:
    """Generate all possible opening/midgame/endgame moves for black."""
    if not is_opening(board) and count_pieces(Piece.BLACK, board) <= 2:
        return []
    return generate_move(board, Piece.BLACK, get_phase(board, Piece.BLACK))

def validate_turn(board: List[Piece], player: Piece) -> tuple:
    """Validate board state and ensure it's the correct player's turn."""
    if len(board) != 21:
        return False, f"Board must have exactly 21 positions got {len(board)}"

    white_count = count_pieces(Piece.WHITE, board)
    black_count = count_pieces(Piece.BLACK, board)

    if white_count > 9 or black_count > 9:
        return False, f"Too many pieces on the board: white={white_count}, black={black_count}"
    
    if white_count == 0 and black_count == 0:
        if player == Piece.BLACK:
            return False, "Empty board, white goes first"
        return True, ""
    
    if white_count == 0 and black_count > 0:
        return False, "Invalid board: Black pieces without any white pieces. White goes first."
    
    # validate edge cases that shouldnt be possible in a normal game but could be in an input file
    total = white_count + black_count
    if is_opening(board) and total <= 4 and white_count <= 2 and black_count <= 2:
        if white_count == black_count and player == Piece.BLACK:
            return False, "In the opening phase, white goes first and players alternate placing pieces."
        elif white_count == black_count + 1 and player == Piece.WHITE:
            return False, "In the opening phase, white goes first and players alternate placing pieces."
        elif black_count > white_count:
            return False, "Invalid board: Black has more pieces than white before mills are closed. White goes first."
    return True, ""

# Static Est Part 1

def static_estimation_open(board: List[Piece]) -> int:
    """Static estimation for the opening phase."""
    return count_pieces(Piece.WHITE, board) - count_pieces(Piece.BLACK, board)

def static_estimation_mid_end(board: List[Piece]) -> int:
    """Static estimation for the midgame/endgame phase."""
    white_count = count_pieces(Piece.WHITE, board)
    black_count = count_pieces(Piece.BLACK, board)
    black_moves = len(generate_move(board, Piece.BLACK, 'endgame' if count_pieces(Piece.BLACK, board) == 3 else 'midgame'))
    if black_count <= 2:
        return 10000
    elif white_count <= 2:
        return -10000
    elif black_moves == 0:
        return 10000
    else:
        return 1000 * (white_count - black_count) - black_moves
    
def static_estimation(board: List[Piece]) -> int:
    """General static estimation function that chooses the appropriate estimation based on the phase."""
    if is_opening(board):
        return static_estimation_open(board)
    else:
        return static_estimation_mid_end(board)

    
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

def minmax(board: List[Piece], depth: int, is_max: bool, move_gen_white, move_gen_black, static_est, history: dict = None, max_depth: int = None) -> SearchResult:
    if history is None:
        history = {}
    if max_depth is None:
        max_depth = depth
    
    if depth == 0:
        est = static_est(board)
        depth_taken = max_depth - depth
        if est >= 10000:
            est -= depth_taken
        elif est <= -10000:
            est += depth_taken
        return SearchResult(est, board, 1)
    
    moves = move_gen_white(board) if is_max else move_gen_black(board)
    if not moves:
        est = static_est(board)
        depth_taken = max_depth - depth
        if est >= 10000:
            est -= depth_taken
        elif est <= -10000:
            est += depth_taken
        return SearchResult(est, board, 1)
    
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
                             static_est, child_history, max_depth)
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
                             static_est, child_history, max_depth)
            total_evals += result.pos_evals
            if result.estimate < best_val:
                best_val = result.estimate
                best_board = child
    return SearchResult(best_val, best_board, total_evals)


# Alpha-beta Pruning Part 2

def alphabeta(board: List[Piece], depth: int, is_max: bool,
              alpha: float, beta: float,
              move_gen_white, move_gen_black,
              static_est,
              history: dict = None, max_depth: int = None) -> SearchResult:

    if history is None:
        history = {}
    if max_depth is None:
        max_depth = depth

    # Base case
    if depth == 0:
        est = static_est(board)
        depth_taken = max_depth - depth
        if est >= 10000:
            est -= depth_taken
        elif est <= -10000:
            est += depth_taken
        return SearchResult(est, board, 1)

    moves = move_gen_white(board) if is_max else move_gen_black(board)
    if not moves:
        est = static_est(board)
        depth_taken = max_depth - depth
        if est >= 10000:
            est -= depth_taken
        elif est <= -10000:
            est += depth_taken
        return SearchResult(est, board, 1)

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
                               static_est, child_history, max_depth)
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
                               static_est, child_history, max_depth)
            total_evals += result.pos_evals
            if result.estimate < best_value:
                best_value = result.estimate
                best_board = move
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return SearchResult(best_value, best_board, total_evals)

# part 4 improved static estimation
def count_potential_mills(board, player):
    count = 0
    for mill in MILLS:
        pieces = [board[p] for p in mill]
        if pieces.count(player) == 2 and pieces.count(Piece.EMPTY) == 1:
            count += 1
    return count

def static_estimation_opening_improved(board: List[Piece]) -> int:
    w = count_pieces(Piece.WHITE, board)
    b = count_pieces(Piece.BLACK, board)

    w_potential = count_potential_mills(board, Piece.WHITE)
    b_potential = count_potential_mills(board, Piece.BLACK)

    return (w - b) + (w_potential - b_potential)
 
def static_estimation_midgame_endgame_improved(board: List[Piece]) -> int:
    w = count_pieces(Piece.WHITE, board)
    b = count_pieces(Piece.BLACK, board)

    black_moves = len(generate_move(board, Piece.BLACK, 'endgame' if count_pieces(Piece.BLACK, board) == 3 else 'midgame'))

    w_potential = count_potential_mills(board, Piece.WHITE)
    b_potential = count_potential_mills(board, Piece.BLACK)

    if b <= 2:
        return 10000
    elif w <= 2:
        return -10000
    elif black_moves == 0:
        return 10000

    return 1000 * (w - b) - black_moves + 5 * (w_potential - b_potential)

def static_estimation_improved(board: List[Piece]) -> int:
    if is_opening(board):
        return static_estimation_opening_improved(board)
    else:
        return static_estimation_midgame_endgame_improved(board)