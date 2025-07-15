import random
import uuid
from constants import *

class Player:
    """ Represents a player's ship in the game. """
    def __init__(self, websocket, name):
        self.websocket = websocket
        self.id = str(uuid.uuid4())
        self.name = name
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(100, HEIGHT - 100)
        self.target_x = self.x
        self.target_y = self.y
        self.radius = PLAYER_RADIUS
        self.is_alive = True

    def update(self):
        """ Move player towards the target (mouse) position. """
        if self.is_alive:
            self.x += (self.target_x - self.x) * PLAYER_ACCELERATION
            self.y += (self.target_y - self.y) * PLAYER_ACCELERATION

    def to_dict(self):
        """ Serialize player state to a dictionary for JSON. """
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "is_alive": self.is_alive,
        }

class Asteroid:
    """ Represents an asteroid. Now with variable size and speed! """
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = -ASTEROID_RADIUS_MAX # Start just off-screen
        # Assign a random size
        self.radius = random.randint(ASTEROID_RADIUS_MIN, ASTEROID_RADIUS_MAX)
        # Smaller asteroids are faster, bigger ones are slower
        self.speed = ASTEROID_BASE_SPEED / self.radius

    def update(self):
        """ Move asteroid downwards based on its speed. """
        self.y += self.speed

    def to_dict(self):
        """ Serialize asteroid state to a dictionary for JSON. """
        return {"x": self.x, "y": self.y, "radius": self.radius}

