#!/usr/bin/env python

import asyncio
import json
import random
import uuid
import websockets

# --- Game Constants ---
WIDTH, HEIGHT = 800, 600
PLAYER_RADIUS = 15
ASTEROID_MIN_RADIUS = 10  # New constant for smallest asteroid
ASTEROID_MAX_RADIUS = 40  # New constant for largest asteroid
ASTEROID_BASE_SPEED = 4   # New constant for speed calculation
ASTEROID_SPAWN_INTERVAL = 0.5 # Seconds
GAME_TICK_RATE = 1 / 60.0 # 60 updates per second for lower latency
PLAYER_ACCELERATION = 0.4 # Increased from 0.1 for snappier movement

# --- Game State ---
players = {}
asteroids = []
game_state = {
    "status": "waiting", # waiting, in_progress, finished
    "winner": None,
    "round_start_time": 0
}

# --- Game Classes ---

class Player:
    def __init__(self, websocket, name):
        self.websocket = websocket
        self.id = str(uuid.uuid4())
        self.name = name
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.target_x = self.x
        self.target_y = self.y
        self.radius = PLAYER_RADIUS
        self.is_alive = True

    def update(self):
        """ Move player towards the target (mouse) position """
        if self.is_alive:
            # Increased acceleration factor for more responsive movement
            self.x += (self.target_x - self.x) * PLAYER_ACCELERATION
            self.y += (self.target_y - self.y) * PLAYER_ACCELERATION

    def to_dict(self):
        """ Serialize player state to a dictionary for JSON """
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "is_alive": self.is_alive,
        }

class Asteroid:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        # Assign a random radius within the defined range
        self.radius = random.randint(ASTEROID_MIN_RADIUS, ASTEROID_MAX_RADIUS)
        self.y = -self.radius # Start just off-screen based on its new size
        
        # Make speed dependent on size (bigger = slower)
        # We use max(1, ...) to ensure speed is never zero or negative.
        self.speed = ASTEROID_BASE_SPEED / (self.radius / ASTEROID_MIN_RADIUS)

    def update(self):
        """ Move asteroid downwards """
        self.y += self.speed

    def to_dict(self):
        """ Serialize asteroid state to a dictionary for JSON """
        return {"x": self.x, "y": self.y, "radius": self.radius}

# --- Game Logic ---

def reset_game():
    """ Resets the game state for a new round """
    asteroids.clear()
    for player in players.values():
        player.is_alive = True
        player.x = random.randint(100, WIDTH - 100)
        player.y = random.randint(100, HEIGHT - 100)
    game_state["status"] = "in_progress"
    game_state["winner"] = None

async def broadcast_game_state():
    """ Sends the current game state to all connected players """
    if not players:
        return
    
    state = {
        "type": "game_state",
        "players": [p.to_dict() for p in players.values()],
        "asteroids": [a.to_dict() for a in asteroids],
        "game_info": game_state,
    }
    message = json.dumps(state)
    # Use asyncio.gather for concurrent sends
    await asyncio.gather(*[p.websocket.send(message) for p in players.values()])

async def broadcast_notification(message):
    """ Sends a notification message to all players """
    if not players:
        return
    
    notification = {
        "type": "notification",
        "message": message
    }
    message = json.dumps(notification)
    await asyncio.gather(*[p.websocket.send(message) for p in players.values()])

def check_collisions():
    """ Checks for collisions between players and asteroids """
    for player in players.values():
        if not player.is_alive:
            continue
        for asteroid in asteroids:
            dist_sq = (player.x - asteroid.x)**2 + (player.y - asteroid.y)**2
            if dist_sq < (player.radius + asteroid.radius)**2:
                player.is_alive = False
                asyncio.create_task(broadcast_notification(f"{player.name} was eliminated!"))

def update_game():
    """ Main game update function """
    # Update all positions
    for player in players.values():
        player.update()
    for asteroid in list(asteroids):
        asteroid.update()
        # Remove asteroids that are off-screen
        if asteroid.y > HEIGHT + asteroid.radius:
            asteroids.remove(asteroid)

    # Check for collisions
    check_collisions()
    
    # Check for a winner
    alive_players = [p for p in players.values() if p.is_alive]
    if len(alive_players) <= 1 and len(players) > 1 and game_state["status"] == "in_progress":
        game_state["status"] = "finished"
        if alive_players:
            winner = alive_players[0]
            game_state["winner"] = winner.name
            asyncio.create_task(broadcast_notification(f"🎉 {winner.name} wins the round! 🎉"))
        else:
            game_state["winner"] = None # Draw or all eliminated
            asyncio.create_task(broadcast_notification("No survivors!"))
        
        # Schedule the next round
        asyncio.create_task(start_next_round_soon(5))

async def start_next_round_soon(delay):
    """ Waits for a delay then starts a new round """
    await asyncio.sleep(delay)
    reset_game()
    await broadcast_notification("New round starting now!")


async def game_loop():
    """ The main, continuous loop that runs the game """
    last_asteroid_spawn = asyncio.get_event_loop().time()
    
    while True:
        loop_start_time = asyncio.get_event_loop().time()

        # Only run game logic if the round is in progress
        if game_state["status"] == "in_progress":
            # Spawn new asteroids
            now = asyncio.get_event_loop().time()
            if now - last_asteroid_spawn > ASTEROID_SPAWN_INTERVAL:
                asteroids.append(Asteroid())
                last_asteroid_spawn = now
            
            update_game()

        await broadcast_game_state()

        # Maintain a consistent tick rate
        elapsed_time = asyncio.get_event_loop().time() - loop_start_time
        await asyncio.sleep(max(0, GAME_TICK_RATE - elapsed_time))

# --- WebSocket Handler ---

async def handler(websocket):
    """ Handles a new WebSocket connection """
    player = None
    try:
        # Wait for the first message, which should be 'join'
        async for message in websocket:
            data = json.loads(message)

            if data.get("type") == "join" and not player:
                player = Player(websocket, data.get("name", "Anonymous"))
                players[player.id] = player
                
                # Send a welcome message with the player's new ID
                await websocket.send(json.dumps({
                    "type": "welcome",
                    "player_id": player.id
                }))
                
                await broadcast_notification(f"{player.name} has joined the game!")
                
                # Start the game if it's the first player
                if len(players) == 1:
                    reset_game()
                    await broadcast_notification("The first player has joined. The game begins!")

            elif data.get("type") == "input" and player and player.is_alive:
                # Update player's target position from mouse coordinates
                player.target_x, player.target_y = data["mouse_pos"]

    finally:
        # Player disconnected
        if player:
            del players[player.id]
            await broadcast_notification(f"{player.name} has left the game.")
            # If no players are left, reset the game state
            if not players:
                game_state["status"] = "waiting"

# --- Main Server Execution ---

async def main():
    # Start the central game loop as a background task
    asyncio.create_task(game_loop())

    # Start the WebSocket server
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

