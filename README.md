# Project 1 - Nine Men's Morris - Variant E 

A Python implementation of the Nine Men's Morris board game (Variant E) with a graphical interface and AI players using MiniMax and Alpha-Beta pruning.
 
## Requirements
 
- Python 3.8+
- Pygame (`pip install pygame`)
 
## Quick Start
 
Run the interactive game:
 
```
python main.py
```
 
## How to Play
 
The game is played between two players — **White** and **Black** — on a board with 21 intersections. Each player has 9 pieces.
 
### Phases
 
**Opening** — Players alternate placing one piece at a time onto any empty intersection. White goes first.
 
**Midgame** — Once all 18 pieces are placed, players take turns sliding one of their pieces along a board line to an adjacent empty intersection.
 
**Endgame** — When a player is reduced to only 3 pieces, that player may "hop" a piece to *any* empty intersection (not just adjacent ones).
 
### Mills
 
A **mill** is formed when three of your pieces sit on the same line segment. Forming a mill lets you remove one of your opponent's pieces from the board. Only isolated pieces (those *not* part of a mill) can be removed — unless all opponent pieces are in mills, in which case any piece can be taken.
 
### Winning
 
You win by either reducing your opponent to 2 pieces or blocking them from making any move.
 
### Controls
 
| Action | Input |
|---|---|
| Place / move / remove a piece | Left-click |
| Cancel a selected piece | Right-click or Esc |
| New game | Press R or click "New Game" |
