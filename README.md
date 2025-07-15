# Cosmic Dodge - Real-time WebSocket Game

A real-time, multiplayer browser game where you pilot a spaceship and dodge a relentless onslaught of asteroids. The last player standing wins! This game is built with Python and WebSockets, perfect for playing with friends over a local network (LAN).

## ✨ Features

-   **Real-Time Multiplayer:** Play with multiple people on the same network.
    
-   **Simple & Fun:** Easy to learn, difficult to master. The objective is simply to survive.
    
-   **LAN Party Ready:** Designed to be easily hosted and joined on a local network.
    
-   **Round-Based Gameplay:** After a winner is decided, a new round automatically begins after a short cooldown.
    

## 🛠️ Technology Stack

-   **Server:** Python 3 with `asyncio` and the `websockets` library.
    
-   **Client:** HTML, CSS, and modern JavaScript (ES6+).

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
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

```

Install the required Python packages:

```
pip3 install -r requirements.txt

```

## 🎮 How to Play

### Hosting a Game

The "host" is the person who will run the Python server on their machine.

1.  **Find Your LAN IP Address:** You'll need this so other players can connect to you.
    
    -   **On Windows:** Open Command Prompt, type `ipconfig`, and look for the "IPv4 Address".
        
    -   **On macOS/Linux:** Open the Terminal, type `ifconfig | grep "inet "`, and find the local IP address (it usually starts with `192.168.` or `10.0.`).
        
2.  **Start the Server:** Navigate to the directory containing the game files in your terminal and run the server:
    
    ```
    python3 server.py
    
    ```
    
    You should see the message: `Server started on ws://0.0.0.0:8765`. The server is now running and waiting for players.
    

### Joining a Game

1.  **Open the Game:** The client cannot just open index.html directly in the browser (file:///...) because browsers have security restrictions. You need to serve it via a simple local web server.

Python has a built-in one that is perfect for this. In a new terminal window (leave the game server running), navigate to your project directory and run:
    ```
    python3 -m http.server
    ```

Now, open your web browser and go to: `http://localhost:8000`
    
2.  **Enter Details and Join:** You will see a login screen.
    
    -   In the **"Host IP Address"** field, enter the LAN IP address of the person hosting the game.
        
    -   Enter your name.
        
    -   Click **"Join Game"**.
        
3.  **Play!** Once joined, use your mouse to move your spaceship around the screen and dodge the falling asteroids. Good luck!