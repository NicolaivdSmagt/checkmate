#!/usr/bin/env python3

import boto3
import logging
from stockfish import Stockfish
import chess
import json

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Initialize Bedrock client
bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')  # Replace with your preferred region

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

def get_claude_move(pgn, color):
    #model_id = "mistral.mistral-7b-instruct-v0:2"
    model_id = "mistral.mixtral-8x7b-instruct-v0:1"
    
    prompt = f"You are a chess grandmaster. Given this chess game PGN, what's your next move for {color}? Respond with only the move in SAN notation, without the move number, move annotations, exclamation or question marks or any comments:\n\n{pgn}"
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"

    native_request = {
        "prompt": formatted_prompt,
        "max_tokens": 5,
        "temperature": 0,
    }

    request = json.dumps(native_request)

    try:
        response = bedrock_client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(response["body"].read())
        
        move_text = model_response["outputs"][0]["text"]
        san_move = move_text.strip().split()[0]
        
        # Log token usage if available
        if "usage" in model_response:
            token_usage = model_response["usage"]
            #logger.info(f"Input tokens: {token_usage.get('input_tokens', 'N/A')}")
            #logger.info(f"Output tokens: {token_usage.get('output_tokens', 'N/A')}")
            #logger.info(f"Total tokens: {token_usage.get('total_tokens', 'N/A')}")
        
        return san_move
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return None
    
def main():
    global pgn
    n = 1
    move_count = 0
    
    while True:
        san_move = get_claude_move(pgn, 'White' if board.turn else 'Black')
        if san_move is None:
            print("Failed to get a move from LLM. Ending the game.")
            break

        print(f"LLM's move: {san_move}")
        move_count += 1
        try:
            uci_move = board.push_san(san_move).uci()
        except (chess.InvalidMoveError, chess.IllegalMoveError) as e:
            print(f"Invalid or illegal move received: move {move_count} by LLM - {san_move}")
            print(f"###{move_count}###")
            print(f"Error: {e}")
            break

        pgn += f" {san_move}"

        stockfish.make_moves_from_current_position([f"{uci_move}"])

        if board.is_checkmate():
            print(pgn)
            print("LLM won!")
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

if __name__ == "__main__":
    main()

