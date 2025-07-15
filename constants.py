# --- Game Screen Dimensions ---
WIDTH, HEIGHT = 800, 600

# --- Game Update Rate ---
# 60 updates per second for lower latency
GAME_TICK_RATE = 1 / 60.0

# --- Player Properties ---
PLAYER_RADIUS = 15
# A higher value makes the ship move towards the cursor faster
PLAYER_ACCELERATION = 0.4

# --- Asteroid Properties ---
ASTEROID_SPAWN_INTERVAL = 0.5  # Seconds
ASTEROID_RADIUS_MIN = 10       # The smallest possible asteroid radius
ASTEROID_RADIUS_MAX = 40       # The largest possible asteroid radius
# We'll calculate speed based on size. This is a base value.
# A higher value means all asteroids are generally faster.
ASTEROID_BASE_SPEED = 100

