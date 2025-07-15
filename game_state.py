# This file holds the global state that needs to be shared across modules.

# A dictionary of all connected players, keyed by player ID.
players = {}

# A list of all active asteroids on the screen.
asteroids = []

# A dictionary holding general information about the current round.
game_info = {
    "status": "waiting",  # "waiting", "in_progress", "finished"
    "winner": None,
}

