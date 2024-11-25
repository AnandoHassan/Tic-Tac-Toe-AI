from flask import Flask, render_template, request, session, jsonify
import random
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your_secret_key_here'

def check_winner(board):
    # Check rows, columns and diagonals
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]
    
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != "":
            return board[combo[0]]
    
    if "" not in board:
        return "tie"
    return None

def minimax(board, depth, is_maximizing):
    result = check_winner(board)
    
    if result == "O":
        return 10 - depth
    elif result == "X":
        return depth - 10
    elif result == "tie":
        return 0
        
    if is_maximizing:
        best_score = float('-inf')
        for i in range(9):
            if board[i] == "":
                board[i] = "O"
                score = minimax(board, depth + 1, False)
                board[i] = ""
                best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for i in range(9):
            if board[i] == "":
                board[i] = "X"
                score = minimax(board, depth + 1, True)
                board[i] = ""
                best_score = min(score, best_score)
        return best_score

def get_best_move(board):
    best_score = float('-inf')
    best_move = None
    
    for i in range(9):
        if board[i] == "":
            board[i] = "O"
            score = minimax(board, 0, False)
            board[i] = ""
            if score > best_score:
                best_score = score
                best_move = i
    
    return best_move

@app.route('/')
def home():
    if 'board' not in session:
        session['board'] = [""] * 9
        session['player_score'] = 0
        session['ai_score'] = 0
        session['ties'] = 0
    return render_template('game.html')

@app.route('/play', methods=['POST'])
def play():
    position = request.json.get('position')
    board = session.get('board', [""] * 9)
    
    # Validate the move
    if position is None or position < 0 or position > 8 or board[position] != "":
        return jsonify({'error': 'Invalid move'}), 400
    
    # Player's move
    board[position] = "X"
    session['board'] = board  # Save the board state immediately after player's move
    
    # Check if player won
    winner = check_winner(board)
    if winner:
        if winner == "X":
            session['player_score'] = session.get('player_score', 0) + 1
        elif winner == "tie":
            session['ties'] = session.get('ties', 0) + 1
        return jsonify({
            'board': board,
            'winner': winner,
            'thinking': False,
            'scores': {
                'player': session['player_score'],
                'ai': session['ai_score'],
                'ties': session['ties']
            }
        })
    
    # Return that AI is thinking
    return jsonify({
        'board': board,
        'thinking': True,
        'scores': {
            'player': session['player_score'],
            'ai': session['ai_score'],
            'ties': session['ties']
        }
    })

@app.route('/ai_move', methods=['POST'])
def ai_move():
    board = session.get('board', [""] * 9)
    
    # Verify there's a valid board state
    if not board or "" not in board:
        return jsonify({'error': 'Invalid board state'}), 400
    
    # AI's move
    ai_move = get_best_move(board)
    if ai_move is not None:
        board[ai_move] = "O"
        session['board'] = board  # Save the board state after AI's move
        
        # Check if AI won
        winner = check_winner(board)
        if winner == "O":
            session['ai_score'] = session.get('ai_score', 0) + 1
        elif winner == "tie":
            session['ties'] = session.get('ties', 0) + 1
    
    return jsonify({
        'board': board,
        'winner': winner if 'winner' in locals() else None,
        'thinking': False,
        'scores': {
            'player': session['player_score'],
            'ai': session['ai_score'],
            'ties': session['ties']
        }
    })

@app.route('/reset', methods=['POST'])
def reset():
    session['board'] = [""] * 9
    gameActive = True
    return jsonify({
        'status': 'success', 
        'board': session['board']
    })

@app.route('/reset_scores', methods=['POST'])
def reset_scores():
    session['player_score'] = 0
    session['ai_score'] = 0
    session['ties'] = 0
    session['board'] = [""] * 9
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
