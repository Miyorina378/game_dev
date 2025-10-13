import pygame
import random
import math
import json
import os

# Initialize Pygame
pygame.init()

# Screen dimensions
NATIVE_WIDTH = 800
NATIVE_HEIGHT = 600
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
UI_WIDTH = 250

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Create the screen
screen = pygame.display.set_mode((NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
render_surface = pygame.Surface((SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aetherium Machina")

# Font
font_name = pygame.font.match_font('arial')
death_sound = pygame.mixer.Sound("media/sfx/death.wav")
select_sound = pygame.mixer.Sound("media/sfx/Select.wav")
start_game_sound = pygame.mixer.Sound("media/sfx/startNewGame.wav")

SAVE_FILE = "savegame.json"

def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

class Weapon:
    def __init__(self, name, weapon_type):
        self.name = name
        self.weapon_type = weapon_type

    def shoot(self, player):
        pass

class WeaponManager:
    def __init__(self, player):
        self.player = player
        self.weapons = {
            "active": [DefaultWeapon(), BeamCannon()],
            "passive": [HomingMissiles()]
        }
        self.active_weapon_index = 0

    def shoot_active(self):
        self.weapons["active"][self.active_weapon_index].shoot(self.player)

    def shoot_passive(self):
        for weapon in self.weapons["passive"]:
            weapon.shoot(self.player)

    def switch_weapon(self):
        self.active_weapon_index = (self.active_weapon_index + 1) % len(self.weapons["active"])

class DefaultWeapon(Weapon):
    def __init__(self):
        super().__init__("Default", "active")

    def shoot(self, player):
        now = pygame.time.get_ticks()
        if now - player.last_shot > player.shoot_delay:
            player.last_shot = now
            if not pygame.mixer.Channel(0).get_busy():
                pygame.mixer.Channel(0).play(player.shooting_sound)
            if player.focused:
                all_sprites.add(Bullet(player.rect.centerx, player.rect.top, 0, -10, "player"))
                bullets.add(all_sprites.sprites()[-1])
            else:
                all_sprites.add(Bullet(player.rect.centerx, player.rect.top, 0, -7, "player"),
                                Bullet(player.rect.left, player.rect.centery, -2, -7, "player"),
                                Bullet(player.rect.right, player.rect.centery, 2, -7, "player"))
                bullets.add(all_sprites.sprites()[-3:])

class Beam(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([40, SCREEN_HEIGHT])
        self.image.fill(RED)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > 200:
            self.kill()

class BeamCannon(Weapon):
    def __init__(self):
        super().__init__("Beam Cannon", "active")
        self.last_shot = 0
        self.shoot_delay = 2000

    def shoot(self, player):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            beam = Beam(player.rect.centerx, player.rect.top)
            all_sprites.add(beam)
            beams.add(beam)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speedx, speedy, bullet_type="player"):
        super().__init__()
        self.bullet_type = bullet_type
        if self.bullet_type == "player":
            self.image = pygame.Surface([5, 10])
            self.image.fill(WHITE)
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

        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speedx = speedx
        self.speedy = speedy
        self.grazed = False

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if not screen.get_rect().colliderect(self.rect):
            self.kill()

class HomingMissile(Bullet):
    def __init__(self, x, y, speedx, speedy):
        self.image = pygame.Surface([7, 15])
        self.image.fill(BLUE)
        super().__init__(x, y, speedx, speedy, "homing_missile")
        self.start_pos = pygame.math.Vector2(x, y)
        self.target = None
        self.last_direction = pygame.math.Vector2(0, 0)

    def update(self):
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
            for enemy in enemies:
                distance = pygame.math.Vector2(self.rect.center).distance_to(enemy.rect.center)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy
            self.target = closest_enemy

class HomingMissiles(Weapon):
    def __init__(self):
        super().__init__("Homing Missiles", "passive")
        self.last_shot = 0
        self.shoot_delay = 2000

    def shoot(self, player):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            missile1 = HomingMissile(player.rect.left, player.rect.centery, -2, -7)
            missile2 = HomingMissile(player.rect.right, player.rect.centery, 2, -7)
            all_sprites.add(missile1, missile2)
            bullets.add(missile1, missile2)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load("media/images/robin.webp").convert()
        self.original_image.set_colorkey(WHITE)
        self.image = pygame.transform.scale(self.original_image, (40, 40))
        self.image_orig = self.image.copy()
        self.mask = pygame.mask.from_surface(self.image)
        self.flicker_interval = 150
        self.i_frame_duration = 3000
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH / 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 5
        self.focused = False
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = 100
        self.lives = 3
        self.bombs = 3
        self.power = 0
        self.score = 0
        self.graze = 0
        self.invincible = False
        self.invincible_timer = 0
        self.stage = 1
        self.shooting_sound = pygame.mixer.Sound("media/sfx/rapidFireLoop.wav")
        self.shooting_sound.set_volume(0.5)
        self.weapon_manager = WeaponManager(self)

    def update(self):
        keys = pygame.key.get_pressed()
        self.speed = 2.5 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 5
        self.focused = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        
        if keys[pygame.K_z]:
            self.shoot()
        else:
            pygame.mixer.Channel(0).stop()

        now = pygame.time.get_ticks()
        if self.invincible:
            if now - self.invincible_timer > self.i_frame_duration:
                self.invincible = False
                try:
                    self.image.set_alpha(255)
                except Exception:
                    pass
            else:
                step = ((now - self.invincible_timer) // self.flicker_interval) % 2
                self.image.set_alpha(255 if step == 0 else 0)
        else:
            try:
                self.image.set_alpha(255)
            except Exception:
                pass

    def shoot(self):
        self.weapon_manager.shoot_active()
        self.weapon_manager.shoot_passive()

    def use_bomb(self):
        if self.bombs > 0:
            self.bombs -= 1
            for enemy in enemies:
                enemy.kill()
            for bullet in enemy_bullets:
                bullet.kill()

    def die(self):
        self.lives -= 1
        pygame.mixer.Channel(1).play(death_sound)
        explosion = Explosion(self.rect.center)
        all_sprites.add(explosion)
        power_to_drop = int(self.power * 0.25)
        self.power -= power_to_drop
        for _ in range(power_to_drop):
            powerup = PowerUp(self.rect.center)
            all_sprites.add(powerup)
            powerups.add(powerup)
        self.rect.centerx = SCREEN_WIDTH / 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks()

    def draw_hitbox(self, surface):
        if self.focused:
            pygame.draw.circle(surface, RED, self.rect.center, 5)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([30, 30])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speedy = 1
        self.speedx = 0
        self.shoot_delay = 1000
        self.last_shot = pygame.time.get_ticks()
        self.health = 10
        self.debuffs = {}

    def update(self):
        self.move()
        self.shoot()
        if self.health <= 0:
            self.kill()

        for debuff, data in list(self.debuffs.items()):
            if pygame.time.get_ticks() - data["start_time"] > data["duration"]:
                del self.debuffs[debuff]

    def move(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > SCREEN_HEIGHT + 10 or self.rect.left < -25 or self.rect.right > SCREEN_WIDTH + 20:
            self.kill()

    def shoot(self):
        pass

class EnemyTypeA(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.shoot_delay = 1500

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.bottom, 0, 5, "enemy_a")
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

class EnemyTypeB(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.shoot_delay = 2000
        self.burst_count = 0
        self.last_burst_shot = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay and self.burst_count == 0:
            self.last_shot = now
            self.burst_count = 3
            self.last_burst_shot = now

        if self.burst_count > 0 and now - self.last_burst_shot > 100:
            self.last_burst_shot = now
            self.burst_count -= 1
            bullet = Bullet(self.rect.centerx, self.rect.bottom, 0, 7, "enemy_b")
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

class EnemyTypeC(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.shoot_delay = 1000
        self.angle = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            for i in range(8):
                angle = self.angle + i * (2 * math.pi / 8)
                speed = 3
                bullet = Bullet(self.rect.centerx, self.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "enemy_c")
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
            self.angle += math.pi / 16

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100, 100))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH / 2
        self.rect.y = 50
        self.health = 1000
        self.max_health = 1000
        self.patterns = ['non_schematic_1', 'schematic_1']
        self.current_pattern_index = 0
        self.pattern_start_time = pygame.time.get_ticks()
        self.debuffs = {}

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.pattern_start_time > 10000:
            self.current_pattern_index = (self.current_pattern_index + 1) % len(self.patterns)
            self.pattern_start_time = now
        getattr(self, self.patterns[self.current_pattern_index])()

        for debuff, data in list(self.debuffs.items()):
            if pygame.time.get_ticks() - data["start_time"] > data["duration"]:
                del self.debuffs[debuff]

    def non_schematic_1(self):
        if pygame.time.get_ticks() % 200 < 20:
            angle = math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx)
            speed = 5
            bullet = Bullet(self.rect.centerx, self.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "boss_bullet")
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

    def schematic_1(self):
        if pygame.time.get_ticks() % 100 < 20:
            for i in range(2):
                angle = (pygame.time.get_ticks() / 1000 + i * math.pi) * 2
                speed = 3
                bullet = Bullet(self.rect.centerx, self.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, "boss_bullet")
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)

class BossTypeA(Boss):
    pass

class Stage:
    def __init__(self, player, all_sprites, enemies, enemy_bullets, bosses):
        self.player = player
        self.all_sprites = all_sprites
        self.enemies = enemies
        self.enemy_bullets = enemy_bullets
        self.bosses = bosses
        self.stage_complete = False
        self.boss_spawned = False

    def update(self): pass
    def spawn_enemies(self): pass
    def spawn_boss(self): pass

class Stage1(Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.waves = [
            {"time": 1000, "enemies": [{"type": "A", "x": 100, "y": -50}, {"type": "A", "x": 300, "y": -50}, {"type": "A", "x": 500, "y": -50}]},
            {"time": 5000, "enemies": [{"type": "B", "x": 200, "y": -50}, {"type": "B", "x": 400, "y": -50}]},
            {"time": 10000, "enemies": [{"type": "C", "x": 300, "y": -50}]},
            {"time": 15000, "enemies": [{"type": "A", "x": 100, "y": -50}, {"type": "B", "x": 300, "y": -50}, {"type": "A", "x": 500, "y": -50}]},
            {"time": 20000, "random": True, "count": 5}
        ]
        self.wave_index = 0
        self.stage_timer = pygame.time.get_ticks()

    def update(self):
        if not self.boss_spawned:
            self.spawn_enemies()
            if self.wave_index >= len(self.waves) and len(self.enemies) == 0:
                self.spawn_boss()
                self.boss_spawned = True
        elif not self.bosses:
            self.stage_complete = True

    def spawn_enemies(self):
        now = pygame.time.get_ticks()
        if self.wave_index < len(self.waves):
            wave = self.waves[self.wave_index]
            if now - self.stage_timer > wave["time"]:
                if wave.get("random"):
                    for _ in range(wave["count"]):
                        enemy_type = random.choice(["A", "B", "C"])
                        x = random.randrange(SCREEN_WIDTH - 30)
                        y = -50
                        self.spawn_enemy(enemy_type, x, y)
                else:
                    for enemy_info in wave["enemies"]:
                        self.spawn_enemy(enemy_info["type"], enemy_info["x"], enemy_info["y"])
                self.wave_index += 1

    def spawn_enemy(self, enemy_type, x, y):
        if enemy_type == "A":
            enemy = EnemyTypeA(x, y)
        elif enemy_type == "B":
            enemy = EnemyTypeB(x, y)
        elif enemy_type == "C":
            enemy = EnemyTypeC(x, y)
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def spawn_boss(self):
        for enemy in self.enemies:
            enemy.kill()
        boss = BossTypeA()
        self.all_sprites.add(boss)
        self.bosses.add(boss)

class Stage2(Stage): pass
class Stage3(Stage): pass
class Stage4(Stage): pass
class Stage5(Stage): pass
class Stage6(Stage): pass
class Stage7(Stage): pass

class StageManager:
    def __init__(self, player, all_sprites, enemies, enemy_bullets, bosses):
        self.player = player
        self.all_sprites = all_sprites
        self.enemies = enemies
        self.enemy_bullets = enemy_bullets
        self.bosses = bosses
        self.stages = [Stage1, Stage2, Stage3, Stage4, Stage5, Stage6, Stage7]
        self.current_stage_index = self.player.stage - 1
        self.current_stage = self.stages[self.current_stage_index](self.player, self.all_sprites, self.enemies, self.enemy_bullets, self.bosses)

    def update(self):
        self.current_stage.update()
        if self.current_stage.stage_complete:
            self.next_stage()

    def next_stage(self):
        self.current_stage_index += 1
        self.player.stage += 1
        if self.current_stage_index < len(self.stages):
            self.current_stage = self.stages[self.current_stage_index](self.player, self.all_sprites, self.enemies, self.enemy_bullets, self.bosses)
        else:
            print("Game complete!") # Placeholder

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 2

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.radius = 1
        self.max_radius = 50
        self.animation_speed = 2
        self.last_update = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.radius += 1
            if self.radius >= self.max_radius:
                self.kill()
            else:
                self.image.fill((0, 0, 0, 0))
                pygame.draw.circle(self.image, (255, 255, 0), (25, 25), self.radius)
                self.image.set_alpha(255 - (self.radius / self.max_radius) * 255)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speedx, speedy, bullet_type="player"):
        super().__init__()
        self.bullet_type = bullet_type
        if self.bullet_type == "player":
            self.image = pygame.Surface([5, 10])
            self.image.fill(WHITE)
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

        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speedx = speedx
        self.speedy = speedy
        self.grazed = False

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if not screen.get_rect().colliderect(self.rect):
            self.kill()

def draw_ui():
    ui_surface = pygame.Surface((UI_WIDTH, SCREEN_HEIGHT))
    ui_surface.fill((50, 50, 50))
    draw_text(ui_surface, f"Score: {player.score}", 18, UI_WIDTH / 2, 10)
    draw_text(ui_surface, f"Lives: {player.lives}", 18, UI_WIDTH / 2, 40)
    draw_text(ui_surface, f"Bombs: {player.bombs}", 18, UI_WIDTH / 2, 70)
    draw_text(ui_surface, f"Power: {player.power}", 18, UI_WIDTH / 2, 100)
    draw_text(ui_surface, f"Graze: {player.graze}", 18, UI_WIDTH / 2, 130)
    draw_text(ui_surface, f"Stage: {player.stage}", 18, UI_WIDTH / 2, 160)
    render_surface.blit(ui_surface, (SCREEN_WIDTH, 0))

def draw_boss_health_bar(surf, x, y, pct):
    if pct < 0: pct = 0
    BAR_LENGTH = SCREEN_WIDTH - 20
    BAR_HEIGHT = 10
    fill = (pct / 100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

def show_go_screen(clock):
    render_surface.fill(BLACK)
    draw_text(render_surface, "Aetherium Machina", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
    draw_text(render_surface, "Arrow keys to move, Z to shoot, X to bomb", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    draw_text(render_surface, "Press any key to begin", 18, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4)
    screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit()
            if event.type == pygame.KEYUP: waiting = False

def save_game(player):
    with open(SAVE_FILE, 'w') as f:
        json.dump({"lives": player.lives, "bombs": player.bombs, "power": player.power, 
                   "score": player.score, "graze": player.graze, "stage": player.stage}, f)

def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f: return json.load(f)
    return None

def fade_to_black(duration):
    fade_surface = pygame.Surface((SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill(BLACK)
    for alpha in range(0, 256, 5):
        fade_surface.set_alpha(alpha)
        render_surface.blit(fade_surface, (0, 0))
        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()
        pygame.time.delay(duration // (256 // 5))


def title_screen():
    pygame.mixer.music.load("media/OST/Title.wav")
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)
    title_image = pygame.image.load("media/images/titleImage.jpg").convert_alpha()
    title_image = pygame.transform.scale(title_image, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
    game_logo = pygame.image.load("media/images/gameLogo.png").convert_alpha()
    game_logo_rect = game_logo.get_rect(center=((SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 4))
    menu_options = ["NEW GAME", "LOAD", "SETTINGS", "EXIT"]
    selected_option = 0
    cursor_image = pygame.image.load("media/images/cursor.png").convert_alpha()
    font_name = pygame.font.match_font('timesnewroman') # Using a serif font
    option_font = pygame.font.Font(font_name, 25)
    font_height = option_font.get_height()
    cursor_image = pygame.transform.scale(cursor_image, (int(font_height * 1.5), int(font_height * 1.5)))

    while True:
        render_surface.blit(title_image, (0, 0))
        render_surface.blit(game_logo, game_logo_rect)

        total_width = 0
        option_font = pygame.font.Font(font_name, 25)

        for option in menu_options:
            total_width += option_font.size(option)[0]
        total_width += 50 * (len(menu_options) - 1)

        box_width = total_width + 100
        box_height = 80
        box_x = (SCREEN_WIDTH + UI_WIDTH) / 2 - box_width / 2
        box_y = SCREEN_HEIGHT - 80
        menu_box = pygame.Surface((box_width, box_height))
        menu_box.set_alpha(200)
        menu_box.fill(BLACK)
        render_surface.blit(menu_box, (box_x, box_y))

        start_x = (SCREEN_WIDTH + UI_WIDTH) / 2 - total_width / 2
        menu_y = SCREEN_HEIGHT - 40
        
        current_x = start_x
        for i, option in enumerate(menu_options):
            color = WHITE if i == selected_option else (150, 150, 150)
            text_surface = option_font.render(option, True, color)
            text_rect = text_surface.get_rect(centery=menu_y)
            text_rect.x = current_x

            if i == selected_option:
                cursor_rect = cursor_image.get_rect(centery=menu_y)
                cursor_rect.right = text_rect.left - 5
                render_surface.blit(cursor_image, cursor_rect)

            render_surface.blit(text_surface, text_rect)
            current_x += text_rect.width + 50

        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.mixer.music.stop()
                return "EXIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected_option = (selected_option - 1) % len(menu_options)
                    select_sound.play()
                elif event.key == pygame.K_RIGHT:
                    selected_option = (selected_option + 1) % len(menu_options)
                    select_sound.play()
                elif event.key == pygame.K_RETURN:
                    pygame.mixer.music.stop()
                    return menu_options[selected_option]


resolutions = [(800, 600), (1024, 720), (1366, 768), (1600, 900), (1920, 1080)]


def options_screen():
    global screen, NATIVE_WIDTH, NATIVE_HEIGHT, render_surface
    selected_resolution_index = 0
    options_image = pygame.image.load("media/images/template menu.png").convert()
    options_image = pygame.transform.scale(options_image, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
    while True:
        render_surface.blit(options_image, (0, 0))
        draw_text(render_surface, "Options", 64, (SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 4)
        for i, res in enumerate(resolutions):
            size = 30 if i == selected_resolution_index else 25
            color = WHITE if i == selected_resolution_index else (150, 150, 150)
            font = pygame.font.Font(font_name, size)
            text_surface = font.render(f"{res[0]}x{res[1]}", True, color)
            text_rect = text_surface.get_rect(midtop=((SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 2 + i * 40))
            render_surface.blit(text_surface, text_rect)
        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_resolution_index = (selected_resolution_index - 1) % len(resolutions)
                    select_sound.play()
                elif event.key == pygame.K_DOWN:
                    selected_resolution_index = (selected_resolution_index + 1) % len(resolutions)
                    select_sound.play()
                elif event.key == pygame.K_RETURN:
                    NATIVE_WIDTH, NATIVE_HEIGHT = resolutions[selected_resolution_index]
                    screen_info = pygame.display.Info()
                    x = (screen_info.current_w - (NATIVE_WIDTH + UI_WIDTH)) // 2
                    y = (screen_info.current_h - NATIVE_HEIGHT) // 2
                    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
                    screen = pygame.display.set_mode((NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
                    render_surface = pygame.Surface((SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT))
                    return
                elif event.key == pygame.K_ESCAPE:
                    return

all_sprites = pygame.sprite.Group()
player_sprite = pygame.sprite.GroupSingle()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()
beams = pygame.sprite.Group()
player = Player()

def game_loop(new_game=True):
    global game_over, running, player, all_sprites, player_sprite, bullets, enemies, enemy_bullets, powerups, bosses

    player = Player()
    if not new_game:
        saved_data = load_game()
        if saved_data:
            for key, value in saved_data.items(): setattr(player, key, value)

    all_sprites = pygame.sprite.Group(player)
    player_sprite = pygame.sprite.GroupSingle(player)
    bullets, enemies, enemy_bullets, powerups, bosses = (pygame.sprite.Group() for _ in range(5))
    beams.empty()

    stage_manager = StageManager(player, all_sprites, enemies, enemy_bullets, bosses)
    game_over = False
    running = True
    clock = pygame.time.Clock()

    while running:
        if game_over:
            pygame.mixer.Channel(0).stop()
            show_go_screen(clock)
            return

        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.mixer.Channel(0).stop()
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x: player.use_bomb()
                if event.key == pygame.K_q: player.weapon_manager.switch_weapon()
                if event.key == pygame.K_ESCAPE: 
                    pygame.mixer.Channel(0).stop()
                    save_game(player); 
                    return

        all_sprites.update()
        stage_manager.update()

        beam_hits = pygame.sprite.groupcollide(enemies, beams, False, False)
        for enemy, hit_beams in beam_hits.items():
            for beam in hit_beams:
                enemy.debuffs["damage_vulnerability"] = {"start_time": pygame.time.get_ticks(), "duration": 10000}
                enemy.health -= 1
            if enemy.health <= 0:
                player.score += 100
                powerup = PowerUp(enemy.rect.center)
                all_sprites.add(powerup)
                powerups.add(powerup)
                enemy.kill()

        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy, hit_bullets in hits.items():
            for bullet in hit_bullets:
                if isinstance(bullet, HomingMissile):
                    damage = 5
                    if "damage_vulnerability" in enemy.debuffs:
                        damage *= 1.5
                    enemy.health -= damage
                else:
                    damage = 10
                    if "damage_vulnerability" in enemy.debuffs:
                        damage *= 1.5
                    enemy.health -= damage

            if enemy.health <= 0:
                player.score += 100
                powerup = PowerUp(enemy.rect.center)
                all_sprites.add(powerup)
                powerups.add(powerup)
                enemy.kill()

        if bosses:
            boss_beam_hits = pygame.sprite.groupcollide(bosses, beams, False, False)
            for boss, hit_beams in boss_beam_hits.items():
                for beam in hit_beams:
                    boss.debuffs["damage_vulnerability"] = {"start_time": pygame.time.get_ticks(), "duration": 10000}
                    boss.health -= 1
                if boss.health <= 0:
                    boss.kill()
                    player.score += 10000
                    save_game(player)

            hits = pygame.sprite.groupcollide(bosses, bullets, False, True)
            for boss, hit_bullets in hits.items():
                damage = 10 * len(hit_bullets)
                if "damage_vulnerability" in boss.debuffs:
                    damage *= 1.5
                boss.health -= damage
                if boss.health <= 0:
                    boss.kill()
                    player.score += 10000
                    save_game(player)

        if pygame.sprite.spritecollide(player, enemy_bullets, True, pygame.sprite.collide_mask) and not player.invincible:
            player.die()

        if player.lives <= 0:
            game_over = True

        if player.rect.y < 150:
            for powerup in powerups:
                powerup.rect.x += (player.rect.centerx - powerup.rect.centerx) / 10
                powerup.rect.y += (player.rect.centery - powerup.rect.centery) / 10
        
        for hit in pygame.sprite.spritecollide(player, powerups, True):
            player.power += 1

        for bullet in enemy_bullets:
            if not bullet.grazed and pygame.math.Vector2(player.rect.center).distance_to(bullet.rect.center) < 50:
                player.graze += 1
                bullet.grazed = True

        render_surface.fill(BLACK)
        all_sprites.draw(render_surface)
        player.draw_hitbox(render_surface)
        for boss in bosses:
            draw_boss_health_bar(render_surface, 5, 5, (boss.health / boss.max_health) * 100)
        draw_ui()
        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()

def splash_screen():
    splash_image = pygame.image.load("media/images/splashScreen.png").convert_alpha()
    splash_image = pygame.transform.scale(splash_image, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
    title_image = pygame.image.load("media/images/titleImage.jpg").convert_alpha()
    title_image = pygame.transform.scale(title_image, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))

    # Fade in splash
    for alpha in range(0, 256, 5):
        splash_image.set_alpha(alpha)
        render_surface.fill(BLACK)
        render_surface.blit(splash_image, (0, 0))
        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)

    pygame.time.delay(2000)

    # Fade out splash and fade in title
    for alpha in range(0, 256, 5):
        splash_image.set_alpha(255 - alpha)
        title_image.set_alpha(alpha)
        render_surface.fill(BLACK)
        render_surface.blit(splash_image, (0, 0))
        render_surface.blit(title_image, (0, 0))
        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)

if __name__ == "__main__":
    splash_screen()
    while True:
        choice = title_screen()
        if choice == "NEW GAME":
            start_game_sound.play()
            fade_to_black(1000)
            pygame.time.delay(2000)
            game_loop()
        elif choice == "LOAD":
            game_loop(new_game=False)
        elif choice == "SETTINGS":
            options_screen()
        elif choice == "EXIT":
            break
    pygame.quit()
