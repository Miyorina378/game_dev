import pygame
import math

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

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Test case: Spinning Wall Pattern")
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
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.active = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 2)

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
        self.pattern_state = "spin_left"  # States: spin_left, pause_left, spin_right, pause_right
        self.state_timer = 0
        self.rotation_angle = 0
        
        # Pattern configuration
        self.SPIN_LEFT_DURATION = 2.0 * FPS  # 2 seconds in frames
        self.PAUSE_DURATION = 0.5 * FPS      # 0.5 seconds in frames
        self.SPIN_RIGHT_DURATION = 2.0 * FPS # 2 seconds in frames
        
    def update(self):
        self.timer += 1
        self.state_timer += 1
        
        # State machine for pattern timing
        if self.pattern_state == "spin_left":
            self.spinning_pattern(direction=-1)  # Counter-clockwise
            if self.state_timer >= self.SPIN_LEFT_DURATION:
                self.pattern_state = "pause_left"
                self.state_timer = 0
        
        elif self.pattern_state == "pause_left":
            # Pause - no new bullets
            if self.state_timer >= self.PAUSE_DURATION:
                self.pattern_state = "spin_right"
                self.state_timer = 0
        
        elif self.pattern_state == "spin_right":
            self.spinning_pattern(direction=1)  # Clockwise
            if self.state_timer >= self.SPIN_RIGHT_DURATION:
                self.pattern_state = "pause_right"
                self.state_timer = 0
        
        elif self.pattern_state == "pause_right":
            # Pause - no new bullets
            if self.state_timer >= self.PAUSE_DURATION:
                self.pattern_state = "spin_left"
                self.state_timer = 0
                self.rotation_angle = 0  # Reset rotation for clean loop
        
        # Update all bullets
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]
        
        # Auto damage for demo
        if self.timer % 30 == 0:
            self.hp -= 1
    
    def spinning_pattern(self, direction):
        """
        Creates a spinning wall pattern - dense with dodgeable gaps
        direction: -1 for left (counter-clockwise), 1 for right (clockwise)
        """
        if self.timer % 3 == 0:  # Shoot every 3 frames for balanced density
            # Update rotation angle based on direction - MUCH slower
            self.rotation_angle += direction * 0.015
            
            # Create wall with slight gaps
            num_bullets = 20  # Slightly reduced for small gaps
            for i in range(num_bullets):
                angle = self.rotation_angle + (i * 2 * math.pi / num_bullets)
                
                # Slower speed to create a wall effect
                speed = 1.2
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                # Color based on direction
                color = CYAN if direction == -1 else PURPLE
                
                self.bullets.append(Bullet(
                    self.x, self.y, vx, vy, color, 7
                ))
    
    def draw(self, screen):
        # Draw boss
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 8)
        
        # Draw eye based on state
        eye_color = RED if "spin" in self.pattern_state else WHITE
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
        if self.hp > 100:
            hp_color = (100, 255, 100)
        elif self.hp > 50:
            hp_color = (255, 255, 100)
        else:
            hp_color = (255, 100, 100)
        
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, hp_width, bar_height))
        
        # Draw spell card name and state
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        spell_text = font.render("Barrier Sign「Rotating Wall」", True, WHITE)
        screen.blit(spell_text, (WIDTH // 2 - spell_text.get_width() // 2, 280))
        
        # Show current state
        state_display = {
            "spin_left": "← SPINNING LEFT",
            "pause_left": "⊗ PAUSED",
            "spin_right": "SPINNING RIGHT →",
            "pause_right": "⊗ PAUSED"
        }
        state_text = small_font.render(state_display[self.pattern_state], True, CYAN if "left" in self.pattern_state else PURPLE)
        screen.blit(state_text, (WIDTH // 2 - state_text.get_width() // 2, 320))
        
        # Draw timer indicator
        total_cycle = self.SPIN_LEFT_DURATION + self.PAUSE_DURATION + self.SPIN_RIGHT_DURATION + self.PAUSE_DURATION
        cycle_progress = (self.timer % total_cycle) / total_cycle
        progress_width = 300
        progress_x = WIDTH // 2 - progress_width // 2
        progress_y = 350
        pygame.draw.rect(screen, WHITE, (progress_x - 2, progress_y - 2, progress_width + 4, 10), 2)
        pygame.draw.rect(screen, CYAN, (progress_x, progress_y, int(cycle_progress * progress_width), 6))

def main():
    player = Player()
    boss = Boss()
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
                    game_over = False
                    victory = False
        
        if not game_over and not victory:
            keys = pygame.key.get_pressed()
            player.update(keys)
            boss.update()
            
            # Collision detection
            for b in boss.bullets:
                dist = math.sqrt((player.x - b.x)**2 + (player.y - b.y)**2)
                if dist < player.hitbox + b.size:
                    game_over = True
            
            if boss.hp <= 0:
                victory = True
        
        # Drawing
        screen.fill(BLACK)
        
        # Draw play area border
        pygame.draw.rect(screen, WHITE, (0, 300, WIDTH, HEIGHT - 300), 2)
        
        boss.draw(screen)
        player.draw(screen)
        
        # Draw instructions
        inst_text = small_font.render("Arrow Keys: Move | Dodge the spinning bullets!", True, WHITE)
        screen.blit(inst_text, (10, 10))
        
        pattern_text = small_font.render("Pattern: Left Spin → Pause → Right Spin → Pause → Loop", True, WHITE)
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