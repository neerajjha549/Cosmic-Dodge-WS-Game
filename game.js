document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const canvas = document.getElementById('game-canvas');
    const ctx = canvas.getContext('2d');
    const loginOverlay = document.getElementById('login-overlay');
    const ipInput = document.getElementById('ip-input'); // Get IP input field
    const nameInput = document.getElementById('name-input');
    const joinButton = document.getElementById('join-button');
    const notifications = document.getElementById('notifications');

    // --- WebSocket ---
    let socket;
    let myPlayerId = null;

    // --- Game State ---
    let players = [];
    let asteroids = [];
    let gameInfo = {};

    // --- Utility Functions ---

    /**
     * Connects to the WebSocket server and sets up event listeners.
     * @param {string} ipAddress The IP address of the server to connect to.
     */
    function connect(ipAddress) {
        // Construct the WebSocket URL using the provided IP address
        const wsUrl = `ws://${ipAddress}:8765`;
        showNotification(`Connecting to ${wsUrl}...`);
        
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('Connected to server');
            // Hide login and show game
            loginOverlay.style.display = 'none';
            // Send join message
            const playerName = nameInput.value || 'Anonymous';
            socket.send(JSON.stringify({
                type: 'join',
                name: playerName
            }));
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        socket.onclose = () => {
            console.log('Disconnected from server');
            showNotification('Disconnected from the server.');
            loginOverlay.style.display = 'flex';
        };

        socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            showNotification(`Could not connect to ${ipAddress}. Check the IP and firewall.`);
            loginOverlay.style.display = 'flex';
        };
    }

    /**
     * Handles incoming messages from the server.
     * @param {object} data The message data from the server.
     */
    function handleServerMessage(data) {
        if (data.type === 'game_state') {
            players = data.players;
            asteroids = data.asteroids;
            gameInfo = data.game_info;
        } else if (data.type === 'welcome') {
            myPlayerId = data.player_id;
        } else if (data.type === 'notification') {
            showNotification(data.message);
        }
    }

    /**
     * Displays a temporary notification on the screen.
     * @param {string} message The text to display.
     */
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notifications.appendChild(notification);

        // Automatically remove the notification after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }


    // --- Rendering ---

    /**
     * Draws a player ship on the canvas.
     * @param {object} player The player object to draw.
     */
    function drawPlayer(player) {
        if (!player.is_alive) return;

        // The player's own ship is a different color
        ctx.fillStyle = player.id === myPlayerId ? '#4a90e2' : '#f5a623';
        
        ctx.beginPath();
        ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw player name
        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(player.name, player.x, player.y + player.radius + 15);
    }

    /**
     * Draws an asteroid on the canvas.
     * @param {object} asteroid The asteroid object to draw.
     */
    function drawAsteroid(asteroid) {
        ctx.fillStyle = '#9b9b9b'; // Grey color for asteroids
        ctx.beginPath();
        ctx.arc(asteroid.x, asteroid.y, asteroid.radius, 0, Math.PI * 2);
        ctx.fill();
    }
    
    /**
     * Draws the main game status text (e.g., winner announcement).
     */
    function drawGameStatus() {
        if (gameInfo.status === 'finished') {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.font = '50px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const winnerText = gameInfo.winner ? `${gameInfo.winner} Wins!` : "Round Over!";
            ctx.fillText(winnerText, canvas.width / 2, canvas.height / 2);
            ctx.font = '20px Arial';
            ctx.fillText('Next round starting soon...', canvas.width / 2, canvas.height / 2 + 50);
        } else if (gameInfo.status === 'waiting' && players.length < 1) {
             ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.font = '30px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText("Waiting for players...", canvas.width / 2, canvas.height / 2);
        }
    }


    /**
     * The main drawing loop, called on every animation frame.
     */
    function draw() {
        // Clear the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw a starfield background
        drawStarfield();

        // Draw game objects
        players.forEach(drawPlayer);
        asteroids.forEach(drawAsteroid);
        
        // Draw game status text
        drawGameStatus();

        // Request the next frame
        requestAnimationFrame(draw);
    }
    
    // --- Background Starfield ---
    let stars = [];
    function createStars() {
        for(let i=0; i<200; i++) {
            stars.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 1.5,
                alpha: Math.random()
            });
        }
    }
    function drawStarfield() {
        ctx.save();
        stars.forEach(star => {
            ctx.beginPath();
            ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${star.alpha})`;
            ctx.fill();
        });
        ctx.restore();
    }


    // --- Event Listeners ---

    // Send mouse position to the server
    canvas.addEventListener('mousemove', (event) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const rect = canvas.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;
            socket.send(JSON.stringify({
                type: 'input',
                mouse_pos: [mouseX, mouseY]
            }));
        }
    });

    // Handle join button click
    joinButton.addEventListener('click', () => {
        const ip = ipInput.value.trim();
        const name = nameInput.value.trim();

        if (!ip) {
            showNotification("Please enter the Host IP Address.");
            return;
        }
        if (!name) {
            showNotification("Please enter a name to join.");
            return;
        }
        connect(ip);
    });
    
    // Allow joining by pressing Enter in either input field
    ipInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            joinButton.click();
        }
    });
    nameInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            joinButton.click();
        }
    });


    // --- Initialization ---
    createStars();
    draw(); // Start the rendering loop
});

