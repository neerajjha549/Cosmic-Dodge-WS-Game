#!/usr/bin/env python

import asyncio
import json
import random
import uuid
import websockets

# --- Game Constants ---
WIDTH, HEIGHT = 800, 600
PLAYER_SPEED = 5
PLAYER_RADIUS = 15
ASTEROID_RADIUS_MIN = 10
ASTEROID_RADIUS_MAX = 40
ASTEROID_SPEED_MIN = 1
ASTEROID_SPEED_MAX = 4
ASTEROID_SPAWN_INTERVAL = 1.0  # seconds

# --- Game State ---
# Using a dictionary to store player data, keyed by their connection object
# This makes it easy to add, remove, and update player information.
players = {}
# A list to hold all the asteroid objects currently in the game.
asteroids = []
# Tracks the current state of the game round.
# "waiting": Before the game starts, waiting for players.
# "in_progress": The round is actively being played.
# "finished": The round has ended, and a winner has been declared.
game_status = "waiting"
winner = None

# --- Helper Functions ---

def create_player(player_id, name):
    """Creates a new player object."""
    return {
        "id": player_id,
        "name": name,
        "x": WIDTH / 2,
        "y": HEIGHT / 2,
        "target_x": WIDTH / 2,
        "target_y": HEIGHT / 2,
        "is_alive": True,
        "radius": PLAYER_RADIUS
    }

def create_asteroid():
    """Creates a new asteroid object with random properties."""
    return {
        "x": random.randint(0, WIDTH),
        "y": 0 - ASTEROID_RADIUS_MAX, # Start just above the screen
        "radius": random.randint(ASTEROID_RADIUS_MIN, ASTEROID_RADIUS_MAX),
        "speed": random.randint(ASTEROID_SPEED_MIN, ASTEROID_SPEED_MAX)
    }

def check_collision(player, asteroid):
    """Checks for collision between a player and an asteroid."""
    distance = ((player["x"] - asteroid["x"]) ** 2 + (player["y"] - asteroid["y"]) ** 2) ** 0.5
    return distance < player["radius"] + asteroid["radius"]

# --- Game Logic ---

async def game_loop():
    """The main game loop that runs continuously."""
    global game_status, winner, asteroids
    last_asteroid_spawn_time = asyncio.get_event_loop().time()

    while True:
        current_time = asyncio.get_event_loop().time()
        
        # --- Game State Management ---
        alive_players = [p for p in players.values() if p["is_alive"]]

        if game_status == "waiting" and len(players) >= 1:
            # Start the game if at least one player is present
            game_status = "in_progress"
            asteroids = [] # Clear asteroids for the new round
            for p in players.values():
                p["is_alive"] = True # Revive all players
                p["x"], p["y"] = WIDTH / 2, HEIGHT / 2 # Reset position

        elif game_status == "in_progress":
            # --- Asteroid Spawning ---
            if current_time - last_asteroid_spawn_time > ASTEROID_SPAWN_INTERVAL:
                asteroids.append(create_asteroid())
                last_asteroid_spawn_time = current_time

            # --- Update Positions ---
            # Move players towards their target (mouse position)
            for player in players.values():
                if player["is_alive"]:
                    dx = player["target_x"] - player["x"]
                    dy = player["target_y"] - player["y"]
                    dist = (dx**2 + dy**2)**0.5
                    if dist > PLAYER_SPEED:
                        player["x"] += (dx / dist) * PLAYER_SPEED
                        player["y"] += (dy / dist) * PLAYER_SPEED
                    else:
                        player["x"] = player["target_x"]
                        player["y"] = player["target_y"]

            # Move asteroids down
            for asteroid in asteroids:
                asteroid["y"] += asteroid["speed"]

            # Remove asteroids that are off-screen
            asteroids = [a for a in asteroids if a["y"] < HEIGHT + ASTEROID_RADIUS_MAX]

            # --- Collision Detection ---
            for player in alive_players:
                for asteroid in asteroids:
                    if check_collision(player, asteroid):
                        player["is_alive"] = False
                        await broadcast_notification(f"{player['name']} has been eliminated!")
                        break # No need to check other asteroids for this player

            # --- Check for Winner ---
            alive_players_after_collision = [p for p in players.values() if p["is_alive"]]
            if len(players) > 1 and len(alive_players_after_collision) == 1:
                winner = alive_players_after_collision[0]
                game_status = "finished"
                await broadcast_notification(f"{winner['name']} is the winner!")
            elif len(players) > 0 and len(alive_players_after_collision) == 0:
                winner = None # No winner if all die simultaneously
                game_status = "finished"
                await broadcast_notification("No one survived!")

        elif game_status == "finished":
            # --- Round Cooldown and Restart ---
            await asyncio.sleep(5) # 5-second cooldown before next round
            game_status = "waiting"
            winner = None


        # --- Broadcast State ---
        # Prepare the state object to be sent to all clients
        game_state = {
            "type": "game_state",
            "players": list(players.values()),
            "asteroids": asteroids,
            "game_info": {
                "status": game_status,
                "winner": winner["name"] if winner else None
            }
        }
        await broadcast(json.dumps(game_state))

        # --- Loop Tick Rate ---
        # This controls how many times the game logic updates per second.
        # 30Hz is a good target for smooth gameplay.
        await asyncio.sleep(1/30)

# --- WebSocket Communication ---

async def broadcast(message):
    """Sends a message to all connected clients."""
    if players: # Avoid sending if no one is connected
        await asyncio.wait([asyncio.create_task(player_conn.send(message)) for player_conn in players.keys()])

async def broadcast_notification(message_text):
    """Broadcasts a simple notification message to all clients."""
    notification = {
        "type": "notification",
        "message": message_text
    }
    await broadcast(json.dumps(notification))


async def handler(websocket):
    """Handles a single client connection."""
    player_id = str(uuid.uuid4())
    player_conn = websocket
    
    try:
        # --- Player Joining ---
        # The first message from the client must be a 'join' message
        join_message = await websocket.recv()
        data = json.loads(join_message)
        
        if data["type"] == "join":
            player_name = data.get("name", "Anonymous")
            new_player = create_player(player_id, player_name)
            players[player_conn] = new_player

            # Send a welcome message to the new player with their ID
            welcome_message = {
                "type": "welcome",
                "player_id": player_id
            }
            await websocket.send(json.dumps(welcome_message))

            # Notify everyone about the new player
            await broadcast_notification(f"{player_name} has joined the game!")

        # --- Message Handling Loop ---
        async for message in websocket:
            data = json.loads(message)
            player = players.get(player_conn)
            
            if not player:
                continue

            if data["type"] == "input":
                # Update the player's target position based on mouse input
                player["target_x"] = data["mouse_pos"][0]
                player["target_y"] = data["mouse_pos"][1]

    except websockets.exceptions.ConnectionClosed:
        print(f"Player disconnected.")
    finally:
        # --- Player Leaving ---
        player_info = players.pop(player_conn, None)
        if player_info:
            await broadcast_notification(f"{player_info['name']} has left the game.")
            
        # If the last player leaves, reset the game
        if not players:
            global game_status, asteroids, winner
            game_status = "waiting"
            asteroids = []
            winner = None


async def main():
    """The main entry point for the server."""
    # Start the game loop as a background task
    asyncio.create_task(game_loop())

    # Start the WebSocket server
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Server started on ws://0.0.0.0:8765")
        await asyncio.Future() # run forever

if __name__ == "__main__":
    asyncio.run(main())

