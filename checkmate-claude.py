#!/usr/bin/env python3

from stockfish import Stockfish

import anthropic
import chess
import os

api_key = os.getenv('ANTHROPIC_KEY')
client = anthropic.Anthropic(api_key=api_key)

stockfish = Stockfish()
stockfish.set_elo_rating(1700)
board = chess.Board()

pgn = """[Event "FIDE World Championship Match 2024"]
[Site "Los Angeles, USA"]
[Date "2024.12.01"]
[Round "5"]
[White "Carlsen, Magnus"]
[Black "Nepomniachtchi, Ian"]
[Result "1-0"]
[WhiteElo "2885"]
[WhiteTitle "GM"]
[WhiteFideId "1503014"]
[BlackElo "2812"]
[BlackTitle "GM"]
[BlackFideId "4168119"]
[TimeControl "40/7200:20/3600:900+30"]
[UTCDate "2024.11.27"]
[UTCTime "09:01:25"]
[Variant "Standard"]

1."""

n = 1
move_count = 0
while True:
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=5,
        temperature=0,
        messages=[
            {"role": "user", "content": f"Given this chess game PGN, what's the next move for {('White' if board.turn else 'Black')}? Respond with only the move in SAN notation:\n\n{pgn}"},
            {"role": "assistant", "content": "Here's the next move:"},
        ]
    )
    # Extract the move from the response content
    move_text = response.content[0].text
    san_move = move_text.strip().split()[0]
    print(f"Claude's move: {san_move}")
    move_count += 1
    try:
        uci_move = board.push_san(san_move).uci()
    except (chess.InvalidMoveError, chess.IllegalMoveError) as e:
        print(f"Invalid or illegal move received: move {move_count} by Claude - {san_move}")
        print(f"###{move_count}###")
        print(f"Error: {e}")
        break

    pgn += f" {san_move}"

    stockfish.make_moves_from_current_position([f"{uci_move}"])
#    print("\033c" + stockfish.get_board_visual())

    if board.is_checkmate():
        print(pgn)
        print("Sonnet 3.5 won!")
        print(f"###{move_count}###")
        break

    if board.is_stalemate():
        print(pgn)
        print("Draw!")
        print(f"###{move_count}###")
        break

    uci_move = stockfish.get_best_move()
    move = chess.Move.from_uci(uci_move)
    san_move = board.san(move)
    print(f"Stockfish's move: {san_move}")
    board.push(move)
    pgn += f" {san_move}"

    stockfish.make_moves_from_current_position([f"{uci_move}"])

    if board.is_checkmate():
        print(pgn)
        print("Stockfish 1700 ELO won!")
        print(f"###{move_count}###")
        break

    if board.is_stalemate():
        print(pgn)
        print("Draw!")
        print(f"###{move_count}###")
        break

    n += 1
    pgn += f" {n}."
