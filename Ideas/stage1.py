import pygame
import math
import random

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 900
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (100, 150, 255)
CYAN = (100, 255, 255)
PURPLE = (200, 100, 255)
YELLOW = (255, 255, 100)
GREEN = (100, 255, 100)
ORANGE = (255, 165, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bullet Hell: Multi-Pattern Boss")
clock = pygame.time.Clock()

class Bullet:
    def __init__(self, x, y, vx, vy, color, size=5):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.active = True
        self.age = 0
        # For wave pattern
        self.wave_amplitude = None
        self.wave_frequency = None
        self.initial_angle = None
        self.wave_axis = 'x'  # Which axis to apply wave motion to
    
    def update(self):
        # Apply wave motion if parameters are set
        if self.wave_amplitude is not None and self.wave_frequency is not None:
            self.age += 1
            angle = self.initial_angle + self.age * self.wave_frequency
            wave_value = math.sin(angle) * self.wave_amplitude
            
            if self.wave_axis == 'x':
                self.vx = wave_value
            else:  # 'y'
                self.vy = wave_value
        
        self.x += self.vx
        self.y += self.vy
        
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.active = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 2)

class AcceleratingBullet(Bullet):
    def __init__(self, x, y, vx, vy, color, size=5, accel=0.02):
        super().__init__(x, y, vx, vy, color, size)
        self.accel = accel
    
    def update(self):
        # Accelerate in current direction
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 0:
            self.vx += (self.vx / speed) * self.accel
            self.vy += (self.vy / speed) * self.accel
        super().update()

class HomingBullet(Bullet):
    def __init__(self, x, y, vx, vy, color, size=5, target=None):
        super().__init__(x, y, vx, vy, color, size)
        self.target = target
        self.homing_strength = 0.05
        self.max_speed = 3
    
    def update(self):
        if self.target and self.age < 120:  # Only home for 2 seconds
            # Calculate direction to target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                # Add homing velocity
                self.vx += (dx / dist) * self.homing_strength
                self.vy += (dy / dist) * self.homing_strength
                
                # Limit speed
                speed = math.sqrt(self.vx**2 + self.vy**2)
                if speed > self.max_speed:
                    self.vx = (self.vx / speed) * self.max_speed
                    self.vy = (self.vy / speed) * self.max_speed
        super().update()

class Background:
    def __init__(self):
        self.particles = []
        self.stars = []
        self.timer = 0
        
        # Create initial stars
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.2, 0.8),
                'brightness': random.randint(100, 255)
            })
    
    def update(self, boss_pattern):
        self.timer += 1
        
        # Update stars - slow scrolling
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, WIDTH)
        
        # Add ambient particles based on boss pattern
        if self.timer % 5 == 0:
            pattern_name = boss_pattern[0]
            
            if pattern_name == "spiral":
                color = CYAN
                num = 2
            elif pattern_name == "burst":
                color = YELLOW
                num = 3
            elif pattern_name == "spinning_wall":
                color = PURPLE
                num = 2
            elif pattern_name == "wave":
                color = GREEN
                num = 3
            elif pattern_name == "star":
                color = ORANGE
                num = 2
            elif pattern_name == "homing":
                color = RED
                num = 4
            elif pattern_name == "chaos":
                color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                num = 5
            else:
                color = WHITE
                num = 1
            
            for _ in range(num):
                self.particles.append({
                    'x': random.randint(0, WIDTH),
                    'y': random.randint(0, 300),
                    'vx': random.uniform(-0.5, 0.5),
                    'vy': random.uniform(0.3, 1.5),
                    'size': random.randint(2, 5),
                    'color': color,
                    'life': random.randint(60, 120),
                    'max_life': 120
                })
        
        # Update particles
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def draw(self, screen, boss_phase):
        # Draw stars with twinkling effect
        for star in self.stars:
            twinkle = abs(math.sin(self.timer * 0.05 + star['x'] * 0.01))
            brightness = int(star['brightness'] * twinkle)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), star['size'])
        
        # Draw particles with fade effect
        for particle in self.particles:
            alpha_factor = particle['life'] / particle['max_life']
            size = int(particle['size'] * alpha_factor)
            if size > 0:
                # Create faded color
                r = int(particle['color'][0] * alpha_factor)
                g = int(particle['color'][1] * alpha_factor)
                b = int(particle['color'][2] * alpha_factor)
                pygame.draw.circle(screen, (r, g, b), (int(particle['x']), int(particle['y'])), size)
        
        # Draw phase-specific background effects
        if boss_phase == 2:
            # Add red vignette/glow effect for phase 2
            for i in range(3):
                alpha = 20 - i * 5
                offset = i * 3
                pygame.draw.rect(screen, (alpha, 0, 0), (offset, offset, WIDTH - offset * 2, HEIGHT - offset * 2), 2)

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.size = 5
        self.speed = 2
        self.hitbox = 2
    
    def update(self, keys):
        if keys[pygame.K_LEFT] and self.x > 20:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WIDTH - 20:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > 300:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < HEIGHT - 20:
            self.y += self.speed
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.hitbox)

class Boss:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = 150
        self.size = 25
        self.hp = 200
        self.max_hp = 200
        self.bullets = []
        
        # Pattern timing variables
        self.timer = 0
        self.pattern_index = 0
        self.pattern_timer = 0
        self.rotation_angle = 0
        self.phase = 1
        
        # Pattern sequence with durations (in seconds)
        self.patterns = [
            ("spiral", 4.0),
            ("burst", 3.0),
            ("spinning_wall", 4.0),
            ("wave", 3.5),
            ("star", 3.0),
            ("homing", 4.0),
            ("chaos", 20.0) 
        ]
        
        self.current_pattern = self.patterns[0]
        
    def update(self, player):
        self.timer += 1
        self.pattern_timer += 1
        
        # Check if it's time to switch patterns
        pattern_duration = self.current_pattern[1] * FPS
        if self.pattern_timer >= pattern_duration:
            self.pattern_index = (self.pattern_index + 1) % len(self.patterns)
            self.current_pattern = self.patterns[self.pattern_index]
            self.pattern_timer = 0
            self.rotation_angle = 0
        
        # Execute current pattern

        pattern_name = self.current_pattern[0]
        if pattern_name == "spiral":
            self.spiral_pattern()
        elif pattern_name == "burst":
            self.burst_pattern()
        elif pattern_name == "spinning_wall":
            self.spinning_wall_pattern()
        elif pattern_name == "wave":
            self.wave_pattern()
        elif pattern_name == "star":
            self.star_pattern()
        elif pattern_name == "homing":
            self.homing_pattern(player)
        elif pattern_name == "chaos":
            self.chaos_pattern(player)
        # ------------------------
        
        # Update all bullets
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]
        
        # Auto damage for demo
        if self.timer % 20 == 0:
            self.hp -= 1
        
        # Check phase transition
        if self.hp <= self.max_hp // 1 and self.phase == 1:
            self.phase = 2
            self.patterns.append(("chaos", 5.0))  # Add chaos pattern in phase 2
    
    def spiral_pattern(self):
        """Dense spiral that expands outward"""
        if self.timer % 4 == 0:
            self.rotation_angle += 0.2
            num_arms = 3
            for i in range(num_arms):
                angle = self.rotation_angle + (i * 2 * math.pi / num_arms)
                speed = 1.5
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                self.bullets.append(Bullet(
                    self.x, self.y, vx, vy, CYAN, 6
                ))
    
    def burst_pattern(self):
        """Circular bursts with gaps"""
        if self.timer % 30 == 0:
            num_bullets = 16
            gap_start = random.randint(0, num_bullets - 1)
            gap_size = 3
            
            for i in range(num_bullets):
                # Skip gap bullets
                if gap_start <= i < gap_start + gap_size:
                    continue
                    
                angle = (i * 2 * math.pi / num_bullets)
                speed = 2.5
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                self.bullets.append(AcceleratingBullet(
                    self.x, self.y, vx, vy, YELLOW, 5, 0.03
                ))
    
    def spinning_wall_pattern(self):
        """Rotating wall with clear gaps"""
        if self.timer % 5 == 0:  # Slower firing rate
            self.rotation_angle += 0.02
            num_bullets = 16  # Fewer bullets for bigger gaps
            gap_indices = [4, 5, 12, 13]  # Two gaps opposite each other
            
            for i in range(num_bullets):
                # Skip gap positions
                if i in gap_indices:
                    continue
                    
                angle = self.rotation_angle + (i * 2 * math.pi / num_bullets)
                speed = 1.5  # Slightly faster to compensate for gaps
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                self.bullets.append(Bullet(
                    self.x, self.y, vx, vy, PURPLE, 6
                ))
    
    def wave_pattern(self):
        """Sine wave bullets that come from alternating sides"""
        if self.timer % 3 == 0:
            # Alternate sides every second
            side = 1 if (self.timer // 60) % 2 == 0 else -1
            
            # Spawn from left or right edge
            bullet_x = WIDTH + 10 if side == 1 else -10
            bullet_y = 350 + (self.pattern_timer % 180) * 3  # Spread vertically
            
            # Base horizontal velocity (toward opposite side)
            vx = -2.5 * side
            
            # Sine wave motion parameters
            bullet = Bullet(bullet_x, bullet_y, vx, 0, GREEN, 6)
            bullet.wave_amplitude = 1.5  # Vertical oscillation strength
            bullet.wave_frequency = 0.15
            bullet.initial_angle = self.pattern_timer * 0.1
            bullet.wave_axis = 'y'  # Oscillate vertically while moving horizontally
            
            self.bullets.append(bullet)
    
    def star_pattern(self):
        """Star-shaped spread that rotates"""
        if self.timer % 20 == 0:
            self.rotation_angle += 0.3
            num_points = 5
            
            for i in range(num_points):
                angle = self.rotation_angle + (i * 2 * math.pi / num_points)
                
                # Create line of bullets for each point
                for j in range(3):
                    speed = 1.8 + j * 0.4
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    
                    self.bullets.append(Bullet(
                        self.x, self.y, vx, vy, ORANGE, 6
                    ))
    
    def homing_pattern(self, player):
        """Homing bullets that chase the player"""
        if self.timer % 25 == 0:
            # Launch homing bullets in a spread
            for i in range(3):
                angle = -math.pi/2 + (i - 1) * 0.5
                speed = 1.0
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                self.bullets.append(HomingBullet(
                    self.x, self.y, vx, vy, RED, 6, player
                ))
    
    def chaos_pattern(self, player):
            """Random bullets focused generally towards the player"""
            if self.timer % 6 == 0:
                # 1. Calculate angle to player
                dx = player.x - self.x
                dy = player.y - self.y
                target_angle = math.atan2(dy, dx)
                
                # 2. Add random spread (e.g., +/- 30 degrees)
                spread = random.uniform(-0.5, 0.5) 
                angle = target_angle + spread
                
                speed = random.uniform(2.0, 4.0) # Slightly faster to threaten player
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                colors = [CYAN, PURPLE, YELLOW, GREEN, ORANGE]
                self.bullets.append(Bullet(
                    self.x, self.y, vx, vy, random.choice(colors), 7
                ))
    
    def draw(self, screen):
        # Draw boss
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 8)
        
        # Draw eye (changes color based on phase)
        eye_color = RED if self.phase == 2 else CYAN
        pygame.draw.circle(screen, eye_color, (int(self.x), int(self.y)), 5)
        
        # Draw bullets
        for b in self.bullets:
            b.draw(screen)
        
        # Draw HP bar
        bar_width = 400
        bar_height = 20
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 250
        pygame.draw.rect(screen, WHITE, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)
        hp_width = int((self.hp / self.max_hp) * bar_width)
        
        # Color changes based on HP
        if self.hp > 666:
            hp_color = (100, 255, 100)
        elif self.hp > 333:
            hp_color = (255, 255, 100)
        else:
            hp_color = (255, 100, 100)
        
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, hp_width, bar_height))
        
        # Draw pattern name
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        pattern_names = {
            "spiral": "Spiral Sign「Triple Helix」",
            "burst": "Burst Sign「Expanding Nova」",
            "spinning_wall": "Barrier Sign「Rotating Wall」",
            "wave": "Wave Sign「Tidal Force」",
            "star": "Star Sign「Pentagram」",
            "homing": "Curse Sign「Seeking Shadow」",
            "chaos": "Chaos Sign「Entropy」"
        }
        
        spell_text = font.render(pattern_names[self.current_pattern[0]], True, WHITE)
        screen.blit(spell_text, (WIDTH // 2 - spell_text.get_width() // 2, 280))
        
        # Phase indicator
        if self.phase == 2:
            phase_text = small_font.render("⚠ PHASE 2 ⚠", True, RED)
            screen.blit(phase_text, (WIDTH // 2 - phase_text.get_width() // 2, 320))

def main():
    player = Player()
    boss = Boss()
    background = Background()
    running = True
    game_over = False
    victory = False
    
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 24)
    
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (game_over or victory):
                    # Restart
                    player = Player()
                    boss = Boss()
                    background = Background()
                    game_over = False
                    victory = False
        
        if not game_over and not victory:
            keys = pygame.key.get_pressed()
            player.update(keys)
            boss.update(player)
            background.update(boss.current_pattern)
            
            # Collision detection
            for b in boss.bullets:
                dist = math.sqrt((player.x - b.x)**2 + (player.y - b.y)**2)
                if dist < player.hitbox + b.size:
                    game_over = True
            
            if boss.hp <= 0:
                victory = True
        
        # Drawing
        screen.fill(BLACK)
        
        # Draw dynamic background
        background.draw(screen, boss.phase)
        
        # Draw play area border
        pygame.draw.rect(screen, WHITE, (0, 300, WIDTH, HEIGHT - 300), 2)
        
        boss.draw(screen)
        player.draw(screen)
        
        # Draw instructions
        inst_text = small_font.render("Arrow Keys: Move | Dodge all patterns!", True, WHITE)
        screen.blit(inst_text, (10, 10))
        
        pattern_text = small_font.render(f"Phase {boss.phase} | Pattern {boss.pattern_index + 1}/{len(boss.patterns)}", True, CYAN if boss.phase == 1 else RED)
        screen.blit(pattern_text, (10, 40))
        
        # Draw game state
        if game_over:
            text = font.render("GAME OVER", True, RED)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            restart_text = small_font.render("Press R to Restart", True, WHITE)
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
        elif victory:
            text = font.render("VICTORY!", True, CYAN)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            restart_text = small_font.render("Press R to Restart", True, WHITE)
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()