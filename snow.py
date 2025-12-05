import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPixmap, QIcon
import random
import math

class SnowWidget(QWidget):
    def __init__(self):
        super().__init__()
        # --- Crucial Wayland/KDE/Click-Through Setup ---
        
        # 1. Set the window flags. These flags tell the Wayland compositor 
        # that the window is frameless, stays on top, and ignores mouse input.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )
        # 2. Enable a fully transparent background (must be done before showing)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 3. Set the geometry to cover the entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.setWindowTitle("Snow Overlay")
        self.show()

        # --- Snow Data ---
        self.width = screen.width()
        self.height = screen.height()
        self.snowflakes = []
        self.init_snowflakes(100)
        self.tree_image = QPixmap("Tree.png")
        self.bobble_images = {
            "red": QPixmap("Red_bobble.png"),
            "green": QPixmap("Green_bobble.png"),
            "blue": QPixmap("Blue_bobble.png")
        }
        self.bobble_colors = list(self.bobble_images.keys())
        # List to hold currently falling bobbles
        self.bobbles = []
        self.max_falling_bobbles = 4 # The maximum allowed at any given time
        # Tree code
        self.max_trees = 5
        self.trees = []
        self.init_trees()
        
        # --- Animation Loop (60 FPS) ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_snow)
        self.timer.start(16) # ~60 FPS (1000ms / 60 frames)

    def init_snowflakes(self, count):
        for _ in range(count):
            self.snowflakes.append({
                "x": random.randint(0, self.width),
                "y": random.randint(-self.height, 0),
                "size": random.uniform(2.0, 5.0),
                "speed": random.uniform(1.0, 3.0),
                "wobble": random.uniform(0, 100)
            })
    def init_trees(self):
        """Initializes a fixed number of trees with random positions."""
        for _ in range(self.max_trees):
            self.trees.append({
                "x": random.randint(0, self.width),
                "y": self.height - random.randint(50, 200), # Place trees near the bottom
                "visible": True,
                "scale": random.uniform(0.15, 0.35) # For variation in size
            })
    def update_snow(self):
        spawn_chance = 0.005 # 0.5% chance per frame to spawn a new bobble
        if len(self.bobbles) < self.max_falling_bobbles and random.random() < spawn_chance:
            
            # Choose a random color
            color = random.choice(self.bobble_colors)
            
            # Define a bobble that starts off-screen (top)
            self.bobbles.append({
                "color": color,
                "x": random.randint(0, self.width),
                "y": -50, # Start above the top edge
                "speed": random.uniform(3.0, 6.0),
                "size": random.uniform(0.1, 0.2) # Scale them slightly
            })

        # 2. Move Existing Bobbles and Remove when off-screen
        bobbles_to_keep = []
        for bobble in self.bobbles:
            bobble["y"] += bobble["speed"]
            
            # Check if bobble is still on screen (bottom edge)
            if bobble["y"] < self.height:
                bobbles_to_keep.append(bobble)
        
        self.bobbles = bobbles_to_keep
        for flake in self.snowflakes:
            flake["y"] += flake["speed"]
            # Add wind/wobble effect using sine wave
            flake["x"] += math.sin(flake["y"] / 50 + flake["wobble"]) * 0.5
            
            # Reset if off screen
            if flake["y"] > self.height:
                flake["y"] = random.randint(-50, -10)
                flake["x"] = random.randint(0, self.width)
        
        if random.random() < 0.01: # 1% chance per frame (adjust for speed)
            # Pick a random tree index
            tree_index = random.randint(0, self.max_trees - 1)
            
            # Toggle its visibility
            self.trees[tree_index]["visible"] = not self.trees[tree_index]["visible"]
        # This triggers the paintEvent to redraw the window
        self.update() 

    def paintEvent(self, event):
        # QPainter handles all drawing for Qt widgets
        painter = QPainter(self)
        
        # 1. Set the background to fully transparent (Qt handles the compositing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        for bobble in self.bobbles:
            pixmap = self.bobble_images.get(bobble["color"])
            
            if pixmap and not pixmap.isNull():
                # Calculate scaled dimensions
                width = pixmap.width() * bobble["size"]
                height = pixmap.height() * bobble["size"]
                
                # Draw the bobble
                painter.drawPixmap(
                    int(bobble["x"] - width / 2),
                    int(bobble["y"]),
                    int(width), int(height),
                    pixmap
                )
        for tree in self.trees:
            if tree["visible"]:
                if not self.tree_image.isNull():
                    # Draw image if loaded
                    width = self.tree_image.width() * tree["scale"]
                    height = self.tree_image.height() * tree["scale"]
                    painter.drawPixmap(tree["x"] - width / 2, # Center the tree drawing
                                       tree["y"] - height,
                                       width, height, 
                                       self.tree_image)
                else:
                    # Fallback: Draw a simple green triangle if image failed to load
                    painter.setBrush(QColor(0, 100, 0)) # Dark Green
                    painter.setPen(Qt.PenStyle.NoPen)
                    
                    # Draw a triangle (simple tree shape)
                    points = [
                        QPointF(tree["x"], tree["y"] - 100 * tree["scale"]),  # Top point
                        QPointF(tree["x"] - 50 * tree["scale"], tree["y"]),   # Bottom left
                        QPointF(tree["x"] + 50 * tree["scale"], tree["y"])    # Bottom right
                    ]
                    painter.drawPolygon(points)
        # 2. Draw Snowflakes
        # White color (255, 255, 255) with 80% opacity (204)
        snowflake_color = QColor(255, 255, 255, 204)
        
        # No outline (Pen) and use the color for the fill (Brush)
        painter.setPen(Qt.PenStyle.NoPen) 
        painter.setBrush(snowflake_color)
        
        for flake in self.snowflakes:
            # Draw a circle (ellipse with equal width/height)
            rect = QRectF(
                flake["x"] - flake["size"],
                flake["y"] - flake["size"],
                flake["size"] * 2,
                flake["size"] * 2
            )
            painter.drawEllipse(rect)


if __name__ == "__main__":
    # Ensure only one instance of QApplication is created
    app = QApplication(sys.argv)
    icon_path = "Tree.png"
    try:
        app_icon = QIcon(icon_path)
        
        if not app_icon.isNull():
            # --- 2. Apply the icon to the entire application ---
            app.setWindowIcon(app_icon)
        else:
            print(f"Warning: Could not load icon file at {icon_path}")
            
    except Exception as e:
        print(f"Error loading icon: {e}")
    win = SnowWidget()
    
    # Run the application event loop
    sys.exit(app.exec())
