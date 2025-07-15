import asyncio
import json
import random
import uuid
import websockets

# --- Game Configuration ---
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8765
GAME_WIDTH = 800
GAME_HEIGHT = 600
PLAYER_SPEED = 4
PLAYER_RADIUS = 15
ASTEROID_RADIUS = 20
ASTEROID_SPEED = 2
ASTEROID_SPAWN_RATE = 0.03 # Probability of spawning an asteroid each tick
GAME_TICK_RATE = 1 / 30  # 30 ticks per second

# --- Game State ---
# Using a dictionary to hold the game state makes it easy to serialize
# and manage.
GAME_STATE = {
    "players": {},
    "asteroids": [],
    "game_info": {
        "status": "waiting", # waiting, in_progress, finished
        "winner": None,
        "round_start_timer": 5
    }
}
CONNECTED_CLIENTS = set()

# --- Helper Functions ---
def get_player_by_websocket(ws):
    """Find a player ID associated with a WebSocket connection."""
    for player_id, player_data in GAME_STATE["players"].items():
        if player_data.get("ws") == ws:
            return player_id
    return None

def check_collision(obj1_pos, obj1_radius, obj2_pos, obj2_radius):
    """Check for collision between two circular objects."""
    distance = ((obj1_pos[0] - obj2_pos[0]) ** 2 + (obj1_pos[1] - obj2_pos[1]) ** 2) ** 0.5
    return distance < (obj1_radius + obj2_radius)

# --- Game Logic ---
async def reset_round():
    """Resets the game state for a new round."""
    print("Resetting round...")
    GAME_STATE["asteroids"].clear()
    GAME_STATE["game_info"]["status"] = "waiting"
    GAME_STATE["game_info"]["winner"] = None
    GAME_STATE["game_info"]["round_start_timer"] = 5
    
    # Reset all players to alive and place them randomly
    for player_id, player in GAME_STATE["players"].items():
        player["alive"] = True
        player["pos"] = [random.randint(50, GAME_WIDTH - 50), random.randint(50, GAME_HEIGHT - 50)]
        player["target_pos"] = list(player["pos"]) # Set target to current position
    
    # Start the countdown timer
    while GAME_STATE["game_info"]["round_start_timer"] > 0:
        await asyncio.sleep(1)
        GAME_STATE["game_info"]["round_start_timer"] -= 1
    
    GAME_STATE["game_info"]["status"] = "in_progress"
    print("Round started!")


async def game_loop():
    """The main game loop that runs continuously."""
    loop = asyncio.get_running_loop()
    loop.create_task(reset_round()) # Start the first round

    while True:
        start_time = loop.time()

        if GAME_STATE["game_info"]["status"] == "in_progress":
            # --- Update Player Positions ---
            for player_id, player in GAME_STATE["players"].items():
                if not player["alive"]:
                    continue
                # Move player towards their target position (set by mouse)
                dx = player["target_pos"][0] - player["pos"][0]
                dy = player["target_pos"][1] - player["pos"][1]
                dist = (dx**2 + dy**2)**0.5
                if dist > PLAYER_SPEED:
                    player["pos"][0] += (dx / dist) * PLAYER_SPEED
                    player["pos"][1] += (dy / dist) * PLAYER_SPEED
        
            # --- Update Asteroids ---
            # Spawn new asteroids
            if random.random() < ASTEROID_SPAWN_RATE:
                GAME_STATE["asteroids"].append({
                    "id": str(uuid.uuid4()),
                    "pos": [random.randint(0, GAME_WIDTH), -ASTEROID_RADIUS],
                    "speed": random.uniform(ASTEROID_SPEED * 0.8, ASTEROID_SPEED * 1.2)
                })

            # Move existing asteroids and remove off-screen ones
            for asteroid in list(GAME_STATE["asteroids"]):
                asteroid["pos"][1] += asteroid["speed"]
                if asteroid["pos"][1] > GAME_HEIGHT + ASTEROID_RADIUS:
                    GAME_STATE["asteroids"].remove(asteroid)

            # --- Collision Detection ---
            for player_id, player in GAME_STATE["players"].items():
                if not player["alive"]:
                    continue
                for asteroid in GAME_STATE["asteroids"]:
                    if check_collision(player["pos"], PLAYER_RADIUS, asteroid["pos"], ASTEROID_RADIUS):
                        player["alive"] = False
                        print(f"Player {player['name']} was hit!")
                        break # No need to check other asteroids for this player

            # --- Check for Winner ---
            alive_players = [p for p in GAME_STATE["players"].values() if p["alive"]]
            if len(alive_players) <= 1 and len(GAME_STATE["players"]) > 1:
                GAME_STATE["game_info"]["status"] = "finished"
                if len(alive_players) == 1:
                    GAME_STATE["game_info"]["winner"] = alive_players[0]["name"]
                    print(f"Round over. Winner is {alive_players[0]['name']}")
                else: # All players died in the same frame
                    GAME_STATE["game_info"]["winner"] = "Nobody"
                    print("Round over. Nobody wins.")
                
                await asyncio.sleep(5) # Wait 5 seconds before starting a new round
                await reset_round()
            elif len(alive_players) == 0 and len(GAME_STATE["players"]) == 1:
                 GAME_STATE["game_info"]["status"] = "finished"
                 GAME_STATE["game_info"]["winner"] = "Nobody"
                 await asyncio.sleep(5)
                 await reset_round()


        # --- Broadcast State ---
        # Create a deep copy of the state to send, excluding sensitive data like websockets
        state_to_send = {
            "players": {pid: {k: v for k, v in p.items() if k != 'ws'} for pid, p in GAME_STATE["players"].items()},
            "asteroids": GAME_STATE["asteroids"],
            "game_info": GAME_STATE["game_info"]
        }
        
        message = json.dumps({"type": "game_state", **state_to_send})
        if CONNECTED_CLIENTS:
            await asyncio.wait([client.send(message) for client in CONNECTED_CLIENTS])

        # --- Maintain Tick Rate ---
        elapsed_time = loop.time() - start_time
        await asyncio.sleep(max(0, GAME_TICK_RATE - elapsed_time))


# --- WebSocket Handler ---
async def handler(websocket, path):
    """Handles WebSocket connections, messages, and disconnections."""
    CONNECTED_CLIENTS.add(websocket)
    player_id = None
    print(f"Client connected. Total clients: {len(CONNECTED_CLIENTS)}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data["type"] == "join":
                    player_id = str(uuid.uuid4())
                    player_name = data.get("name", "Anonymous")
                    GAME_STATE["players"][player_id] = {
                        "ws": websocket, # Keep a reference to the websocket object
                        "name": player_name,
                        "pos": [random.randint(50, GAME_WIDTH-50), random.randint(50, GAME_HEIGHT-50)],
                        "target_pos": [0,0],
                        "alive": True,
                        "color": f"hsl({random.randint(0, 360)}, 100%, 50%)"
                    }
                    GAME_STATE["players"][player_id]["target_pos"] = list(GAME_STATE["players"][player_id]["pos"])
                    print(f"Player {player_name} ({player_id}) joined.")
                    
                    # Send welcome message with player ID
                    await websocket.send(json.dumps({"type": "welcome", "player_id": player_id}))
                
                elif data["type"] == "input":
                    # It's important to find the player_id associated with this specific websocket
                    p_id = get_player_by_websocket(websocket)
                    if p_id and GAME_STATE["players"][p_id]["alive"]:
                        GAME_STATE["players"][p_id]["target_pos"] = data["mouse_pos"]

            except json.JSONDecodeError:
                print("Received invalid JSON message.")
            except KeyError:
                print("Received message with missing 'type' key.")

    except websockets.exceptions.ConnectionClosed:
        print("Client connection closed.")
    finally:
        # --- Handle Disconnection ---
        if player_id and player_id in GAME_STATE["players"]:
            print(f"Player {GAME_STATE['players'][player_id]['name']} disconnected.")
            del GAME_STATE["players"][player_id]
        
        CONNECTED_CLIENTS.remove(websocket)
        print(f"Client disconnected. Total clients: {len(CONNECTED_CLIENTS)}")


# --- Main Entry Point ---
async def main():
    """Starts the game server and the main game loop."""
    print(f"Starting server on ws://{SERVER_HOST}:{SERVER_PORT}")
    game_server = await websockets.serve(handler, SERVER_HOST, SERVER_PORT)
    
    # Start the game loop as a background task
    asyncio.create_task(game_loop())
    
    await game_server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")
