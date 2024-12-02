# Student agent: Add your own agent here
from agents.agent import Agent
from store import register_agent
import sys
import numpy as np
from copy import deepcopy
import time
from helpers import random_move, count_capture, execute_move, check_endgame, get_valid_moves

_board_weights = None

#not used
def stability(board, maximizing_player, player, opponent):

    stability_weights = (1, 0, -1)
    def is_stable(x, y):
        if (x, y) in corners:
            return True
        for dx, dy in directions:
            if not (0 <= x + dx < n and 0 <= y + dy < n):
                continue
            if board[x + dx, y + dy] != board[x, y] or not stable[x + dx, y + dy]:
                return False
        return True

    def is_unstable(x, y):
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if n > nx >= 0 == board[nx, ny] and 0 <= ny < n:
                return True
        return False

    n = board.shape[0]
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    corners = {(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)}
    stable = np.zeros_like(board, dtype=bool)
    stability_values = {player: 0, opponent: 0}

    for x in range(n):
        for y in range(n):
            if board[x, y] == 0:
                continue  # Skip empty spaces
            player = board[x, y]
            if (x, y) in corners or is_stable(x, y):
                stable[x, y] = True
                stability_values[player] += stability_weights[0]  # Stable weight
            elif is_unstable(x, y):
                stability_values[player] += stability_weights[2]  # Unstable weight
            else:
                stability_values[player] += stability_weights[1]  # Semi-stable weight

    max_stability = stability_values[player]
    min_stability = stability_values[opponent]

    score = 0
    if max_stability + min_stability != 0:
        score = (max_stability - min_stability) / (max_stability + min_stability) * 100

    return score if maximizing_player else -score
#not used
def mobility(board, player, opponent):
    player_player_mobility = len(get_valid_moves(board, player))
    opponent_player_mobility = len(get_valid_moves(board, opponent))
    score = 0
    if player_player_mobility + opponent_player_mobility != 0:
        score = (player_player_mobility - opponent_player_mobility) / (
                    player_player_mobility + opponent_player_mobility) * 100
    return score

def board_stability(board, player, opponent):

    n = board.shape[0]
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    corners = {(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)}

    stability_map = np.full_like(board, 0, dtype=int)

    stable_value = 1
    unstable_value = -1
    semi_stable_value = 0

    # Identify corners as stable
    for x, y in corners:
        if board[x, y] != 0:
            stability_map[x, y] = stable_value

    # Create a mask for empty cells
    empty_mask = board == 0

    # Compute unstable coins (next to at least one empty space)
    unstable_mask = np.zeros_like(board, dtype=bool)
    for dx, dy in directions:
        shifted = np.roll(np.roll(empty_mask, dx, axis=0), dy, axis=1)
        # Ignore out-of-bounds caused by rolling
        if dx > 0:
            shifted[:dx, :] = False
        elif dx < 0:
            shifted[dx:, :] = False
        if dy > 0:
            shifted[:, :dy] = False
        elif dy < 0:
            shifted[:, dy:] = False
        unstable_mask |= (shifted & (board != 0))

    # Assign unstable coins
    stability_map[unstable_mask] = unstable_value

    # Semi-stable coins (neither stable nor unstable)
    for x in range(n):
        for y in range(n):
            if stability_map[x, y]==0 and board[x, y] != 0:
                stability_map[x, y] = semi_stable_value

    return stability_map

def parity(board, player, opponent):
    player_score = np.sum(board == player)
    opponent_score = np.sum(board == opponent)
    return (player_score - opponent_score) / (player_score + opponent_score) *100

def corner_capture(board, player, opponent):
    player_corner_capture = 0
    opponent_corner_capture = 0
    board_size = board.shape[0]
    near_corner_player = 0
    near_corner_opponent = 0
    for corner in [(0, 0), (0, board_size - 1), (board_size - 1, 0), (board_size - 1, board_size - 1)]:
        if board[corner] != 0:
            if board[corner] == player:
                player_corner_capture += 1
            else:
                opponent_corner_capture += 1
        else :
            for d in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                if 0 <= corner[0] + d[0] < board_size and 0 <= corner[1] + d[1] < board_size :
                    if board[(corner[0] + d[0],corner[1] + d[1])] == player:
                        near_corner_player += 1
                    if board[(corner[0] + d[0],corner[1] + d[1])] == opponent:
                        near_corner_opponent += 1

    corner_score = 0
    near_corner_score = 0
    if (player_corner_capture + opponent_corner_capture) != 0:
        corner_score = (player_corner_capture-opponent_corner_capture)/(player_corner_capture+opponent_corner_capture) *100
    if (near_corner_player + near_corner_opponent) != 0:
        near_corner_score = (near_corner_opponent-near_corner_player)/(near_corner_opponent+near_corner_player) *100
    return (corner_score,near_corner_score)

def board_weights(board_size):
    global _board_weights

    def static_weights(board_size):

        ratio = 8 + abs(board_size - 8) / 8
        weights = np.zeros((board_size, board_size))
        corner_value = 4 * ratio
        near_corner_penalty = -3 * ratio
        near_corner_diagonal_penalty = -4 * ratio
        near_edge_value = -1 * ratio
        edge_value = 2 * ratio
        inner_value = 0.5 * ratio
        middle_four_value = 1 * ratio

        middle_four = [(board_size // 2 - 1, board_size // 2 - 1), (board_size // 2 - 1, board_size // 2),
                       (board_size // 2, board_size // 2 - 1), (board_size // 2, board_size // 2)]
        corners = [(0, 0), (0, board_size - 1), (board_size - 1, 0), (board_size - 1, board_size - 1)]
        near_corners = [(0, 1), (1, 0), (0, board_size - 2), (1, board_size - 1), (board_size - 2, 0),
                        (board_size - 1, 1), (board_size - 2, board_size - 1), (board_size - 1, board_size - 2)]
        near_corner_diagonal = [(1, 1), (1, board_size - 2), (board_size - 2, 1), (board_size - 2, board_size - 2)]

        for i in range(board_size):
            for j in range(board_size):
                if (i, j) in corners:
                    weights[i, j] = corner_value
                elif (i, j) in middle_four:
                    weights[i, j] = middle_four_value
                elif i in [0, board_size - 1] or j in [0, board_size - 1]:
                    weights[i, j] = edge_value if (i, j) not in near_corners else near_corner_penalty
                elif (i, j) not in near_corner_diagonal and (
                        i == board_size - 2 or j == board_size - 2 or i == 1 or j == 1):
                    weights[i, j] = near_edge_value
                else:
                    weights[i, j] = inner_value if (i, j) not in near_corner_diagonal else near_corner_diagonal_penalty

        return weights


    if _board_weights is None or _board_weights.shape[0] != board_size:
        _board_weights = static_weights(board_size)
    return _board_weights

def heuristic(board, player, opponent):
    #parity_score = parity(board, player, opponent)
    (corners_score,near_corner_penalty) = corner_capture(board, player, opponent)
    #weights = board_weights(board.shape[0])
    #board_score = (np.sum((board == player) * weights) - np.sum((board == opponent) * weights))
    #stability = board_stability(board, player, opponent)
    #stability_score = np.sum((board==player) * stability) - np.sum((board==opponent) * stability)
    #mobility_score = mobility(board, player, opponent)
    #print(parity_score,corners_score,stability_score,board_score,parity_score * 25 + corners_score * 30 + stability_score * 25 + board_score * 20)
    return  corners_score * 30

def alpha_beta(board, depth, alpha, beta, maximizing_player, player, opponent, start_time,move_order=None):
    """
    Alpha-beta pruning with optional move ordering.

    Args:
        board (np.ndarray): The current state of the board.
        depth (int): Maximum search depth.
        alpha (float): Alpha value for pruning.
        beta (float): Beta value for pruning.
        maximizing_player (bool): Whether the current player is maximizing or minimizing.
        player (int): Maximizing player.
        opponent (int): Minimizing player.
        move_order (list): A list of moves ordered by priority from the previous iteration.

    Returns:
        tuple: The best evaluation value and the best move.
    """

    valid_moves = get_valid_moves(board, player if maximizing_player else opponent)
    if depth == 0 or not valid_moves:
        return heuristic(board, player, opponent), None

    if time.time() - start_time >=2 :
        #print("alpha",time.time(),start_time)
        raise TimeoutError

    # Use move ordering if provided
    if move_order:
        valid_moves = sorted(valid_moves, key=lambda m: move_order.index(m) if m in move_order else len(move_order))

    best_move = None
    if maximizing_player:
        max_eval = float('-inf')
        for move in valid_moves:
            new_board = deepcopy(board)
            execute_move(new_board, move, player)
            eval, _ = alpha_beta(new_board, depth - 1, alpha, beta, False, player, opponent, start_time,move_order)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in valid_moves:
            new_board = deepcopy(board)
            execute_move(new_board, move, opponent)
            eval, _ = alpha_beta(new_board, depth - 1, alpha, beta, True, player,opponent, start_time,move_order)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval, best_move


@register_agent("corners")
class Corners(Agent):

    def __init__(self):
        super(Corners, self).__init__()
        self.name = "corners"

    def step(self, board, player, opponent):

        best_value = float('-inf')
        best_move = None
        depth = [5,4,4,3,3,2,2][board.shape[0]-6]
        move_order = []  # Store the best move from previous depths for ordering
        start_time = time.time()
        #print("step",start_time)

        while True:

            if time.time() - start_time >= 2:
                break

            try:
                #print(time.time() - start_time)
                #print(start_time)
                value, move = alpha_beta(board, depth, float('-inf'), float('inf'), True, player, opponent, start_time, move_order)
                if move is not None:
                    best_move = move
                    best_value = value
                    # Update move order to prioritize the current best move
                    move_order = [best_move] + [m for m in move_order if m != best_move]
                depth += 1

            except TimeoutError:
                break

        time_taken = time.time() - start_time
        #print(f"Player {player}'s turn took {time_taken:.4f} seconds. For a board of size {board.shape[0]}.")
        #print("BEST MOVE :",best_move,"at depth ",depth-1," possible moves",len(get_valid_moves(board, player)))
        return best_move