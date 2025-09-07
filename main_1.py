from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time

_GLU_QUAD = gluNewQuadric()

def Gl_Depth(enable: bool):
    try:
        if enable:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)
    except Exception:
        pass

_APP_START = time.perf_counter()
def now_ms():
    return int((time.perf_counter() - _APP_START) * 1000)
player_life = 3
player_coins = 0
player_distance = 0

game_over = False
game_won = False

font = GLUT_BITMAP_HELVETICA_18

# Weather system
weather_state = "night"  
rain_drops = []

# Player position and movement
player_x = 0.0  
player_y = 0.0  
player_z = 0.0  
player_lane = 0  
player_target_x = 0.0  
player_is_jumping = False
player_is_sliding = False
player_slide_timer = 0
player_jump_timer = 0
player_jump_duration_frames = 150 # slightly longer jump duration
player_jump_height = 2 
player_jump_forward_distance = 1.5 
slide_hold = False  

# Camera and world
camera_view = "third_person"
camera_angle_h = 0
camera_height = 8
road_speed = 0.08  
track_segments = []
obstacles = []
coins = []
barriers = []
score = 0
distance_traveled = 0

# Power-ups (magnet)
magnet_active = False
magnet_duration_frames = 600  
magnet_timer_frames = 0

# Power-ups (lightning - invincibility)
lightning_active = False
lightning_duration_frames = 600  
lightning_timer_frames = 0
lightning_speed_multiplier = 1.6  # Speed boost while invincible

# Special power: limited bullets 
bullets_left = 3           
last_fire_ms = 0           
bullet_tracers = []       
is_playing = True


class Player:
    def __init__(self):
        self.update_from_globals()
        self.animation_timer = 0

    def update_from_globals(self):
        global player_x, player_y, player_z, player_lane, player_life, player_coins
        self.x = player_x
        self.y = player_y
        self.z = player_z
        self.lane = player_lane
        self.life = player_life
        self.coins = player_coins

    def push_to_globals(self):
        global player_x, player_y, player_z, player_lane, player_life, player_coins
        player_x = self.x
        player_y = self.y
        player_z = self.z
        player_lane = self.lane
        player_life = self.life
        player_coins = self.coins

    def draw_person(self):
        
        self.update_from_globals()
        self.animation_timer += 1
        
        # Visual cue for invincibility (no blending): switch to brighter colors
        global lightning_active
        alpha = 1.0
        
        glPushMatrix()
        # Read sliding state from global for visual pose
        global player_is_sliding, player_is_jumping
        if player_is_sliding:
            # Lower overall pose further and tilt more for a flatter slide profile
            glTranslatef(self.x, self.y + 0.35, self.z)
            glRotatef(-20, 1, 0, 0)
            
            # Torso (compressed)
            glPushMatrix()
            glColor3f(0.3, 0.75, 1.0) if lightning_active else glColor3f(0.2, 0.6, 0.9)
            glScalef(1.0, 0.55, 0.6)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Head closer to body
            glPushMatrix()
            glTranslatef(0, 0.5, 0)
            glColor3f(0.9, 0.7, 0.5)
            gluSphere(_GLU_QUAD, 0.35, 16, 16)
            glPopMatrix()
            
            # Arms tucked
            glPushMatrix()
            glTranslatef(-0.7, 0.15, 0)
            glRotatef(65, 1, 0, 0)
            glColor3f(0.9, 0.7, 0.5)
            glScalef(0.2, 0.6, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0.7, 0.15, 0)
            glRotatef(-65, 1, 0, 0)
            glColor3f(0.9, 0.7, 0.5)
            glScalef(0.2, 0.6, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Legs extended forward slightly
            glPushMatrix()
            glTranslatef(-0.35, -0.55, 0.12)
            glRotatef(-20, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.8)
            glScalef(0.25, 0.6, 0.25)
            glutSolidCube(1.0)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0.35, -0.55, 0.12)
            glRotatef(-20, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.8)
            glScalef(0.25, 0.6, 0.25)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Feet
            glPushMatrix()
            glTranslatef(-0.35, -0.92, 0.18)
            glColor3f(0.0, 0.0, 0.0)
            glScalef(0.3, 0.15, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0.35, -0.92, 0.18)
            glColor3f(0.0, 0.0, 0.0)
            glScalef(0.3, 0.15, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()

        elif player_is_jumping:
            # Jump pose: legs at ~45 degrees with body, hands raised upward
            glTranslatef(self.x, self.y + 1.0, self.z)

            # Torso (slight lean back)
            glPushMatrix()
            glColor3f(0.2, 0.6, 0.9)
            glRotatef(-10, 1, 0, 0)
            glScalef(0.8, 1.2, 0.4)
            glutSolidCube(1.0)
            glPopMatrix()

            # Head
            glPushMatrix()
            glTranslatef(0, 1.2, 0)
            glColor3f(0.9, 0.7, 0.5)
            gluSphere(_GLU_QUAD, 0.4, 16, 16)
            glPopMatrix()

            # Arms raised up (rotate about X to bring them overhead)
            glPushMatrix()
            glTranslatef(-0.6, 0.4, 0)
            glRotatef(-100, 1, 0, 0)
            glColor3f(0.9, 0.7, 0.5)
            glScalef(0.2, 0.8, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.6, 0.4, 0)
            glRotatef(-100, 1, 0, 0)
            glColor3f(0.9, 0.7, 0.5)
            glScalef(0.2, 0.8, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()

            # Legs both at ~45 degrees forward
            glPushMatrix()
            glTranslatef(-0.25, -0.8, 0)
            glRotatef(-45, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.8)
            glScalef(0.25, 0.9, 0.25)
            glutSolidCube(1.0)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.25, -0.8, 0)
            glRotatef(-45, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.8)
            glScalef(0.25, 0.9, 0.25)
            glutSolidCube(1.0)
            glPopMatrix()

            # Feet
            glPushMatrix()
            glTranslatef(-0.25, -1.4, 0.1)
            glColor3f(0.0, 0.0, 0.0)
            glScalef(0.3, 0.15, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.25, -1.4, 0.1)
            glColor3f(0.0, 0.0, 0.0)
            glScalef(0.3, 0.15, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()
        else:
            glTranslatef(self.x, self.y + 1.0, self.z)
            
            # Body (torso)
            glPushMatrix()
            glColor3f(0.2, 0.6, 0.9)  # Blue shirt
            glScalef(0.8, 1.2, 0.4)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Head
            glPushMatrix()
            glTranslatef(0, 1.2, 0)
            glColor3f(0.9, 0.7, 0.5)  # Skin color
            gluSphere(_GLU_QUAD, 0.4, 16, 16)
            glPopMatrix()
            
            # Arms (animated for running)
            arm_swing = math.sin(self.animation_timer * 0.3) * 30
            
            # Left arm
            glPushMatrix()
            glTranslatef(-0.6, 0.4, 0)
            glRotatef(arm_swing, 1, 0, 0)
            glColor3f(0.9, 0.7, 0.5)
            glScalef(0.2, 0.8, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Right arm
            glPushMatrix()
            glTranslatef(0.6, 0.4, 0)
            glRotatef(-arm_swing, 1, 0, 0)
            glColor3f(0.9, 0.7, 0.5)
            glScalef(0.2, 0.8, 0.2)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Legs (animated for running)
            leg_swing = math.sin(self.animation_timer * 0.4) * 20
            
            # Left leg
            glPushMatrix()
            glTranslatef(-0.25, -0.8, 0)
            glRotatef(leg_swing, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.8)  # Blue pants
            glScalef(0.25, 0.9, 0.25)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Right leg
            glPushMatrix()
            glTranslatef(0.25, -0.8, 0)
            glRotatef(-leg_swing, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.8)  # Blue pants
            glScalef(0.25, 0.9, 0.25)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Feet
            glPushMatrix()
            glTranslatef(-0.25, -1.4, 0.1)
            glColor3f(0.0, 0.0, 0.0)  # Black shoes
            glScalef(0.3, 0.15, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0.25, -1.4, 0.1)
            glColor3f(0.0, 0.0, 0.0)  # Black shoes
            glScalef(0.3, 0.15, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()
        
        glPopMatrix()
        
        # No blending used; nothing to restore

    def draw_info(self):
        # Sync from current global state before drawing HUD
        self.update_from_globals()
        global distance_traveled, magnet_active, magnet_timer_frames
        global lightning_active, lightning_timer_frames
        
        # Lives
        glColor3f(1, 0, 0)
        glRasterPos2f(10, 150)
        
            
        # Coins
        glColor3f(1, 1, 0)
        glRasterPos2f(10, 120)
        for ch in f"Coins: {self.coins}":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            
        # Distance
        glColor3f(0, 1, 0)
        glRasterPos2f(10, 90)
        for ch in f"Distance: {int(distance_traveled)}m":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            
        # Score
        glColor3f(1, 1, 1)
        glRasterPos2f(10, 60)
        for ch in f"Score: {score}":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        # Bullets remaining
        glColor3f(0.6, 0.8, 1.0)
        glRasterPos2f(10, 210)
        for ch in f"Bullets: {bullets_left}/3":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

        # Weather
        glColor3f(0.8, 0.8, 1)
        glRasterPos2f(10, 180)
        for ch in f"Weather: {weather_state.title()}":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        # Magnet status
        if magnet_active:
            glColor3f(1, 0.5, 0)
            glRasterPos2f(10, 30)
            secs = int(magnet_timer_frames / 60)
            for ch in f"Magnet: ON ({secs}s)":
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        # Lightning invincibility status
        if lightning_active:
            glColor3f(1, 1, 0.2)  # Bright yellow
            glRasterPos2f(10, 15)
            secs = int(lightning_timer_frames / 60)
            for ch in f"INVINCIBLE: ON ({secs}s)":
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


# Global player instance
player = Player()


class EndlessWorld:
    def __init__(self):
        self.track_segments = []
        self.obstacles = []
        self.coins = []
        self.barriers = []
        self.powerups = []  
        self.segment_length = 10
        # City background building segments (repeat like track)
        self.building_segments = []  
        # Rolling drum spawn timer (in frames)
        self.drum_timer = 720
        self.drum_interval_min = 700
        self.drum_interval_max = 1100
        # Magnet spawn timer (in frames)
        self.magnet_timer = 900
        self.magnet_interval_min = 900
        self.magnet_interval_max = 1500
        # Lightning spawn timer (in frames)
        self.lightning_timer = 300  # Start spawning after 5 seconds
        self.lightning_interval_min = 600  # 10 seconds minimum
        self.lightning_interval_max = 1200  # 20 seconds maximum
        
        self._last_timer_ms = None
        
        self.stars = self.generate_stars(160)
        self.generate_initial_world()

    def generate_initial_world(self):
        # Generate initial track segments
        for i in range(20):
            z_pos = i * self.segment_length
            self.track_segments.append(z_pos)
            # Create matching building segments on both sides
            self.generate_buildings_for_segment(z_pos)
            
            # Randomly place obstacles and coins
            if i > 3 and random.random() < 0.3:  
                lane = random.choice([-1, 0, 1])
                obstacle_type = random.choice(['barrier', 'low_barrier'])
                self.obstacles.append({
                    'x': lane * 3, 'z': z_pos, 'type': obstacle_type, 'y': 0
                })
            
            if i > 1 and random.random() < 0.4:  
                lane = random.choice([-1, 0, 1])
                self.coins.append({
                    'x': lane * 3, 'z': z_pos, 'y': 1.5
                })

    def draw_track(self):
        # Draw endless track
        glColor3f(0.3, 0.3, 0.3)
        # Draw far-to-near so depth test isn't required
        for segment_z in sorted(self.track_segments, reverse=True):
            # Main track surface
            glBegin(GL_QUADS)
            glVertex3f(-6, 0, segment_z)
            glVertex3f(6, 0, segment_z)
            glVertex3f(6, 0, segment_z + self.segment_length)
            glVertex3f(-6, 0, segment_z + self.segment_length)
            glEnd()
            
            # Lane dividers
            glColor3f(1, 1, 1)
            glBegin(GL_LINES)
            glVertex3f(-3, 0.01, segment_z)
            glVertex3f(-3, 0.01, segment_z + self.segment_length)
            glVertex3f(3, 0.01, segment_z)
            glVertex3f(3, 0.01, segment_z + self.segment_length)
            glEnd()
            glColor3f(0.3, 0.3, 0.3)

    def draw_obstacles(self):
        for obstacle in sorted(self.obstacles, key=lambda o: o.get('z', 0.0), reverse=True):
            glPushMatrix()
            glTranslatef(obstacle['x'], obstacle['y'], obstacle['z'])
            
            if obstacle['type'] == 'barrier':
                glPushMatrix()
                glColor3f(0.15, 0.4, 0.75)  
                glTranslatef(0.0, 0.15, 0.0)
                glScalef(1.6, 0.3, 0.7)
                glutSolidCube(1.0)
                glPopMatrix()

                # Main sign panel raised (leaves ~1.0 gap at bottom)
                glPushMatrix()
                glTranslatef(0.0, 2.0, 0.0)
                # Backing board
                glPushMatrix()
                glColor3f(0.95, 0.95, 0.95)
                glScalef(2.2, 2.0, 0.1)
                glutSolidCube(1.0)
                glPopMatrix()
                # Red chevrons (triangles) and thin frame
                glPushMatrix()
                glTranslatef(0.0, 0.0, 0.06)
                glScalef(2.0, 1.8, 1.0)
                glColor3f(0.85, 0.15, 0.15)
                glBegin(GL_TRIANGLES)
                glVertex3f(-0.9, 0.7, 0)
                glVertex3f(0.0, 0.2, 0)
                glVertex3f(0.9, 0.7, 0)
                glVertex3f(-0.9, 0.0, 0)
                glVertex3f(0.0, -0.5, 0)
                glVertex3f(0.9, 0.0, 0)
                glEnd()
                glColor3f(0.75, 0.1, 0.1)
                glBegin(GL_QUADS)
                glVertex3f(-1.0, 0.9, 0); glVertex3f(1.0, 0.9, 0); glVertex3f(1.0, 0.8, 0); glVertex3f(-1.0, 0.8, 0)
                glVertex3f(-1.0, -0.9, 0); glVertex3f(1.0, -0.9, 0); glVertex3f(1.0, -0.8, 0); glVertex3f(-1.0, -0.8, 0)
                glVertex3f(-1.0, -0.9, 0); glVertex3f(-0.9, -0.9, 0); glVertex3f(-0.9, 0.9, 0); glVertex3f(-1.0, 0.9, 0)
                glVertex3f(0.9, -0.9, 0); glVertex3f(1.0, -0.9, 0); glVertex3f(1.0, 0.9, 0); glVertex3f(0.9, 0.9, 0)
                glEnd()
                glPopMatrix()  
                glPopMatrix()  

            elif obstacle['type'] == 'low_barrier':
                glPushMatrix()
                glColor3f(0.55, 0.45, 0.8)  
                glTranslatef(0.0, 0.25, 0.0)
                glScalef(2.4, 0.5, 0.9)
                glutSolidCube(1.0)
                glPopMatrix()

                # Side supports (orange)
                def support(x):
                    glPushMatrix()
                    glColor3f(0.95, 0.55, 0.25)
                    glTranslatef(x, 1.0, 0.0)
                    glScalef(0.35, 2.0, 0.35)
                    glutSolidCube(1.0)
                    glPopMatrix()
                support(-0.9)
                support(0.9)

                # Horizontal plank (red with white stripes)
                glPushMatrix()
                glTranslatef(0.0, 1.6, 0.0)
                # base red slab
                glColor3f(0.9, 0.15, 0.15)
                glPushMatrix()
                glScalef(2.4, 0.4, 0.25)
                glutSolidCube(1.0)
                glPopMatrix()
                # white stripes as thin quads in front
                glPushMatrix()
                glTranslatef(0.0, 0.0, 0.14)
                glScalef(2.2, 0.35, 1.0)
                glColor3f(0.98, 0.98, 0.98)
                glBegin(GL_QUADS)
                # Three vertical white bars
                glVertex3f(-0.8, -0.5, 0); glVertex3f(-0.55, -0.5, 0); glVertex3f(-0.55, 0.5, 0); glVertex3f(-0.8, 0.5, 0)
                glVertex3f(-0.15, -0.5, 0); glVertex3f(0.10, -0.5, 0); glVertex3f(0.10, 0.5, 0); glVertex3f(-0.15, 0.5, 0)
                glVertex3f(0.55, -0.5, 0); glVertex3f(0.80, -0.5, 0); glVertex3f(0.80, 0.5, 0); glVertex3f(0.55, 0.5, 0)
                glEnd()
                glPopMatrix()
                # circular gray end caps
                glColor3f(0.75, 0.75, 0.8)
                glPushMatrix()
                glTranslatef(-1.05, 0.0, 0.14)
                gluSphere(_GLU_QUAD, 0.22, 14, 14)
                glPopMatrix()
                glPushMatrix()
                glTranslatef(1.05, 0.0, 0.14)
                gluSphere(_GLU_QUAD, 0.22, 14, 14)
                glPopMatrix()
                glPopMatrix()  # end plank

            elif obstacle['type'] == 'gap':
                # Skip rendering gaps to avoid black holes in the road
                pass

            elif obstacle['type'] == 'drum':
                # Rolling red petrol drum
                radius = obstacle.get('radius', 0.6)
                length = obstacle.get('length', 1.2)
                roll = obstacle.get('roll', 0.0)
                glPushMatrix()
                glTranslatef(0, radius, 0)
                glRotatef(90, 0, 1, 0)
                glRotatef(roll, 1, 0, 0)
                glColor3f(0.9, 0.1, 0.1)
                quad = gluNewQuadric()
                gluCylinder(quad, radius, radius, length, 32, 1)
                # ribs
                glColor3f(0.85, 0.08, 0.08)
                band_r = radius * 1.03
                band_len = 0.03
                glPushMatrix(); glTranslatef(0.2, 0, 0); gluCylinder(gluNewQuadric(), band_r, band_r, band_len, 24, 1); glPopMatrix()
                glPushMatrix(); glTranslatef(length * 0.5 - band_len * 0.5, 0, 0); gluCylinder(gluNewQuadric(), band_r, band_r, band_len, 24, 1); glPopMatrix()
                glPushMatrix(); glTranslatef(length - 0.2 - band_len, 0, 0); gluCylinder(gluNewQuadric(), band_r, band_r, band_len, 24, 1); glPopMatrix()
                # yellow caps + small plugs
                glPushMatrix(); glRotatef(90, 0, 1, 0); glColor3f(0.96, 0.85, 0.1); draw_filled_disc(radius, 32);
                glColor3f(0.1, 0.1, 0.1); glPushMatrix(); glTranslatef(radius*0.45, radius*0.2, 0.01); gluSphere(_GLU_QUAD, 0.05, 10, 10); glPopMatrix();
                glPushMatrix(); glTranslatef(-radius*0.25, -radius*0.3, 0.01); gluSphere(_GLU_QUAD, 0.035, 10, 10); glPopMatrix(); glPopMatrix()
                glPushMatrix(); glTranslatef(length, 0, 0); glRotatef(90, 0, 1, 0); glColor3f(0.96, 0.85, 0.1); draw_filled_disc(radius, 32); glPopMatrix()
                glPopMatrix()

            # Pop for this obstacle
            glPopMatrix()

    def draw_buildings(self):
        # Draw colorful low-poly buildings along both sides (far-to-near)
        for seg in sorted(self.building_segments, key=lambda s: s.get('z', 0.0), reverse=True):
            z = seg['z']
            # Left side buildings
            for b in seg['left']:
                glPushMatrix()
                glTranslatef(b['x'], b['h'] * 0.5, z + b['dz'])
                glColor3f(*b['color'])
                glScalef(b['w'], b['h'], b['d'])
                glutSolidCube(1.0)
                glPopMatrix()
            # Right side buildings
            for b in seg['right']:
                glPushMatrix()
                glTranslatef(b['x'], b['h'] * 0.5, z + b['dz'])
                glColor3f(*b['color'])
                glScalef(b['w'], b['h'], b['d'])
                glutSolidCube(1.0)
                glPopMatrix()

    def generate_buildings_for_segment(self, z_pos):
        # Build 3-5 buildings per side with varied sizes and colors
        def rand_color():
            palette = [
                (0.9, 0.4, 0.3),  # coral
                (0.2, 0.6, 0.9),  # sky blue
                (0.95, 0.8, 0.2), # yellow
                (0.5, 0.7, 0.3),  # greenish
                (0.8, 0.5, 0.8),  # lavender
                (0.9, 0.6, 0.2),  # orange
            ]
            return random.choice(palette)

        def make_side(x_center):
            count = random.randint(3, 5)
            buildings = []
            z_offsets = sorted([random.uniform(0.0, self.segment_length) for _ in range(count)])
            for dz in z_offsets:
                w = random.uniform(2.0, 3.0)
                d = random.uniform(2.0, 3.0)
                h = random.uniform(5.0, 10.0)
                # Slight jitter along X to vary facades
                x = x_center + random.uniform(-0.6, 0.6)
                buildings.append({'x': x, 'w': w, 'd': d, 'h': h, 'dz': dz, 'color': rand_color()})
            return buildings

        seg = {
            'z': z_pos,
            'left': make_side(-8.5),   # left row offset from road center
            'right': make_side(8.5),   # right row offset
        }
        self.building_segments.append(seg)
        # End generate_buildings_for_segment

    def get_difficulty(self):
        # Difficulty scales from 0.0 to 1.0 as distance grows
        # Reaches 1.0 around ~600 meters
        global distance_traveled
        return max(0.0, min(1.0, distance_traveled / 600.0))

    def generate_stars(self, count):
        # Create star positions high in the sky with per-star twinkle params
        stars = []
        for _ in range(count):
            x = random.uniform(-45.0, 45.0)
            y = random.uniform(15.0, 40.0)
            z = random.uniform(10.0, 140.0)
            size = random.uniform(1.5, 3.2)
            phase = random.uniform(0.0, math.tau if hasattr(math, 'tau') else 2*math.pi)
            speed = random.uniform(0.6, 1.6)
            stars.append({'x': x, 'y': y, 'z': z, 'size': size, 'phase': phase, 'speed': speed})
        return stars

    def draw_sky(self):
        # Render a twinkling starfield; very cheap using GL_POINTS
        # Manually manage state without glPushAttrib/glPopAttrib
        # No point smoothing (avoid glEnable)
        t = now_ms() / 1000.0
        # Important: cannot change glPointSize inside glBegin/End. Draw per-star.
        for s in self.stars:
            # Twinkle brightness 0.6..1.0
            b = 0.6 + 0.4 * abs(math.sin(t * s['speed'] + s['phase']))
            glColor3f(b, b, b)
            glPointSize(s['size'])
            glBegin(GL_POINTS)
            glVertex3f(s['x'], s['y'], s['z'])
            glEnd()
        # Nothing to restore

    def draw_day_sun(self):
        """Draw a simple sun in the sky for day weather."""
        from math import sin, cos, radians
        # Position the sun to the right-top area of the sky, at a far Z so it doesn't intersect world
        sun_x, sun_y, sun_z = 28.0, 26.0, 85.0
        radius = 4.0
        # Opaque sun (no blending)
        glColor3f(1.0, 0.93, 0.25)
        # Draw filled sun disc using triangles instead of triangle fan
        glBegin(GL_TRIANGLES)
        for a in range(0, 360, 8):
            x1 = sun_x + radius * cos(radians(a))
            y1 = sun_y + radius * sin(radians(a))
            x2 = sun_x + radius * cos(radians(a + 8))
            y2 = sun_y + radius * sin(radians(a + 8))
            glVertex3f(sun_x, sun_y, sun_z)
            glVertex3f(x1, y1, sun_z)
            glVertex3f(x2, y2, sun_z)
        glEnd()
        # Rays drawn as thin quads (simulate line width)
        glColor3f(1.0, 0.95, 0.3)
        thickness = 0.12
        for a in range(0, 360, 30):
            x1 = sun_x + (radius + 0.8) * cos(radians(a))
            y1 = sun_y + (radius + 0.8) * sin(radians(a))
            x2 = sun_x + (radius + 3.0) * cos(radians(a))
            y2 = sun_y + (radius + 3.0) * sin(radians(a))
            dx = x2 - x1
            dy = y2 - y1
            L = math.hypot(dx, dy) or 1.0
            nx = -dy / L * thickness
            ny = dx / L * thickness
            glBegin(GL_QUADS)
            glVertex3f(x1 - nx, y1 - ny, sun_z + 0.01)
            glVertex3f(x1 + nx, y1 + ny, sun_z + 0.01)
            glVertex3f(x2 + nx, y2 + ny, sun_z + 0.01)
            glVertex3f(x2 - nx, y2 - ny, sun_z + 0.01)
            glEnd()
        # No blending used

    def draw_birds(self):
        """Draw a small flock of stylized birds (V shapes) gliding across the sky."""
        # Animate horizontal position over time for a gentle drift
        t = now_ms() / 1000.0
        base_x = -35.0 + (t * 5.0) % 80.0  # loops across -35..45
        base_y = 20.0
        z = 90.0
        glColor3f(0.15, 0.15, 0.15)
        thickness = 0.08
        # Each bird is two short segments; draw each as a thin quad
        for i in range(5):
            bx = base_x + i * 4.5
            by = base_y + (i % 2) * 1.0
            wing = 1.6
            drop = 0.6
            # left wing segment endpoints
            x1, y1 = (bx - wing, by)
            x2, y2 = (bx, by - drop)
            dx, dy = (x2 - x1), (y2 - y1)
            L = math.hypot(dx, dy) or 1.0
            nx, ny = (-dy / L * thickness, dx / L * thickness)
            glBegin(GL_QUADS)
            glVertex3f(x1 - nx, y1 - ny, z)
            glVertex3f(x1 + nx, y1 + ny, z)
            glVertex3f(x2 + nx, y2 + ny, z)
            glVertex3f(x2 - nx, y2 - ny, z)
            glEnd()
            # right wing segment endpoints
            x1, y1 = (bx, by - drop)
            x2, y2 = (bx + wing, by)
            dx, dy = (x2 - x1), (y2 - y1)
            L = math.hypot(dx, dy) or 1.0
            nx, ny = (-dy / L * thickness, dx / L * thickness)
            glBegin(GL_QUADS)
            glVertex3f(x1 - nx, y1 - ny, z)
            glVertex3f(x1 + nx, y1 + ny, z)
            glVertex3f(x2 + nx, y2 + ny, z)
            glVertex3f(x2 - nx, y2 - ny, z)
            glEnd()

    def draw_coins(self):
        # Draw far-to-near
        for coin in sorted(self.coins, key=lambda c: c.get('z', 0.0), reverse=True):
            glPushMatrix()
            glTranslatef(coin['x'], coin['y'], coin['z'])
            glRotatef(now_ms() * 0.5, 0, 1, 0)  # Rotating coin
            glColor3f(1.0, 1.0, 0.0)  # Gold color
            # Flat coin (no hole): filled disc on local XY plane
            draw_filled_disc(0.35, 32)
            glPopMatrix()

    def draw_powerups(self):
        # Draw magnet symbol power-up (far-to-near)
        for p in sorted(self.powerups, key=lambda x: x.get('z', 0.0), reverse=True):
            if p['type'] == 'magnet':
                glPushMatrix()
                # Floating bob and gentle spin
                t = now_ms() / 1000.0
                bob = math.sin(t * 2.5) * 0.2
                glTranslatef(p['x'], p['y'] + bob, p['z'])
                glRotatef(now_ms() * 0.05, 0, 1, 0)
                glRotatef(90, 1, 0, 0)
                # U-shaped magnet: red body with golden tips
                # left leg (red)
                glColor3f(0.9, 0.15, 0.1)
                glPushMatrix()
                glTranslatef(-0.28, 0.0, 0)
                glScalef(0.22, 0.85, 0.22)
                glutSolidCube(1.0)
                glPopMatrix()
                # right leg (red)
                glPushMatrix()
                glTranslatef(0.28, 0.0, 0)
                glScalef(0.22, 0.85, 0.22)
                glutSolidCube(1.0)
                glPopMatrix()
                # top bridge (red)
                glPushMatrix()
                glTranslatef(0.0, 0.45, 0)
                glScalef(0.75, 0.22, 0.22)
                glutSolidCube(1.0)
                glPopMatrix()
                # golden tips
                glColor3f(1.0, 0.85, 0.2)
                glPushMatrix()
                glTranslatef(-0.28, -0.47, 0)
                glScalef(0.22, 0.18, 0.22)
                glutSolidCube(1.0)
                glPopMatrix()
                glPushMatrix()
                glTranslatef(0.28, -0.47, 0)
                glScalef(0.22, 0.18, 0.22)
                glutSolidCube(1.0)
                glPopMatrix()
                glPopMatrix()
                
            elif p['type'] == 'lightning':
                glPushMatrix()
                # Floating bob and gentle spin
                t = now_ms() / 1000.0
                bob = math.sin(t * 3.0) * 0.25
                glTranslatef(p['x'], p['y'] + bob, p['z'])
                glRotatef(now_ms() * 0.1, 0, 1, 0)

                # Draw a glowing 5-point star (no circle)
                # Create star vertices (10-point path alternating outer/inner radii)
                r_outer = 0.55
                r_inner = 0.23
                pts = []
                for i in range(10):
                    ang = i * math.pi / 5.0  # 36 degrees per step
                    r = r_outer if (i % 2 == 0) else r_inner
                    x = r * math.sin(ang)
                    y = r * math.cos(ang)
                    pts.append((x, y))

                # Opaque star body (no blending) using triangles (no triangle fan)
                glColor3f(1.0, 0.95, 0.2)
                glBegin(GL_TRIANGLES)
                for i in range(len(pts)):
                    x1, y1 = pts[i]
                    x2, y2 = pts[(i + 1) % len(pts)]
                    glVertex3f(0.0, 0.0, 0.0)
                    glVertex3f(x1, y1, 0.01)
                    glVertex3f(x2, y2, 0.01)
                glEnd()

                # Thin orange outline for visibility (simulate line width with quads)
                glColor3f(0.98, 0.55, 0.1)
                thickness = 0.06
                for i in range(len(pts)):
                    x1, y1 = pts[i]
                    x2, y2 = pts[(i + 1) % len(pts)]
                    dx = x2 - x1
                    dy = y2 - y1
                    L = math.hypot(dx, dy) or 1.0
                    nx = -dy / L * thickness
                    ny = dx / L * thickness
                    glBegin(GL_QUADS)
                    glVertex3f(x1 - nx, y1 - ny, 0.02)
                    glVertex3f(x1 + nx, y1 + ny, 0.02)
                    glVertex3f(x2 + nx, y2 + ny, 0.02)
                    glVertex3f(x2 - nx, y2 - ny, 0.02)
                    glEnd()

                glPopMatrix()

    def update_world(self):
        global road_speed, distance_traveled, player_coins, score, player_is_jumping, player_jump_duration_frames, player_jump_forward_distance
        global magnet_active, magnet_timer_frames, magnet_duration_frames
        global lightning_active, lightning_timer_frames, lightning_duration_frames
        
        # Real-time delta (ms) for time-accurate timers
        current_ms = now_ms()
        if self._last_timer_ms is None:
            self._last_timer_ms = current_ms
        dt_ms = max(0, current_ms - self._last_timer_ms)
        self._last_timer_ms = current_ms
        # Convert elapsed time to 60fps 'frame units' so existing frame-based values still work
        frame_units = dt_ms / (1000.0 / 60.0)

        # Apply extra scroll while jumping to simulate slight forward motion
        jump_extra = (player_jump_forward_distance / player_jump_duration_frames) if player_is_jumping else 0.0
        # Speed boost while lightning is active
        base_speed = road_speed * (lightning_speed_multiplier if lightning_active else 1.0)
        step = base_speed + jump_extra

        # Spawn rolling drum periodically ahead (shorter intervals as difficulty rises)
        self.drum_timer -= frame_units
        if self.drum_timer <= 0:
            # Only spawn if no other drum is currently present in scene (z > -10)
            drum_present = any((o.get('type') == 'drum' and o.get('z', 0) > -10) for o in self.obstacles)
            if not drum_present:
                lane = random.choice([-1, 0, 1])
                radius = 0.7
                length = 1.4
                spawn_z = max(self.track_segments) + 40 if self.track_segments else 80
                # Give the drum its own forward speed so it comes at the player like a car
                forward_speed = random.uniform(0.06, 0.14)
                self.obstacles.append({'x': lane * 3, 'z': spawn_z, 'y': 0.0, 'type': 'drum', 'radius': radius, 'length': length, 'roll': 0.0, 'forward_speed': forward_speed})
            # Reset drum timer with difficulty-based interval shrinking
            diff = self.get_difficulty()
            min_iv = int(self.drum_interval_min * (1.0 - 0.5 * diff))
            max_iv = int(self.drum_interval_max * (1.0 - 0.5 * diff))
            # enforce sensible bounds
            min_iv = max(300, min_iv)
            max_iv = max(min_iv + 100, max_iv)
            self.drum_timer = random.randint(min_iv, max_iv)

        # Move world toward player
        for i in range(len(self.track_segments)):
            self.track_segments[i] -= step
        
        # Move building segments to scroll with the road
        for seg in self.building_segments:
            seg['z'] -= step
        
        for obstacle in self.obstacles[:]:
            # Base scroll toward player
            dz = step
            # Drums have extra oncoming velocity to simulate rolling from the front like cars
            if obstacle['type'] == 'drum':
                dz += obstacle.get('forward_speed', 0.0)
            obstacle['z'] -= dz
            # Update rolling rotation for drum using actual moved distance
            if obstacle['type'] == 'drum':
                r = obstacle.get('radius', 0.6)
                delta_angle = (dz / (2 * math.pi * r)) * 360.0
                obstacle['roll'] = (obstacle.get('roll', 0.0) + delta_angle) % 360.0
            if obstacle['z'] < -10:
                self.obstacles.remove(obstacle)
                
        for coin in self.coins[:]:
            coin['z'] -= step
            if coin['z'] < -10:
                self.coins.remove(coin)

        # Spawn magnet power-up periodically ahead
        self.magnet_timer -= frame_units
        if self.magnet_timer <= 0:
            lane = random.choice([-1, 0, 1])
            spawn_z = max(self.track_segments) + 30 if self.track_segments else 70
            self.powerups.append({'type': 'magnet', 'x': lane * 3, 'y': 1.5, 'z': spawn_z})
            self.magnet_timer = random.randint(self.magnet_interval_min, self.magnet_interval_max)

        # Spawn lightning power-up periodically ahead
        self.lightning_timer -= frame_units
        if self.lightning_timer <= 0:
            lane = random.choice([-1, 0, 1])
            spawn_z = max(self.track_segments) + 35 if self.track_segments else 75
            self.powerups.append({'type': 'lightning', 'x': lane * 3, 'y': 1.5, 'z': spawn_z})
            self.lightning_timer = random.randint(self.lightning_interval_min, self.lightning_interval_max)

        # Move power-ups toward player
        for p in self.powerups[:]:
            p['z'] -= step
            if p['z'] < -10:
                self.powerups.remove(p)
        
        # Tick down magnet timer if active
        if magnet_active:
            magnet_timer_frames -= frame_units
            if magnet_timer_frames <= 0:
                magnet_active = False
        
        # Tick down lightning timer if active
        if lightning_active:
            lightning_timer_frames -= frame_units
            if lightning_timer_frames <= 0:
                lightning_active = False
        
        # Generate new segments ahead
        if len(self.track_segments) > 0 and self.track_segments[-1] < 100:
            new_z = self.track_segments[-1] + self.segment_length
            self.track_segments.append(new_z)
            # Also create new building segment
            self.generate_buildings_for_segment(new_z)
            
            # Add new obstacles and coins with difficulty 
            diff = self.get_difficulty()
            # Base 25% + up to +35% with difficulty 
            obstacle_chance = 0.25 + 0.35 * diff
            if random.random() < obstacle_chance:
                # sometimes 2 obstacles in different lanes
                spawn_count = 1 + (1 if random.random() < 0.25 * diff else 0)
                used_lanes = set()
                for _ in range(spawn_count):
                    avail_lanes = [l for l in [-1, 0, 1] if l not in used_lanes]
                    if not avail_lanes:
                        break
                    lane = random.choice(avail_lanes)
                    used_lanes.add(lane)
                    # Remove 'gap' to avoid black holes in the road
                    obstacle_type = random.choice(['barrier', 'low_barrier'])
                    self.obstacles.append({
                        'x': lane * 3, 'z': new_z, 'type': obstacle_type, 'y': 0
                    })
            
            # Slightly reduce coin chance as difficulty rises
            coin_chance = 0.6 - 0.2 * diff
            if random.random() < coin_chance:
                lane = random.choice([-1, 0, 1])
                self.coins.append({
                    'x': lane * 3, 'z': new_z, 'y': 1.5
                })
        
        # Remove old segments
        self.track_segments = [z for z in self.track_segments if z > -20]
        self.building_segments = [seg for seg in self.building_segments if seg['z'] > -30]
        
        # Update distance (include jump extra movement)
        distance_traveled += step
        
        # Check coin collection
        self.check_coin_collection()
        # Check power-up collection
        self.check_powerup_collection()
        
        # Check obstacle collision
        self.check_obstacle_collision()
    
    def check_coin_collection(self):
        global player_x, player_y, player_z, player_coins, score
        for coin in self.coins[:]:
            # If magnet is active, attract coins toward player
            if magnet_active:
                
                if abs(coin['z'] - player_z) < 8.0:
                    # strong lateral pull toward player's lane
                    dx = player_x - coin['x']
                    coin['x'] += max(min(dx, 0.7), -0.7)  
                    # gentle pull in Z to close distance
                    dz = player_z - coin['z']
                    coin['z'] += max(min(dz, 0.25), -0.25)
                    #coin toward head height
                    dy = (player_y + 1.0) - coin['y']
                    coin['y'] += max(min(dy, 0.3), -0.3)
                else:
                    # pull coins toward alignment
                    ax = player_x - coin['x']
                    ay = (player_y + 1.0) - coin['y']
                    az = player_z - coin['z']
                    dist = math.sqrt(ax*ax + ay*ay + az*az) + 1e-6
                    pull = min(0.25, dist)
                    coin['x'] += (ax / dist) * pull
                    coin['y'] += (ay / dist) * pull
                    coin['z'] += (az / dist) * pull
            if (abs(coin['x'] - player_x) < 1.0 and 
                abs(coin['z'] - player_z) < 1.0 and
                abs(coin['y'] - (player_y + 1.0)) < 1.0):
                self.coins.remove(coin)
                player_coins += 1
                score += 10

    def check_powerup_collection(self):
        global player_x, player_y, player_z, magnet_active, magnet_timer_frames, magnet_duration_frames
        global lightning_active, lightning_timer_frames, lightning_duration_frames
        for p in self.powerups[:]:
            if p['type'] == 'magnet':
                if (abs(p['x'] - player_x) < 1.2 and
                    abs(p['z'] - player_z) < 1.2 and
                    abs(p['y'] - (player_y + 1.0)) < 1.2):
                    self.powerups.remove(p)
                    magnet_active = True
                    magnet_timer_frames = magnet_duration_frames
            elif p['type'] == 'lightning':
                if (abs(p['x'] - player_x) < 1.2 and
                    abs(p['z'] - player_z) < 1.2 and
                    abs(p['y'] - (player_y + 1.0)) < 1.2):
                    self.powerups.remove(p)
                    lightning_active = True
                    lightning_timer_frames = lightning_duration_frames
    
    def check_obstacle_collision(self):
        global player_x, player_y, player_z, player_life, game_over, player_is_jumping, player_is_sliding
        global lightning_active
        
        for obstacle in self.obstacles:
            if (abs(obstacle['x'] - player_x) < 1.2 and 
                abs(obstacle['z'] - player_z) < 1.0):
                # If lightning power is active, ignore this collision
                if lightning_active:
                    continue
                
                if obstacle['type'] == 'barrier':
                    # Elevated red barrier: must slide under
                    if not player_is_sliding:
                        game_over = True
                elif obstacle['type'] == 'low_barrier':
                    # Short brown barrier: must jump over
                    if not player_is_jumping or player_y < 1.0:
                        game_over = True
                elif obstacle['type'] == 'drum':
                    # must jump over sufficiently high
                    required = obstacle.get('radius', 0.6) * 0.8
                    # Make horizontal hitbox depend on drum radius to match visual size
                    half_width = obstacle.get('radius', 0.6) + 0.25
                    if abs(obstacle['x'] - player_x) < half_width:
                        if not player_is_jumping or player_y < required:
                            game_over = True
                elif obstacle['type'] == 'gap':
                    # No game over for gaps by request
                    pass

# Global world instance
world = EndlessWorld()

def zone_check(x1, y1, x2, y2):
    # checks in which zone the current point is at
    dx = x2 - x1
    dy = y2 - y1

    if abs(dx) >= abs(dy): 
        if dx >= 0 and dy >= 0:
            return 0 #zone 0
        elif dx >= 0 and dy <= 0:
            return 7 #zone 7
        elif dx <= 0 and dy >= 0:
            return 3 #zone 3
        elif dx <= 0 and dy <= 0:
            return 4 #zone 4
    else:
        if dx >= 0 and dy >= 0:
            return 1 #zone 1
        elif dx >= 0 and dy <= 0:
            return 6 #zone 6
        elif dx <= 0 and dy >= 0:
            return 2 #zone 2
        elif dx <= 0 and dy <= 0:
            return 5 #zone 5

def zone_m_to_zone_zero(x1, y1, x2, y2, zone):
    #converts any other zone points to zone 0
    if zone == 0:
        return x1, y1, x2, y2
    elif zone == 1:
        return y1, x1, y2, x2
    elif zone == 2:
        return y1, -x1, y2, -x2
    elif zone == 3:
        return -x1, y1, -x2, y2
    elif zone == 4:
        return -x1, -y1, -x2, -y2
    elif zone == 5:
        return -y1, -x1, -y2, -x2
    elif zone == 6:
        return -y1, x1, -y2, x2
    elif zone == 7:
        return x1, -y1, x2, -y2
    
def zone_zero_to_zone_m(x,y,zone): 
    #coverts the zone 0 to its original zone
    if zone == 1:
        return y, x
    elif zone == 2:
        return -y, x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return y, -x
    elif zone == 7:
        return x, -y
    elif zone == 0:
        return x, y

def midpoint_line(x1, y1, x2, y2):   
    zone = zone_check(x1, y1, x2, y2) #finds the zone 
    x1, y1, x2, y2 = zone_m_to_zone_zero(x1, y1, x2, y2, zone)#convert the mth zone coordinates to zone 0
    
    dx = x2 - x1
    dy = y2 - y1
    d = (2 * dy) - dx
    incE = 2 * dy #East
    incNE = 2 * (dy - dx) #North East
    x, y = x1, y1
    glPointSize(3)
    glBegin(GL_POINTS)
    while x <= x2:  #X2 always increases
        conX, conY = zone_zero_to_zone_m(x, y, zone) #converts back the 0th zone to original zone 
        
        glVertex2f(conX, conY)
        if d >= 0: # pixel moves to north east
            d += incNE
            y += 1
        else: # pixel moves to east
            d += incE
        x += 1
    glEnd()

class BOARD:
    def draw_quit(self, a, b):
        glColor3f(1, 0, 0)
        midpoint_line(a - 15, b - 15, a + 15, b + 15)
        midpoint_line(a - 15, b + 15, a + 15, b - 15)

    def draw_back(self, a, b):
        glColor3f(0, 0, 1)
        midpoint_line(a + 25, b, a - 15, b)  # horizontal line
        midpoint_line(a + 5, b + 15, a - 15, b)  # upper
        midpoint_line(a + 5, b - 15, a - 15, b)  # lower

    def draw_pause_play(self, a, b):
        global is_playing
        if is_playing == True:  # unpause
            glColor3f(0.0, 1.0, 0.0)
            midpoint_line(a - 10, b + 15, a - 10, b - 15)
            midpoint_line(a + 10, b + 15, a + 10, b - 15)
        else:  # pause
            glColor3f(1.0, 0.75, 0.0)
            midpoint_line(a - 10, b + 15, a - 10, b - 15)
            midpoint_line(a - 10, b + 15, a + 10, b)  # up
            midpoint_line(a - 10, b - 15, a + 10, b)  # below

    def draw_buttons(self):
        self.draw_quit(950, 750)
        self.draw_back(50, 750)
        self.draw_pause_play(500, 750)

# Global board instance
board = BOARD()

def restart_game():
    global player_x, player_y, player_z, player_lane, player_target_x, player_life, player_coins
    global score, game_over, is_playing, distance_traveled
    global camera_view, camera_angle_h, camera_height
    global player_jump_velocity, player_is_jumping, player_is_sliding, player_slide_timer
    global world, road_speed, magnet_active, lightning_active
    global magnet_timer_frames, lightning_timer_frames, weather_state
    global bullets_left, last_fire_ms
    global bullet_tracers
   
    player_x = 0.0
    player_y = 0.0
    player_z = 0.0
    player_lane = 0
    player_target_x = 0.0
    player_life = 3
    player_coins = 0
    
    score = 0
    distance_traveled = 0
    game_over = False
    is_playing = True  
    camera_view = "third_person"
    camera_angle_h = 0
    camera_height = 8
    
    player_jump_velocity = 0.0
    player_is_jumping = False
    player_is_sliding = False
    player_slide_timer = 0
    
    magnet_active = False
    lightning_active = False
    magnet_timer_frames = 0
    lightning_timer_frames = 0
    
    # Reset world
    world = EndlessWorld()  
    
    # Keep current weather state
    # weather_state remains unchanged
    
    # Ensure constant speed after restart
    road_speed = 0.08
    
    # Reload special power
    bullets_left = 3
    last_fire_ms = 0
    bullet_tracers = []

def fire_bullet():
    """Fire a bullet forward in the current lane and remove the nearest obstacle.
    Limited to 3 uses per run. A small debounce prevents rapid repeat when key is held.
    """
    global bullets_left, last_fire_ms, world, player_lane, player_z, score
    # Must have bullets and not be game over (checked by caller's flow already)
    if bullets_left <= 0:
        return
    # Debounce: at least 200ms between shots
    now = now_ms()
    if (now - last_fire_ms) < 200:
        return

    # Consider obstacles directly in player's lane and slightly ahead
    target_x = player_lane * 3.0
    # Include rolling drum so bullets can destroy it too
    allowed_types = {"barrier", "gap", "low_barrier", "drum"}
    candidates = [
        o for o in world.obstacles
        if (o.get('type') in allowed_types)
        and (abs(o.get('x', 9999.0) - target_x) < 0.11)
        and (o.get('z', -9999.0) > player_z - 0.5)
        and (o.get('z', -9999.0) < player_z + 28.0)
    ]

    end_z = player_z + 24.0  # default beam length if nothing hit
    if candidates:
        # Remove the closest one ahead (smallest positive z distance from player)
        target = min(candidates, key=lambda o: o.get('z', 1e9))
        end_z = max(end_z, target.get('z', end_z))
        try:
            world.obstacles.remove(target)
        except ValueError:
            pass

        bullets_left -= 1
        score_increment = 5
        try:
            # Small reward for smart use
            from builtins import int as _int
            score_local = _int(score) + score_increment
            score = score_local
        except Exception:
            score += score_increment
    else:
        # No target found; still consume a bullet as a miss? Do NOT consume per user intent.
        # Keep bullets; just show tracer for feedback without removal.
        pass

    # Spawn a visible tracer along the lane so it is clearly seen in any weather
    spawn_bullet_tracer(player_lane * 3.0, player_z + 0.5, end_z)
    last_fire_ms = now

def spawn_bullet_tracer(x, z0, z1):
    """Create a short-lived glowing tracer along Z at lane X.
    x: lane x position, z0: start z, z1: end z in world space.
    """
    global bullet_tracers
    start_ms = now_ms()
    duration_ms = 220  # ~0.22s
    tracer = {
        'x': x,
        'y': 1.2,          # slightly above ground so it's not z-fighting
        'z0': z0,
        'z1': z1,
        'start_ms': start_ms,
        'duration_ms': duration_ms,
    }
    bullet_tracers.append(tracer)

def update_bullet_tracers():
    """Remove expired tracers based on time."""
    global bullet_tracers
    if not bullet_tracers:
        return
    now = now_ms()
    bullet_tracers = [t for t in bullet_tracers if (now - t['start_ms']) < t['duration_ms']]

def draw_bullet_tracers():
    """Draw glowing tracers with additive blending; disable depth test so visible in any weather."""
    global bullet_tracers
    if not bullet_tracers:
        return
    now = now_ms()
    # Draw opaque quads (no depth/blend toggling)
    for t in bullet_tracers:
        age = now - t['start_ms']
        dur = float(t['duration_ms'])
        a = max(0.0, 1.0 - (age / dur))  # fade out
        # two-layer: a bright core and a softer halo
        x = t['x']
        y = t['y']
        z0 = t['z0']
        z1 = t['z1']
        length = z1 - z0
        if length <= 0.05:
            continue
        # Core
        glColor3f(1.0, 0.95, 0.2)
        _draw_tracer_quad(x, y, z0, z1, 0.12)
        # Halo
        glColor3f(0.6, 0.8, 1.0)
        _draw_tracer_quad(x, y, z0, z1, 0.35)
    # No state to restore

def _draw_tracer_quad(x, y, z0, z1, half_w):
    """Draw a vertical rectangle centered at (x,y) extending from z0..z1 with given half-width along X."""
    glBegin(GL_QUADS)
    glVertex3f(x - half_w, y, z0)
    glVertex3f(x + half_w, y, z0)
    glVertex3f(x + half_w, y, z1)
    glVertex3f(x - half_w, y, z1)
    glEnd()

def generate_rain():
    global rain_drops
    rain_drops = []
    for _ in range(300):  
        x = random.uniform(-15, 15)
        z = random.uniform(-90, 90)
        y = random.uniform(5, 10)
        rain_drops.append({'x': x, 'y': y, 'z': z})
    return rain_drops

def draw_rain():
    global rain_drops
    if weather_state == "rainy":
        glColor3f(0.7, 0.7, 1.0)
        glBegin(GL_LINES)
        for raindrop in rain_drops:
            glVertex3f(raindrop['x'], raindrop['y'], raindrop['z'])
            glVertex3f(raindrop['x'], raindrop['y'] - 0.8, raindrop['z'])  # longer streak
        glEnd()

def draw_text(x, y, text, w=18, h=28, spacing=6):
    
    if not text:
        return
    cx = int(x)
    cy = int(y)
    for ch in text.upper():
        if ch == ' ':
            cx += w + spacing
            continue
        # Try to draw supported letter; otherwise fallback to box
        try:
            draw_letter(ch, cx, cy, w, h)
        except Exception:
            # Fallback: simple rectangle block representing the character cell
            draw_rect_outline(cx, cy, cx + w, cy + h)
        cx += w + spacing

# --- UI: Game Over box with stroked letters using midpoint line ---
def draw_rect_filled(x0, y0, x1, y1):
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x1, y0)
    glVertex2f(x1, y1)
    glVertex2f(x0, y1)
    glEnd()

def draw_filled_disc(radius, segments=32):
    """Draw a filled circle of given radius on the local XY plane using GL_TRIANGLES.
    Assumes caller has set the desired transform and color. Center at (0,0,0).
    """
    step = 2.0 * math.pi / float(max(3, segments))
    glBegin(GL_TRIANGLES)
    a = 0.0
    for i in range(max(3, segments)):
        x0 = radius * math.cos(a)
        y0 = radius * math.sin(a)
        a1 = a + step
        x1 = radius * math.cos(a1)
        y1 = radius * math.sin(a1)
        # Triangle: center -> edge a -> edge a1
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(x0, y0, 0.0)
        glVertex3f(x1, y1, 0.0)
        a = a1
    glEnd()

def draw_rect_outline(x0, y0, x1, y1):
    midpoint_line(int(x0), int(y0), int(x1), int(y0))
    midpoint_line(int(x1), int(y0), int(x1), int(y1))
    midpoint_line(int(x1), int(y1), int(x0), int(y1))
    midpoint_line(int(x0), int(y1), int(x0), int(y0))

def draw_letter(letter, x, y, w, h):
    # All letters are drawn with midpoint_line to create a stroked style
    # Coordinates are in screen 2D (UI) space
    lx = int(x); ly = int(y); rx = int(x + w); ty = int(y + h); cx = int(x + w/2)
    qw = int(w/4); qh = int(h/4)
    if letter == 'G':
        # Outer C shape
        midpoint_line(lx, ty, rx, ty)
        midpoint_line(lx, ly, rx, ly)
        midpoint_line(lx, ly, lx, ty)
        # Inner bar of G
        midpoint_line(cx, ly + qh, rx, ly + qh)
        midpoint_line(rx, ly + qh, rx, ly + qh*2)  # small inward notch
    elif letter == 'A':
        midpoint_line(lx, ly, cx, ty)
        midpoint_line(rx, ly, cx, ty)
        midpoint_line(lx + qw, ly + qh*2, rx - qw, ly + qh*2)
    elif letter == 'M':
        midpoint_line(lx, ly, lx, ty)
        midpoint_line(rx, ly, rx, ty)
        midpoint_line(lx, ty, cx, ly)
        midpoint_line(cx, ly, rx, ty)
    elif letter == 'E':
        midpoint_line(lx, ly, lx, ty)
        midpoint_line(lx, ty, rx, ty)
        midpoint_line(lx, ly + qh*2, cx + qw, ly + qh*2)
        midpoint_line(lx, ly, rx, ly)
    elif letter == 'O':
        draw_rect_outline(lx, ly, rx, ty)
    elif letter == 'V':
        midpoint_line(lx, ty, cx, ly)
        midpoint_line(rx, ty, cx, ly)
    elif letter == 'R':
        # P shape + leg
        midpoint_line(lx, ly, lx, ty)
        midpoint_line(lx, ty, cx + qw, ty)
        midpoint_line(cx + qw, ty, cx + qw, ly + qh*2)
        midpoint_line(cx + qw, ly + qh*2, lx, ly + qh*2)
        # diagonal leg
        midpoint_line(lx + qw, ly + qh*2, rx, ly)
    else:
        # Fallback: simple rectangle outline
        draw_rect_outline(lx, ly, rx, ty)

def draw_game_over_box_and_text():
    # Centered box
    cx, cy = 500, 400
    # Draw "GAME OVER" centered
    letters = list("GAME OVER")
    # Letter cell size
    lw, lh = 60, 110
    spacing = 20
    total_w = len(letters) * lw + (len(letters) - 1) * spacing
    # Box width with extra padding so stroked letters (like G and R) stay inside
    padding_x = 120
    bw = total_w + padding_x
    bh = 220
    x0 = cx - bw//2; x1 = cx + bw//2
    y0 = cy - bh//2; y1 = cy + bh//2

    # Filled white box
    glColor3f(1.0, 1.0, 1.0)
    draw_rect_filled(x0, y0, x1, y1)
    # Black border using midpoint lines
    glColor3f(0.0, 0.0, 0.0)
    draw_rect_outline(x0, y0, x1, y1)

    start_x = cx - total_w // 2
    base_y = cy - lh // 2

    for i, ch in enumerate(letters):
        if ch == ' ':
            continue
        x = start_x + i * (lw + spacing)
        glColor3f(0.0, 0.0, 0.0)
        draw_letter(ch, x, base_y, lw, lh)

def keyboardListener(key, x, y):
    global player_x, player_y, player_lane, player_target_x
    global player_is_jumping, player_is_sliding, player_slide_timer, player_jump_timer
    global game_over, road_speed, slide_hold, weather_state

    if game_over:
        if key == b'r' or key == b'R':
            restart_game()
        return  

    if is_playing:
        # Lane switching
        if key == b'd' or key == b'D':  # Move left
            if player_lane > -1:
                player_lane -= 1
                player_target_x = player_lane * 3.0
                
        elif key == b'a' or key == b'A':  # Move right
            if player_lane < 1:
                player_lane += 1
                player_target_x = player_lane * 3.0
                
        elif key == b'w' or key == b'W':  # Jump (fixed arc)
            if not player_is_jumping and not player_is_sliding:
                player_is_jumping = True
                player_jump_timer = 0
                
        elif key == b's' or key == b'S':  # Slide (hold to keep sliding)
            slide_hold = True
            if not player_is_jumping and not player_is_sliding:
                player_is_sliding = True
                player_slide_timer = 90  # initial slide duration
            elif player_is_sliding:
                # If already sliding, small bump so release won't end immediately
                player_slide_timer = min(player_slide_timer + 10, 150)
                
        elif key == b' ':  # Fire bullet to clear nearest obstacle in current lane
            fire_bullet()
            
        elif key == b'r' or key == b'R':  # Restart game
            restart_game()
            
        # Weather controls
        elif key == b'1':
            weather_state = "day"
        elif key == b'2':
            weather_state = "night"
        elif key == b'3':
            weather_state = "rainy"
            generate_rain()
        
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_angle_h, camera_height
    if key == GLUT_KEY_LEFT:
        camera_angle_h -= 5
    elif key == GLUT_KEY_RIGHT:
        camera_angle_h += 5
    elif key == GLUT_KEY_UP:
        camera_height += 1
    elif key == GLUT_KEY_DOWN:
        camera_height = max(2, camera_height - 1)

def keyboardUpListener(key, x, y):
    # Handle key release to stop continuous sliding
    global slide_hold
    if key == b's' or key == b'S':
        slide_hold = False

def mouseListener(button, state, x, y):
    global camera_view, game_over, is_playing
    y = 800 - y 
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if (500-10)<= x <=(500+10) and (750  -15) <= y <= (750 +15): #when pause/resume is pressed
            is_playing = not is_playing
            
        if (950-15)<= x <=(950+15) and (750 -15) <= y <= (750 +15): #when quit is pressed 
            print('Goodbye! Score:', score)
            glutLeaveMainLoop()
            
        if (30) <= x <= (80) and (750 -15) <= y <= (750 + 15):  # Restart
            print('Restarting the game...')
            restart_game()

    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        # Toggle between first-person and third-person views
        camera_view = "first_person" if camera_view == "third_person" else "third_person"
        print(f"Camera view switched to {camera_view}")

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if camera_view == "third_person":
        # Slightly narrower FOV for third-person stability
        gluPerspective(60, 1.25, 0.1, 400)
    else:
        # Wider FOV for first-person sense of speed
        gluPerspective(75, 1.25, 0.05, 400)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_view == "third_person":
        # Camera follows behind and above the player
        cx = player_x
        cy = camera_height  # keep camera height fixed
        cz = player_z - 10  # Behind the player
        # Look at a fixed height on the road for stable framing
        gluLookAt(cx, cy, cz, player_x, 2.0, player_z + 5, 0, 1, 0)
    else:
        # First person view from player's eyes slightly ahead to avoid clipping
        eye_x = player_x
        eye_y = (player_y if player_y > 0 else 0.0) + 1.6  # approximate eye height
        eye_z = player_z + 0.25
        look_x = player_x
        look_y = eye_y
        look_z = player_z + 8.0
        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0, 1, 0)
        
def animate():
    global player_x, player_y, player_target_x
    global player_is_jumping, player_is_sliding, player_slide_timer
    global game_over, road_speed, world

    if game_over or not is_playing:
        return
    
    # Update rain animation
    if weather_state == "rainy":
        for raindrop in rain_drops:
            raindrop['y'] -= 0.09 
            if raindrop['y'] < 0:
                raindrop['x'] = random.uniform(-30, 30)
                raindrop['z'] = random.uniform(-45, 60)
                raindrop['y'] = random.uniform(5, 20)
    
    # Update player movement
    update_player_movement()
    
    # Update world (endless runner mechanics)
    world.update_world()
    # Update visual effects
    update_bullet_tracers()
    
    # Keep world speed constant
    road_speed = road_speed
    
    glutPostRedisplay()

def update_player_movement():
    global player_x, player_y, player_z, player_target_x
    global player_is_jumping, player_is_sliding, player_slide_timer, player_jump_timer, player_jump_duration_frames, player_jump_height, player_jump_forward_distance, slide_hold
    
    # Smooth lane transitions (faster for better responsiveness)
    if abs(player_x - player_target_x) > 0.1:
        if player_x < player_target_x:
            player_x += 0.5
        else:
            player_x -= 0.5
    else:
        player_x = player_target_x
    
    # Handle jumping with fixed-duration sine arc and slight forward motion
    if player_is_jumping:
        t = player_jump_timer
        d = player_jump_duration_frames
        # y follows a sine arc from 0 -> peak -> 0 over d frames
        player_y = player_jump_height * math.sin(math.pi * (t / d))
        # move slightly forward each frame of the jump
        player_z += (player_jump_forward_distance / d)
        player_jump_timer += 1
        if player_jump_timer > d:
            player_y = 0.0
            player_is_jumping = False
    
    # Handle sliding
    if player_is_sliding:
        if slide_hold and not player_is_jumping:
            # Keep a small buffer so slide persists while S is held
            player_slide_timer = max(player_slide_timer, 10)
        else:
            player_slide_timer -= 1
        if player_slide_timer <= 0:
            player_is_sliding = False
            player_slide_timer = 0

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Ensure depth testing is enabled for 3D scene
    Gl_Depth(True)

    
    # Draw a fullscreen quad in 2D UI space behind everything
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    Gl_Depth(False)
    if weather_state == "day":
        glColor3f(0.5, 0.8, 1.0)  # Sky blue
    elif weather_state == "night":
        glColor3f(0.0, 0.0, 0.0)  # Black
    else:  # rainy
        glColor3f(0.2, 0.2, 0.4)  # Dark blue-gray
    glBegin(GL_QUADS)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(1000.0, 0.0, 0.0)
    glVertex3f(1000.0, 800.0, 0.0)
    glVertex3f(0.0, 800.0, 0.0)
    glEnd()
    Gl_Depth(True)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    setupCamera()
    
    # Draw night sky stars only in night mode
    if weather_state == "night":
        world.draw_sky()

    # Daytime indicator: sun and birds
    if weather_state == "day":
        world.draw_day_sun()
        world.draw_birds()

    # Draw world elements
    world.draw_track()
    world.draw_buildings()
    world.draw_obstacles()
    world.draw_coins()
    world.draw_powerups()
    # Draw bullet tracers so they are always visible across weather
    draw_bullet_tracers()
    
    # Draw rain effect
    draw_rain()
    
    # Draw player character only in third-person view
    if camera_view == "third_person":
        player.draw_person()
    
    iterate()
    
    # Draw UI elements
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)  
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    # UI overlay should ignore depth so it draws above 3D scene
    glClear(GL_DEPTH_BUFFER_BIT)
    # Also disable depth testing during UI so stroked text/lines cannot be hidden
    Gl_Depth(False)
    
    board.draw_buttons()
    player.draw_info()

    # Game over screen
    if game_over:
        draw_game_over_box_and_text()
        # Hint text under the box
        glColor3f(1, 1, 1)
        glRasterPos2f(380, 260)
        for ch in "Press R to Restart":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Controls help
    glColor3f(1, 1, 1)
    glRasterPos2f(700, 170)
    for ch in "Controls:":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glRasterPos2f(700, 140)
    for ch in "A/D - Switch Lanes":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glRasterPos2f(700, 110)
    for ch in "W - Jump":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glRasterPos2f(700, 80)
    for ch in "S - Slide":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glRasterPos2f(700, 50)
    for ch in "Space - Fire Bullet":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glRasterPos2f(700, 35)
    for ch in "1/2/3 - Day/Night/Rain":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glRasterPos2f(700, 20)
    for ch in "Right Click - Camera":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
  
    # Depth was disabled for UI; matrices restored below. Next frame re-enables depth at start.
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    glutSwapBuffers()

def iterate():
    glViewport(0, 0, 1000, 800)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glLoadIdentity()
      
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Endless Runner with Weather System")
    # Enable depth test for correct 3D layering
    Gl_Depth(True)
    
    # Initialize rain drops
    generate_rain()
    
    glutDisplayFunc(showScreen)
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutMainLoop()

if __name__ == "__main__":
    main()