#!/usr/bin/env python3

import boto3
import logging
from stockfish import Stockfish
import chess

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

def get_claude_move(pgn, color, messages):
    model_id = "meta.llama3-1-70b-instruct-v1:0"
    
    new_message = {
        "role": "user",
        "content": [{"text": f"You are a chess grandmaster. Given this chess game PGN, what's your next move for {color}? Respond with only the move in SAN notation, without the move number:\n\n{pgn}"}]
    }
    messages.append(new_message)

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={"temperature": 0, "maxTokens": 5}
        )
        
        output_message = response['output']['message']
        messages.append(output_message)
        
        move_text = output_message['content'][0]['text']
        san_move = move_text.strip().split()[0]
        
        # Log token usage
        token_usage = response['usage']
        #logger.info(f"Input tokens: {token_usage['inputTokens']}")
        #logger.info(f"Output tokens: {token_usage['outputTokens']}")
        #logger.info(f"Total tokens: {token_usage['totalTokens']}")
        #logger.info(f"Stop reason: {response['stopReason']}")
        
        return san_move, messages
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return None, messages

def main():
    global pgn
    n = 1
    move_count = 0
    messages = []
    
    while True:
        san_move, messages = get_claude_move(pgn, 'White' if board.turn else 'Black', messages)
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

