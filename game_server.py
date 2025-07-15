#!/usr/bin/env python

import asyncio
import json
import websockets
from models import Player
from game_logic import game_loop, broadcast_notification, reset_game
import game_state

async def connection_handler(websocket):
    """
    Handles a new player's WebSocket connection, processing their messages
    and cleaning up when they disconnect.
    """
    player = None
    try:
        # The first message from a client must be a "join" request.
        async for message in websocket:
            data = json.loads(message)

            if data.get("type") == "join" and not player:
                # Create a new Player object and add it to the game state.
                player = Player(websocket, data.get("name", "Anonymous"))
                game_state.players[player.id] = player
                
                # Send a "welcome" message back to the new player with their ID.
                await websocket.send(json.dumps({
                    "type": "welcome",
                    "player_id": player.id
                }))
                
                await broadcast_notification(f"{player.name} has joined the game!")
                
                # If this is the first player, start the game.
                if len(game_state.players) == 1:
                    reset_game()
                    await broadcast_notification("The first player has joined. The game begins!")

            elif data.get("type") == "input" and player and player.is_alive:
                # Update player's target position from mouse coordinates.
                player.target_x, player.target_y = data["mouse_pos"]

    finally:
        # This block executes when the player's connection is closed.
        if player:
            # Remove the player from the game state.
            del game_state.players[player.id]
            await broadcast_notification(f"{player.name} has left the game.")
            # If no players are left, reset the game to the "waiting" screen.
            if not game_state.players:
                game_state.game_info["status"] = "waiting"

async def main():
    """ The main function to set up and run the server. """
    # Start the central game loop as a background task.
    asyncio.create_task(game_loop())

    # Start the WebSocket server.
    async with websockets.serve(connection_handler, "0.0.0.0", 8765):
        print("Server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server is shutting down.")

