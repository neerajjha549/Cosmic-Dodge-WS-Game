# Cosmic Dodge - Real-time WebSocket Game

Cosmic Dodge is a multiplayer, real-time, browser-based game built with Python `websockets` and `asyncio` on the backend, and HTML/CSS/JavaScript on the frontend.

Players control a ship and must dodge a continuous stream of asteroids. The last player standing wins the round.

## Features

-   **Real-time Multiplayer:** Play with multiple people in the same game world.
    
-   **Asynchronous Server:** Built on Python's `asyncio` for high-performance handling of many concurrent connections.
    
-   **Authoritative Server:** All game logic, physics, and state are handled by the server to prevent cheating.
    
-   **Simple & Scalable:** The design is straightforward and can be extended with new features.
    
-   **Browser-based Client:** No installation required for players, just a modern web browser.
    

## Technology Stack

-   **Backend:** Python, `websockets`, `asyncio`
    
-   **Frontend:** HTML5 Canvas, JavaScript (ES6+), CSS
    

## How to Run

### 1. Prerequisites

-   Python 3.9 or newer
    
-   A modern web browser (Chrome, Firefox, etc.)
    

### 2. Setup

First, clone the repository:

```
git clone <your-repo-url>
cd <your-repo-directory>

```

Next, it's recommended to create a virtual environment:

```
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

```

Install the required Python packages:

```
pip install -r requirements.txt

```

### 3. Run the Server

Start the Python WebSocket server:

```
python server.py

```

You should see output indicating the server has started:

```
Starting server on ws://0.0.0.0:8765

```

The server is now running and waiting for connections.

### 4. Play the Game

The client is a single HTML file. You cannot just open it directly in the browser (`file:///...`) because browsers have security restrictions. You need to serve it via a simple local web server.

Python has a built-in one that is perfect for this. In a **new terminal window** (leave the game server running), navigate to your project directory and run:

```
python -m http.server

```

Now, open your web browser and go to:

**http://localhost:8000**

You will see the "Cosmic Dodge" login screen. Enter a name, click "Join," and start playing! Open multiple tabs or windows to simulate multiple players.