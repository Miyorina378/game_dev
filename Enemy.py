import pygame
import math
import random
from config import SCREEN_HEIGHT, SCREEN_WIDTH

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speedx, speedy, bullet_type="player"):
        super().__init__()
        self.bullet_type = bullet_type
        if self.bullet_type == "player":
            self.image = pygame.image.load("media/images/bullet2.png").convert_alpha()
        elif self.bullet_type == "enemy_a":
            self.image = pygame.Surface([8, 8])
            pygame.draw.circle(self.image, RED, (4, 4), 4)
            self.image.set_colorkey(BLACK)
        elif self.bullet_type == "enemy_b":
            self.image = pygame.Surface([10, 10])
            self.image.fill(GREEN)
        elif self.bullet_type == "enemy_c":
            self.image = pygame.Surface([12, 12])
            self.image.fill(BLUE)
        elif self.bullet_type == "boss_bullet":
            self.image = pygame.image.load("media/images/bullet1.png").convert_alpha()
        elif self.bullet_type == "emerald_bullet":
            self.image = pygame.image.load("media/images/emerald-bullet.png").convert_alpha()
        elif self.bullet_type == "homing_missile":
            self.image = pygame.Surface([7, 15])
            self.image.fill(BLUE)

        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speedx = speedx
        self.speedy = speedy
        self.grazed = False

    def update(self, frame_count):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if not pygame.display.get_surface().get_rect().colliderect(self.rect):
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=None, waypoints=None, speed=1, fast_entry=False):
        super().__init__()
        self.image = pygame.Surface([30, 30], pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.position = pygame.math.Vector2(x, y)
        self.rect.center = self.position
        self.normal_speed = speed
        self.fast_entry_speed = 10 # Example high speed
        self.speed = self.fast_entry_speed if fast_entry else self.normal_speed
        self.fast_entry = fast_entry
        self.decelerating = False
        self.speed_threshold_y = screen_height * 0.25 # Changed from 0.75 to 0.25
        self.velocity = pygame.math.Vector2(0, self.speed)
        self.shoot_delay = 1000
        self.last_shot = 0
        self.health = 10
        self.debuffs = {}
        self.player = player
        self.bullet_pattern = bullet_pattern
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.all_sprites = all_sprites
        self.enemy_bullets = enemy_bullets

    def update(self, frame_count):
        self.move(frame_count)
        self.shoot(frame_count)
        if self.health <= 0:
            self.kill()

        for debuff, data in list(self.debuffs.items()):
            if frame_count - data["start_time"] > data["duration"]:
                del self.debuffs[debuff]

    def move(self, frame_count):
        if self.fast_entry and self.position.y >= self.speed_threshold_y:
            self.decelerating = True
            self.fast_entry = False

        if self.decelerating:
            if self.speed > self.normal_speed:
                self.speed -= 1 # Deceleration factor
                if self.speed < self.normal_speed:
                    self.speed = self.normal_speed
            else:
                self.decelerating = False
            self.velocity.y = self.speed # Update velocity to reflect new speed

        if self.waypoints and self.current_waypoint_index < len(self.waypoints):
            target = pygame.math.Vector2(self.waypoints[self.current_waypoint_index])
            desired_velocity = (target - self.position)
            dist = desired_velocity.length()

            if dist < self.speed * 5:
                self.current_waypoint_index += 1

            if self.current_waypoint_index < len(self.waypoints):
                target = pygame.math.Vector2(self.waypoints[self.current_waypoint_index])
                desired_velocity = (target - self.position)
                desired_velocity.normalize_ip()
                desired_velocity *= self.speed

                steer = desired_velocity - self.velocity
                max_steer = 0.3 # Lower value for sharper turns, higher for smoother turns
                if steer.length() > max_steer:
                    steer.scale_to_length(max_steer)

                self.velocity += steer
                if self.velocity.length() > self.speed:
                    self.velocity.scale_to_length(self.speed)

                self.position += self.velocity
                self.rect.center = self.position
            else:
                self.position += self.velocity
                self.rect.center = self.position
        else:
            self.position += self.velocity # Use velocity for movement
            self.rect.center = self.position

    def shoot(self, frame_count):
        if self.bullet_pattern:
            self.bullet_pattern(self, self.player, self.all_sprites, self.enemy_bullets, frame_count)

class EnemyTypeA(Enemy):
    def __init__(self, x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=None, waypoints=None, speed=1, fast_entry=False):
        super().__init__(x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=bullet_pattern, waypoints=waypoints, speed=speed, fast_entry=fast_entry)
        self.image = pygame.Surface([30, 30], pygame.SRCALPHA)
        pygame.draw.polygon(self.image, RED, [(15, 0), (0, 30), (30, 30)])
        self.shoot_delay = 1500

class EnemyTypeB(Enemy):
    def __init__(self, x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=None, waypoints=None, speed=1, fast_entry=False):
        super().__init__(x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=bullet_pattern, waypoints=waypoints, speed=speed, fast_entry=fast_entry)
        self.image = pygame.Surface([30, 30], pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (15, 15), 15)
        self.shoot_delay = 2000
        self.burst_count = 0
        self.last_burst_shot = 0

class EnemyTypeC(Enemy):
    def __init__(self, x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=None, waypoints=None, speed=1, fast_entry=False):
        super().__init__(x, y, player, all_sprites, enemy_bullets, screen_height, bullet_pattern=bullet_pattern, waypoints=waypoints, speed=speed, fast_entry=fast_entry)
        self.image = pygame.Surface([30, 30], pygame.SRCALPHA)
        points = self.create_star_points(15, 15, 15, 7, 5)
        pygame.draw.polygon(self.image, (255, 255, 0), points)
        self.shoot_delay = 1000
        self.angle = 0

    def create_star_points(self, center_x, center_y, outer_radius, inner_radius, num_points=5):
        points = []
        angle = -math.pi / 2
        angle_step = 2 * math.pi / (num_points * 2)
        for i in range(num_points * 2):
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            points.append((x, y))
            angle += angle_step
        return points

class Boss(pygame.sprite.Sprite):
    def __init__(self, player, all_sprites, enemy_bullets):
        super().__init__()
        self.image = pygame.Surface((100, 100))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = 400
        self.rect.y = 50
        self.health = 1000
        self.max_health = 1000
        self.patterns = ['non_schematic_1', 'schematic_1']
        self.current_pattern_index = 0
        self.pattern_start_time = 0
        self.debuffs = {}
        self.player = player
        self.all_sprites = all_sprites
        self.enemy_bullets = enemy_bullets

        # Schematic 2 state variables
        self.schematic_2_active = False  # NEW: Track if schematic 2 is active
        self.schematic_2_timer = 0
        self.schematic_2_pattern_state = "spin_left"
        self.schematic_2_state_timer = 0
        self.schematic_2_rotation_angle = 0
        self.SPIN_LEFT_DURATION = 120  # 2 seconds at 60 FPS
        self.PAUSE_DURATION = 30       # 0.5 seconds at 60 FPS
        self.SPIN_RIGHT_DURATION = 120 # 2 seconds at 60 FPS

    def update(self, frame_count):
        # Check if we should activate schematic 2
        if self.health / self.max_health < 0.25 and not self.schematic_2_active:
            self.schematic_2_active = True
            self.schematic_2_timer = 0
            self.schematic_2_state_timer = 0
            self.schematic_2_rotation_angle = 0
            self.schematic_2_pattern_state = "spin_left"
        
        # If schematic 2 is active, use it exclusively
        if self.schematic_2_active:
            self.schematic_2(frame_count)
        else:
            # Normal pattern rotation
            if frame_count - self.pattern_start_time > 600:
                self.current_pattern_index = (self.current_pattern_index + 1) % len(self.patterns)
                self.pattern_start_time = frame_count
            getattr(self, self.patterns[self.current_pattern_index])(frame_count)

        # Handle debuffs
        for debuff, data in list(self.debuffs.items()):
            if frame_count - data["start_time"] > data["duration"]:
                del self.debuffs[debuff]

    def non_schematic_1(self, frame_count):
        if frame_count % 12 < 2:
            angle = math.atan2(self.player.rect.centery - self.rect.centery, 
                             self.player.rect.centerx - self.rect.centerx)
            speed = 5
            bullet = Bullet(self.rect.centerx, self.rect.centery, 
                          math.cos(angle) * speed, math.sin(angle) * speed, 
                          "boss_bullet")
            self.all_sprites.add(bullet)
            self.enemy_bullets.add(bullet)

    def schematic_1(self, frame_count):
        if frame_count % 6 < 2:
            for _ in range(15):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1, 3)
                bullet = Bullet(self.rect.centerx, self.rect.centery, 
                              math.cos(angle) * speed, math.sin(angle) * speed, 
                              "boss_bullet")
                self.all_sprites.add(bullet)
                self.enemy_bullets.add(bullet)

    def schematic_2(self, frame_count):
        """Spinning wall pattern - alternates left/right with pauses"""
        self.schematic_2_timer += 1
        self.schematic_2_state_timer += 1
        
        if self.schematic_2_pattern_state == "spin_left":
            self.spinning_pattern(direction=-1)
            if self.schematic_2_state_timer >= self.SPIN_LEFT_DURATION:
                self.schematic_2_pattern_state = "pause_left"
                self.schematic_2_state_timer = 0
        
        elif self.schematic_2_pattern_state == "pause_left":
            # No bullets during pause
            if self.schematic_2_state_timer >= self.PAUSE_DURATION:
                self.schematic_2_pattern_state = "spin_right"
                self.schematic_2_state_timer = 0
        
        elif self.schematic_2_pattern_state == "spin_right":
            self.spinning_pattern(direction=1)
            if self.schematic_2_state_timer >= self.SPIN_RIGHT_DURATION:
                self.schematic_2_pattern_state = "pause_right"
                self.schematic_2_state_timer = 0
        
        elif self.schematic_2_pattern_state == "pause_right":
            # No bullets during pause
            if self.schematic_2_state_timer >= self.PAUSE_DURATION:
                self.schematic_2_pattern_state = "spin_left"
                self.schematic_2_state_timer = 0
                # Optional: reset rotation for clean loop
                # self.schematic_2_rotation_angle = 0

    def spinning_pattern(self, direction):
        """Creates a spinning wall of bullets"""
        if self.schematic_2_timer % 3 == 0:  # Fire every 3 frames
            # Slower rotation for dodgeable gaps
            self.schematic_2_rotation_angle += direction * 0.03
            
            num_bullets = 20
            for i in range(num_bullets):
                angle = self.schematic_2_rotation_angle + (i * 2 * math.pi / num_bullets)
                speed = 1.2  # Slow speed for wall effect
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                bullet = Bullet(self.rect.centerx, self.rect.centery, 
                              vx, vy, "boss_bullet")
                self.all_sprites.add(bullet)
                self.enemy_bullets.add(bullet)




class BossTypeA(Boss):
    def __init__(self, player, all_sprites, enemy_bullets):
        super().__init__(player, all_sprites, enemy_bullets)

class Miniboss(Enemy):
    def __init__(self, x, y, player, all_sprites, enemy_bullets, screen_height, waypoints=None):
        super().__init__(x, y, player, all_sprites, enemy_bullets, screen_height, waypoints=None, speed=2)
        self.image = pygame.Surface((60, 60))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.health = 500
        self.max_health = 500
        self.shoot_delay = 100
        self.pattern_state = 0
        self.pattern_wave_count = 0

        self.movement_state = 'moving_to_center'
        self.center_pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        self.top_left_pos = pygame.math.Vector2(100, 100)
        self.top_right_pos = pygame.math.Vector2(SCREEN_WIDTH - 100, 100)
        self.movement_timer = 0
        self.corner_move_interval = 4000

    def move(self, frame_count):
        if self.movement_state == 'moving_to_center':
            self.waypoints = [self.center_pos]
            if self.position.distance_to(self.center_pos) < 5:
                self.movement_state = 'at_center'
                self.movement_timer = frame_count
                self.waypoints = None
        
        elif self.movement_state == 'at_center':
                    if frame_count - self.movement_timer > 240:
                        self.movement_state = 'moving_to_corner'
                        if random.random() < 0.5:
                            self.waypoints = [self.top_left_pos, self.center_pos]
                        else:
                            self.waypoints = [self.top_right_pos, self.center_pos]
                        self.current_waypoint_index = 0

        elif self.movement_state == 'moving_to_corner':
            if self.current_waypoint_index >= len(self.waypoints):
                self.movement_state = 'at_center'
                self.movement_timer = frame_count
                self.waypoints = None

        if self.waypoints:
            super().move(frame_count)

    def shoot(self, frame_count):
        if frame_count - self.last_shot > self.shoot_delay:
            self.last_shot = frame_count
            
            target_x, target_y = self.player.rect.center
            if self.pattern_state == 1:
                target_x -= 50
            elif self.pattern_state == 2:
                target_x += 50

            for i in range(10):
                angle = math.atan2(target_y - self.rect.centery, target_x - self.rect.centerx)
                angle += random.uniform(-0.1, 0.1)
                speed = 5
                bullet = Bullet(self.rect.centerx, self.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "enemy_b")
                self.all_sprites.add(bullet)
                self.enemy_bullets.add(bullet)

            self.pattern_wave_count += 1
            if self.pattern_state == 0:
                if self.pattern_wave_count >= 2:
                    self.pattern_state = 1
                    self.pattern_wave_count = 0
            elif self.pattern_state == 1:
                if self.pattern_wave_count >= 1:
                    self.pattern_state = 2
                    self.pattern_wave_count = 0
            elif self.pattern_state == 2:
                if self.pattern_wave_count >= 1:
                    self.pattern_state = 0
                    self.pattern_wave_count = 0

class HomingMissile(Bullet):
    def __init__(self, x, y, speedx, speedy, enemies):
        super().__init__(x, y, speedx, speedy, "homing_missile")
        self.start_pos = pygame.math.Vector2(x, y)
        self.target = None
        self.last_direction = pygame.math.Vector2(0, 0)
        self.enemies = enemies

    def update(self, frame_count):
        if self.target and self.target.alive():
            direction = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            if direction.length() > 0:
                direction.normalize_ip()
                self.last_direction = direction
            self.rect.x += direction.x * 5
            self.rect.y += direction.y * 5
        elif self.target and not self.target.alive():
            self.rect.x += self.last_direction.x * 5
            self.rect.y += self.last_direction.y * 5
        else:
            self.rect.x += self.speedx
            self.rect.y += self.speedy

        if not self.target and self.start_pos.distance_to(self.rect.center) > 300:
            closest_enemy = None
            closest_distance = float('inf')
            for enemy in self.enemies:
                distance = pygame.math.Vector2(self.rect.center).distance_to(enemy.rect.center)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy
            self.target = closest_enemy


def pattern_simple_shot(enemy, player, all_sprites, enemy_bullets, frame_count):
    if frame_count - enemy.last_shot > enemy.shoot_delay:
        enemy.last_shot = frame_count
        bullet = Bullet(enemy.rect.centerx, enemy.rect.bottom, 0, 5, "enemy_a")
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

def pattern_burst_shot(enemy, player, all_sprites, enemy_bullets, frame_count):
    if not hasattr(enemy, 'burst_count'):
        enemy.burst_count = 0
    if not hasattr(enemy, 'last_burst_shot'):
        enemy.last_burst_shot = 0

    if frame_count - enemy.last_shot > enemy.shoot_delay and enemy.burst_count == 0:
        enemy.last_shot = frame_count
        enemy.burst_count = 3
        enemy.last_burst_shot = frame_count

    if enemy.burst_count > 0 and frame_count - enemy.last_burst_shot > 6:
        enemy.last_burst_shot = frame_count
        enemy.burst_count -= 1
        bullet = Bullet(enemy.rect.centerx, enemy.rect.bottom, 0, 7, "enemy_b")
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

def pattern_spiral_shot(enemy, player, all_sprites, enemy_bullets, frame_count):
    if not hasattr(enemy, 'angle'):
        enemy.angle = 0
    if frame_count - enemy.last_shot > enemy.shoot_delay:
        enemy.last_shot = frame_count
        for i in range(8):
            angle = enemy.angle + i * (2 * math.pi / 8)
            speed = 3
            bullet = Bullet(enemy.rect.centerx, enemy.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "enemy_c")
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
        enemy.angle += math.pi / 16

def pattern_triple_shot(enemy, player, all_sprites, enemy_bullets, frame_count):
    if not hasattr(enemy, 'shoot_delay'):
        enemy.shoot_delay = 420
    if frame_count - enemy.last_shot > enemy.shoot_delay:
        enemy.last_shot = frame_count
        for i in range(-1, 2):
            bullet = Bullet(enemy.rect.centerx, enemy.rect.bottom, i * 2, 5, "enemy_a")
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

def pattern_aimed_shot(enemy, player, all_sprites, enemy_bullets, frame_count):
    if frame_count - enemy.last_shot > enemy.shoot_delay:
        enemy.last_shot = frame_count
        base_angle = math.atan2(player.rect.centery - enemy.rect.centery, player.rect.centerx - enemy.rect.centerx)
        spread = 0.2 # radians
        for i in range(3):
            angle = base_angle + (i - 1) * spread
            speed = 5
            bullet = Bullet(enemy.rect.centerx, enemy.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "enemy_a")
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

def pattern_emerald_shot(enemy, player, all_sprites, enemy_bullets, frame_count):
    if frame_count - enemy.last_shot > enemy.shoot_delay:
        enemy.last_shot = frame_count
        angle = math.atan2(player.rect.centery - enemy.rect.centery, player.rect.centerx - enemy.rect.centerx)
        speed = 7
        bullet = Bullet(enemy.rect.centerx, enemy.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "emerald_bullet")
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)
