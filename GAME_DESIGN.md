
# Design Document: Cosmic Dodge

This document outlines the architecture and design for "Cosmic Dodge," a real-time, multiplayer browser game built with Python websockets.

## 1. Game Concept 🚀

-   **Objective:** Players control a spaceship with their mouse. Asteroids continuously spawn from the top of the screen and move downwards. Players must dodge the asteroids. If a player's ship is hit, they are eliminated. The last player standing wins the round.
    
-   **Rounds:** The game is round-based. A new round starts shortly after a winner is determined.
    
-   **Audience:** Casual gamers looking for a quick and fun real-time competitive experience.
    

## 2. System Architecture

The application follows a classic client-server model, designed for low-latency communication.

-   **Server:** A single Python application acting as the authoritative game server. It manages all game logic, player states, and physics. It's the single source of truth.
    
-   **Clients:** Web browsers connecting to the server via WebSockets. The client is responsible for rendering the game state received from the server and sending user input (mouse movements) back to the server.
    
-   **Communication:** WebSockets are used for persistent, bidirectional communication. Messages are sent in JSON format for easy parsing on both the server (Python) and client (JavaScript).
    

### Technology Stack

-   **Server-side:**
    
    -   **Language:** Python 3.9+
        
    -   **Core Libraries:**
        
        -   `asyncio`: For handling concurrent operations and connections efficiently.
            
        -   `websockets`: For managing WebSocket connections.
            
        -   `json`: For serializing and deserializing messages.
            
-   **Client-side:**
    
    -   **Structure:** HTML
        
    -   **Styling:** CSS
        
    -   **Logic:** JavaScript (ES6+) for handling rendering on an HTML `<canvas>` and communicating with the server.
        

## 3. WebSocket Message Protocol

A clear and concise message protocol is crucial. All messages will be JSON objects with a `type` field.

### Client to Server Messages

-   `{"type": "join", "name": "PlayerName"}`: Sent when a player first connects and joins the game.
    
-   `{"type": "input", "mouse_pos": [x, y]}`: Sent frequently to update the server with the player's current mouse position, which dictates their ship's target location.
    

### Server to Client Messages

-   `{"type": "game_state", "players": [...], "asteroids": [...], "game_info": {...}}`: Broadcast to all clients at a fixed rate (e.g., 30 times per second). This is the primary message for rendering the game.
    
    -   `players`: A list of all player objects, including their ID, name, position, and status (alive/dead).
        
    -   `asteroids`: A list of all asteroid objects with their position and size.
        
    -   `game_info`: Contains round status (e.g., "waiting", "in_progress", "finished"), timer, and winner information.
        
-   `{"type": "welcome", "player_id": "unique_id"}`: Sent to a client upon successfully joining, providing them with their unique ID.
    
-   `{"type": "notification", "message": "Player X has joined!"}`: Sent to all clients to announce game events like joins, leaves, or wins.
    

## 4. Game Logic and State Management

-   **Game Loop:** The server runs a central, asynchronous game loop. This loop ticks at a fixed rate (e.g., 30 Hz).
    
-   **State Updates:** In each tick, the server:
    
    1.  Processes any pending input from clients.
        
    2.  Updates player ship positions (moving them towards their target mouse position).
        
    3.  Spawns new asteroids if required.
        
    4.  Updates all asteroid positions.
        
    5.  Performs collision detection between players and asteroids.
        
    6.  Updates the game state (player status, round timer, etc.).
        
    7.  Broadcasts the new `game_state` to all connected clients.
        
-   **State:** The server maintains the entire game state in memory, including:
    
    -   A dictionary of connected players.
        
    -   A list of active asteroids.
        
    -   The current game round status.
        

This design ensures that the server is fully authoritative, preventing cheating and keeping all players perfectly synchronized.