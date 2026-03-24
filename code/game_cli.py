# cli code for running game from command line for AI search


import sys
from game import board_to_string, string_to_board, format_board, Piece
from minmax import (
    minmax, alphabeta, is_opening, validate_turn,
    generate_white, generate_black,
    static_estimation_open, static_estimation_mid_end,
    static_estimation_mid_end, static_estimation_open
)
# cli defs

COMMANDS = {

    # part 1 minmax
    'MiniMaxOpening': (
        'minimax', True,
        generate_white, generate_black,
        static_estimation_open, 'MINIMAX', True,
    ),
    'MiniMaxGame': (
        'minimax', True,
        generate_white, generate_black,
        static_estimation_mid_end, 'MINIMAX', False,
    ),
 
    # Part 2 alpha beta
    'ABOpening': (
        'alphabeta', True,
        generate_white, generate_black,
        static_estimation_open, 'AB', True,
    ),
    'ABGame': (
        'alphabeta', True,
        generate_white, generate_black,
        static_estimation_mid_end, 'AB', False,
    ),
 
    # Part 3 min max black
    'MiniMaxOpeningBlack': (
        'minimax', False,
        generate_white, generate_black,
        static_estimation_open, 'MINIMAX', True,
    ),
    'MiniMaxGameBlack': (
        'minimax', False,
        generate_white, generate_black,
        static_estimation_mid_end, 'MINIMAX', False,
    ),
 
    # Part 4 min max improved
    'MiniMaxOpeningImproved': (
        'minimax', True,
        generate_white, generate_black,
        static_estimation_open, 'MINIMAX', True,
    ),
    'MiniMaxGameImproved': (
        'minimax', True,
        generate_white, generate_black,
        static_estimation_mid_end, 'MINIMAX', False,
    ),

}

def run(command: str, input_file: str, output_file: str, depth: int):
    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(sorted(COMMANDS))}")
        sys.exit(1)
 
    search_type, is_max, gen_white, gen_black, estimation, label, req_open = COMMANDS[command]
 
    with open(input_file, 'r') as f:
        input_board = string_to_board(f.read())
 
    if req_open and not is_opening(input_board):
        print(f"Error: {command} requires an opening position.")
        print(f"Use MiniMaxGame or ABGame instead.")
        sys.exit(1)        

    player = Piece.WHITE if is_max else Piece.BLACK
    is_valid, error = validate_turn(input_board, player)
    if not is_valid:
        print(f"Error: {error}")
        sys.exit(1)

    if search_type == 'minimax':
        result = minmax(input_board, depth, is_max,
                         gen_white, gen_black, estimation)
    else:
        result = alphabeta(input_board, depth, is_max,
                           float('-inf'), float('inf'),
                           gen_white, gen_black, estimation)
 
    output_str = board_to_string(result.board)
    with open(output_file, 'w') as f:
        f.write(output_str)
 
    input_str = board_to_string(input_board)
    print(f"Input state: {input_str}")
    print(format_board(input_board))
    print()
    print(f"Output state: {output_str}")
    print(format_board(result.board))
    print()
    print(f"States evaluated by static estimation: {result.pos_evals}.")
    print(f"{label} estimate: {result.estimate}.")
 
 
def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print(__doc__.strip())
        sys.exit(0)
 
    if len(sys.argv) != 5:
        print(f"Usage: python morris_cli.py <command> <input_file> <output_file> <depth>")
        sys.exit(1)
 
    command = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    depth = int(sys.argv[4])
    run(command, input_file, output_file, depth)
 
 
if __name__ == '__main__':
    main()