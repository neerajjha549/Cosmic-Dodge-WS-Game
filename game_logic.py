import asyncio
import json
import random
from constants import *
import game_state
from models import Asteroid

# --- Broadcasting Functions ---

async def broadcast_game_state():
    """ Sends the current game state to all connected players. """
    if not game_state.players:
        return

    state_message = {
        "type": "game_state",
        "players": [p.to_dict() for p in game_state.players.values()],
        "asteroids": [a.to_dict() for a in game_state.asteroids],
        "game_info": game_state.game_info,
    }
    message = json.dumps(state_message)
    # Use asyncio.gather for concurrent sends
    await asyncio.gather(*[p.websocket.send(message) for p in game_state.players.values()])

async def broadcast_notification(message):
    """ Sends a notification message to all players. """
    if not game_state.players:
        return

    notification = {"type": "notification", "message": message}
    message = json.dumps(notification)
    await asyncio.gather(*[p.websocket.send(message) for p in game_state.players.values()])

# --- Core Game Logic ---

def check_collisions():
    """ Checks for collisions between players and asteroids. """
    for player in game_state.players.values():
        if not player.is_alive:
            continue
        for asteroid in game_state.asteroids:
            dist_sq = (player.x - asteroid.x)**2 + (player.y - asteroid.y)**2
            if dist_sq < (player.radius + asteroid.radius)**2:
                player.is_alive = False
                asyncio.create_task(broadcast_notification(f"{player.name} was eliminated!"))

def update_game_elements():
    """ Updates positions of players and asteroids, and removes off-screen asteroids. """
    for player in game_state.players.values():
        player.update()
    for asteroid in list(game_state.asteroids):
        asteroid.update()
        if asteroid.y > HEIGHT + asteroid.radius:
            game_state.asteroids.remove(asteroid)

def check_for_winner():
    """ Checks if a winner can be determined. """
    if game_state.game_info["status"] != "in_progress":
        return

    alive_players = [p for p in game_state.players.values() if p.is_alive]
    # A winner is decided if 1 or 0 players are left alive (and there was >1 to start)
    if len(alive_players) <= 1 and len(game_state.players) > 1:
        game_state.game_info["status"] = "finished"
        winner = alive_players[0] if alive_players else None
        
        if winner:
            game_state.game_info["winner"] = winner.name
            asyncio.create_task(broadcast_notification(f"🎉 {winner.name} wins the round! 🎉"))
        else:
            game_state.game_info["winner"] = None  # Draw or all eliminated
            asyncio.create_task(broadcast_notification("No survivors!"))
        
        # Schedule the next round to start after a delay
        asyncio.create_task(start_next_round_soon(5))

def reset_game():
    """ Resets the game state for a new round. """
    game_state.asteroids.clear()
    for player in game_state.players.values():
        player.is_alive = True
        player.x = random.randint(100, WIDTH - 100)
        player.y = random.randint(100, HEIGHT - 100)
    game_state.game_info["status"] = "in_progress"
    game_state.game_info["winner"] = None

async def start_next_round_soon(delay):
    """ Waits for a delay then starts a new round. """
    await asyncio.sleep(delay)
    reset_game()
    await broadcast_notification("New round starting now!")

# --- Main Game Loop ---

async def game_loop():
    """ The main, continuous loop that runs the game logic. """
    last_asteroid_spawn = asyncio.get_event_loop().time()

    while True:
        loop_start_time = asyncio.get_event_loop().time()

        if game_state.game_info["status"] == "in_progress":
            # Spawn new asteroids periodically
            now = asyncio.get_event_loop().time()
            if now - last_asteroid_spawn > ASTEROID_SPAWN_INTERVAL:
                game_state.asteroids.append(Asteroid())
                last_asteroid_spawn = now
            
            # Update all game elements and check for events
            update_game_elements()
            check_collisions()
            check_for_winner()

        # Broadcast the latest state to all clients
        await broadcast_game_state()

        # Maintain a consistent tick rate
        elapsed_time = asyncio.get_event_loop().time() - loop_start_time
        await asyncio.sleep(max(0, GAME_TICK_RATE - elapsed_time))

