#!/usr/bin/env python3

from stockfish import Stockfish
import openai
import chess
import os

# Set up OpenAI API
api_key = os.getenv('OPENAI_KEY')
client = openai.OpenAI(api_key = api_key)

# Set up Stockfish
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
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "user", "content": f"Given this chess game PGN, what's the next move for {('White' if board.turn else 'Black')}? Respond with only the move in SAN notation and never specify the move number:\n\n{pgn}"}
        ],
        temperature=0,
        max_tokens=5
    )

    san_move = response.choices[0].message.content.strip().split()[0]
    print(f"GPT's move: {san_move}")
    move_count += 1
    try:
        uci_move = board.push_san(san_move).uci()
    except (chess.InvalidMoveError, chess.IllegalMoveError) as e:
        print(f"Invalid or illegal move received: move {move_count} by GPT - {san_move}")
        print(f"###{move_count}###")
        print(f"Error: {e}")
        break
    pgn += f" {san_move}"

    stockfish.make_moves_from_current_position([f"{uci_move}"])

    if board.is_checkmate():
        print(pgn)
        print("GPT won!")
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

