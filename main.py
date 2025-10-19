import pygame
import random
import math
import json
import os
from Enemy import Bullet, HomingMissile
from stages.stage1 import Stage1, Stage2, Stage3, Stage4, Stage5, Stage6, Stage7
from config import SCREEN_WIDTH, SCREEN_HEIGHT, UI_WIDTH, settings

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
pygame.mixer.init()

# Screen dimensions
NATIVE_WIDTH = 800
NATIVE_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Create the screen
screen = pygame.display.set_mode((NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
render_surface = pygame.Surface((SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT))
game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aetherium Machina")

font_name = pygame.font.match_font('arial')

sfx = {
    "death": pygame.mixer.Sound("media/sfx/death.wav"),
    "select": pygame.mixer.Sound("media/sfx/Select.wav"),
    "start_game": pygame.mixer.Sound("media/sfx/startNewGame.wav"),
    "shooting": pygame.mixer.Sound("media/sfx/rapidFireLoop.wav"),
    "beam": pygame.mixer.Sound("media/sfx/Laser.wav"),
    "error": pygame.mixer.Sound("media/sfx/Error.wav")
}

def set_sfx_volume(volume):
    for sound in sfx.values():
        sound.set_volume(volume)

set_sfx_volume(settings.sfx_volume)
pygame.mixer.music.set_volume(settings.music_volume)

# Screen dimensions

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
    def __init__(self, player, enemies):
        self.player = player
        self.weapons = {
            "active": [DefaultWeapon(), BeamCannon()],
            "passive": [HomingMissiles(enemies)]
        }
        self.active_weapon_index = 0

    def shoot_active(self, frame_count):
        self.weapons["active"][self.active_weapon_index].shoot(self.player, frame_count)

    def shoot_passive(self, frame_count):
        for weapon in self.weapons["passive"]:
            weapon.shoot(self.player, frame_count)

    def switch_weapon(self):
        self.active_weapon_index = (self.active_weapon_index + 1) % len(self.weapons["active"])

class WeaponUI:
    def __init__(self, weapon_manager):
        self.weapon_manager = weapon_manager
        self.center_x = UI_WIDTH // 2
        self.center_y = 300
        self.weapon_icon_size = (40, 40)

    def draw(self, surface):
        active_weapons = self.weapon_manager.weapons["active"]
        passive_weapons = self.weapon_manager.weapons["passive"]
        all_weapons = active_weapons + passive_weapons
        num_weapons = len(all_weapons)
        if num_weapons == 0:
            return

        start_x = self.center_x - (num_weapons * 60) // 2
        y = self.center_y

        for i, weapon in enumerate(all_weapons):
            x = start_x + i * 60

            # Draw a circle for the weapon
            is_selected = False
            if weapon.weapon_type == "active" and weapon == active_weapons[self.weapon_manager.active_weapon_index]:
                is_selected = True
            else:
                is_selected = False
            
            color = WHITE if is_selected and weapon.weapon_type == "active" else (100, 100, 100)

            radius = 30 if is_selected else 25
            pygame.draw.circle(surface, color, (int(x), int(y)), radius, 2)

            # Draw weapon name
            font_size = 20 if is_selected else 16
            font = pygame.font.Font(font_name, font_size)
            if weapon.weapon_type == "passive":
                text_color = (150, 150, 150)
                type_text_color = (150, 150, 150)
            else:
                text_color = WHITE
                type_text_color = WHITE
            text = font.render(weapon.name, True, text_color)
            text_rect = text.get_rect(center=(x, y))
            surface.blit(text, text_rect)

            # Draw A or P
            type_text_content = "A" if weapon.weapon_type == "active" else "P"
            type_font = pygame.font.Font(font_name, 12)
            type_text = type_font.render(type_text_content, True, type_text_color)
            type_text_rect = type_text.get_rect(center=(x, y + 30))
            surface.blit(type_text, type_text_rect)

class DefaultWeapon(Weapon):
    def __init__(self):
        super().__init__("Default", "active")

    def shoot(self, player, frame_count):
        if frame_count - player.last_shot > player.shoot_delay:
            player.last_shot = frame_count
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
    def __init__(self, x, y, frame_count):
        super().__init__()
        self.image = pygame.Surface([40, SCREEN_HEIGHT])
        self.image.fill(RED)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.spawn_time = frame_count

    def update(self, frame_count):
        if frame_count - self.spawn_time > 12:
            self.kill()

class BeamCannon(Weapon):
    def __init__(self):
        super().__init__("Beam Cannon", "active")
        self.last_shot = 0
        self.shoot_delay = 120
        self.beam_sound = sfx["beam"]

    def shoot(self, player, frame_count):
        if frame_count - self.last_shot > self.shoot_delay:
            self.last_shot = frame_count
            beam = Beam(player.rect.centerx, player.rect.top, frame_count)
            all_sprites.add(beam)
            beams.add(beam)



class HomingMissiles(Weapon):
    def __init__(self, enemies):
        super().__init__("Homing Missiles", "passive")
        self.last_shot = 0
        self.shoot_delay = 120
        self.enemies = enemies

    def shoot(self, player, frame_count):
        if frame_count - self.last_shot > self.shoot_delay:
            self.last_shot = frame_count
            missile1 = HomingMissile(player.rect.left, player.rect.centery, -2, -7, self.enemies)
            missile2 = HomingMissile(player.rect.right, player.rect.centery, 2, -7, self.enemies)
            all_sprites.add(missile1, missile2)
            bullets.add(missile1, missile2)

class Player(pygame.sprite.Sprite):
    def __init__(self, enemies):
        super().__init__()
        self.original_image = pygame.image.load("media/images/robin.webp").convert()
        self.original_image.set_colorkey(WHITE)
        self.image = pygame.transform.scale(self.original_image, (40, 40))
        self.image_orig = self.image.copy()
        self.mask = pygame.mask.from_surface(self.image)
        self.flicker_interval = 150
        self.i_frame_duration = 3000
        self.rect = self.image.get_rect()
        self.position = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 10)
        self.rect.center = self.position
        self.speed = 7.5
        self.focused = False
        self.last_shot = 0
        self.shoot_delay = 6
        self.lives = 3
        self.bombs = 3
        self.power = 0
        self.score = 0
        self.graze = 0
        self.invincible = False
        self.invincible_timer = 0
        self.stage = 1
        self.shooting_sound = sfx["shooting"]
        self.weapon_manager = WeaponManager(self, enemies)
        self.weapon_ui = WeaponUI(self.weapon_manager)
        self.angle = 0

    def update(self, frame_count):
        self.angle = (self.angle + 5) % 360
        new_image = pygame.transform.rotate(self.image_orig, self.angle)
        old_center = self.rect.center
        self.image = new_image
        self.rect = self.image.get_rect()
        self.rect.center = old_center

        keys = pygame.key.get_pressed()
        self.speed = 2.5 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 7.5
        self.focused = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if self.focused:
            hitbox_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(hitbox_surface, (255, 255, 255, 255), (self.rect.width // 2 - 6, self.rect.height // 2 - 6, 12, 12))
            self.mask = pygame.mask.from_surface(hitbox_surface)
        else:
            self.mask = pygame.mask.from_surface(self.image)
        self.focused = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if keys[pygame.K_UP] and self.rect.top > 0:
            self.position.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.position.y += self.speed
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.position.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.position.x += self.speed

        self.rect.center = self.position
        
        if keys[pygame.K_z]:
            self.shoot(frame_count)
        else:
            pygame.mixer.Channel(0).stop()

        if self.invincible:
            if frame_count - self.invincible_timer > 180:
                self.invincible = False
                try:
                    self.image.set_alpha(255)
                except Exception:
                    pass
            else:
                step = ((frame_count - self.invincible_timer) // 9) % 2
                self.image.set_alpha(255 if step == 0 else 0)
        else:
            try:
                self.image.set_alpha(255)
            except Exception:
                pass

    def shoot(self, frame_count):
        self.weapon_manager.shoot_active(frame_count)
        self.weapon_manager.shoot_passive(frame_count)

    def use_bomb(self):
        if self.bombs > 0:
            self.bombs -= 1
            for enemy in enemies:
                enemy.kill()
            for bullet in enemy_bullets:
                bullet.kill()

    def die(self, frame_count):
        self.lives -= 1
        pygame.mixer.Channel(1).play(sfx["death"])
        explosion = Explosion(self.rect.center, frame_count)
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
        self.invincible_timer = frame_count

    def draw_hitbox(self, surface):
        if self.focused:
            pygame.draw.rect(surface, RED, (self.rect.centerx - 6, self.rect.centery - 6, 12, 12))




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

    def update(self, frame_count):
        self.current_stage.update(frame_count)
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

    def update(self, frame_count):
        self.rect.y += self.speedy
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, frame_count):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.radius = 1
        self.max_radius = 50
        self.animation_speed = 2
        self.last_update = frame_count

    def update(self, frame_count):
        if frame_count - self.last_update > self.animation_speed:
            self.last_update = frame_count
            self.radius += 1
            if self.radius >= self.max_radius:
                self.kill()
            else:
                self.image.fill((0, 0, 0, 0))
                pygame.draw.circle(self.image, (255, 255, 0), (25, 25), self.radius)
                self.image.set_alpha(255 - (self.radius / self.max_radius) * 255)

class WelcomeAnimation:
    def __init__(self, frame_count):
        self.font = pygame.font.Font(font_name, 48)
        self.text = "WELCOME TO THE TRAINING GROUND"
        self.text_surface = self.font.render(self.text, True, WHITE)
        self.text_rect = self.text_surface.get_rect()
        self.text_rect.centery = SCREEN_HEIGHT / 2
        
        self.start_time = frame_count
        self.finished = False
        self.state = 'fade_in' # 'fade_in', 'pause', 'fade_out'

        self.fade_in_duration = 60
        self.pause_duration = 180
        self.fade_out_duration = 30

        self.start_pos_x = SCREEN_WIDTH * 0.25
        self.mid_pos_x = SCREEN_WIDTH * 0.5
        self.end_pos_x = SCREEN_WIDTH * 0.75

    def update(self, frame_count):
        if self.finished:
            return

        elapsed = frame_count - self.start_time

        if self.state == 'fade_in':
            if elapsed > self.fade_in_duration:
                self.state = 'pause'
                self.start_time = frame_count # Reset timer for next state
                elapsed = 0
            
            progress = elapsed / self.fade_in_duration
            self.text_rect.centerx = self.start_pos_x + (self.mid_pos_x - self.start_pos_x) * progress
            alpha = int(255 * progress)
            self.text_surface.set_alpha(alpha)

        elif self.state == 'pause':
            if elapsed > self.pause_duration:
                self.state = 'fade_out'
                self.start_time = frame_count # Reset timer for next state
                elapsed = 0
            
            self.text_rect.centerx = self.mid_pos_x
            self.text_surface.set_alpha(255)

        elif self.state == 'fade_out':
            if elapsed > self.fade_out_duration:
                self.finished = True
                return
                
            progress = elapsed / self.fade_out_duration
            self.text_rect.centerx = self.mid_pos_x + (self.end_pos_x - self.mid_pos_x) * progress
            alpha = int(255 * (1 - progress))
            self.text_surface.set_alpha(alpha)

    def draw(self, surface):
        if not self.finished:
            surface.blit(self.text_surface, self.text_rect)

def draw_ui(player):
    font_name = pygame.font.match_font('arial')
    global fullscreen_mode
    if fullscreen_mode:
        return
    ui_surface = pygame.Surface((UI_WIDTH, SCREEN_HEIGHT))
    ui_surface.fill((50, 50, 50))
    draw_text(ui_surface, f"Score: {player.score}", 18, UI_WIDTH / 2, 10)
    draw_text(ui_surface, f"Lives: {player.lives}", 18, UI_WIDTH / 2, 40)
    draw_text(ui_surface, f"Bombs: {player.bombs}", 18, UI_WIDTH / 2, 70)
    draw_text(ui_surface, f"Power: {player.power}", 18, UI_WIDTH / 2, 100)
    draw_text(ui_surface, f"Graze: {player.graze}", 18, UI_WIDTH / 2, 130)
    draw_text(ui_surface, f"Stage: {player.stage}", 18, UI_WIDTH / 2, 160)
    player.weapon_ui.draw(ui_surface)
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
                    sfx["select"].play()
                elif event.key == pygame.K_RIGHT:
                    selected_option = (selected_option + 1) % len(menu_options)
                    sfx["select"].play()
                elif event.key == pygame.K_RETURN:
                    pygame.mixer.music.stop()
                    return menu_options[selected_option]




fullscreen_mode = False

def options_screen():
    global screen, NATIVE_WIDTH, NATIVE_HEIGHT, render_surface, fullscreen_mode
    
    options = ["Display Mode", "Music Volume", "SFX Volume", "Back"]
    selected_option_index = 0
    
    display_modes = ["Windowed", "Fullscreen", "Borderless"]
    selected_mode_index = 0

    options_image = pygame.image.load("media/images/template menu.png").convert()
    options_image = pygame.transform.scale(options_image, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))

    while True:
        render_surface.blit(options_image, (0, 0))
        draw_text(render_surface, "Options", 64, (SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 4)

        for i, option in enumerate(options):
            size = 30 if i == selected_option_index else 25
            color = WHITE if i == selected_option_index else (150, 150, 150)
            
            if option == "Display Mode":
                display_text = f"Display Mode: {display_modes[selected_mode_index]}"
                font = pygame.font.Font(font_name, size)
                text_surface = font.render(display_text, True, color)
                text_rect = text_surface.get_rect(midtop=((SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 2 + i * 60))
                render_surface.blit(text_surface, text_rect)
            elif option == "Music Volume":
                # Draw slider
                slider_x = (SCREEN_WIDTH + UI_WIDTH) / 2 - 100
                slider_y = SCREEN_HEIGHT / 2 + i * 60
                slider_width = 200
                slider_height = 20
                
                # Draw text
                font = pygame.font.Font(font_name, size)
                text_surface = font.render(f"Music Volume: {int(settings.music_volume * 100)}%", True, color)
                text_rect = text_surface.get_rect(midtop=((SCREEN_WIDTH + UI_WIDTH) / 2, slider_y - 30))
                render_surface.blit(text_surface, text_rect)

                # Draw slider bar
                pygame.draw.rect(render_surface, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
                pygame.draw.rect(render_surface, WHITE, (slider_x, slider_y, slider_width * settings.music_volume, slider_height))
            elif option == "SFX Volume":
                # Draw slider
                slider_x = (SCREEN_WIDTH + UI_WIDTH) / 2 - 100
                slider_y = SCREEN_HEIGHT / 2 + i * 60
                slider_width = 200
                slider_height = 20

                # Draw text
                font = pygame.font.Font(font_name, size)
                text_surface = font.render(f"SFX Volume: {int(settings.sfx_volume * 100)}%", True, color)
                text_rect = text_surface.get_rect(midtop=((SCREEN_WIDTH + UI_WIDTH) / 2, slider_y - 30))
                render_surface.blit(text_surface, text_rect)

                # Draw slider bar
                pygame.draw.rect(render_surface, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
                pygame.draw.rect(render_surface, WHITE, (slider_x, slider_y, slider_width * settings.sfx_volume, slider_height))
            else: # Back button
                font = pygame.font.Font(font_name, size)
                text_surface = font.render(option, True, color)
                text_rect = text_surface.get_rect(midtop=((SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 2 + i * 60))
                render_surface.blit(text_surface, text_rect)


        if fullscreen_mode:
            screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH, NATIVE_HEIGHT)), (0, 0))
        else:
            screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                settings.save()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option_index = (selected_option_index - 1) % len(options)
                    sfx["select"].play()
                elif event.key == pygame.K_DOWN:
                    selected_option_index = (selected_option_index + 1) % len(options)
                    sfx["select"].play()
                elif event.key == pygame.K_LEFT:
                    if options[selected_option_index] == "Display Mode":
                        selected_mode_index = (selected_mode_index - 1) % len(display_modes)
                    elif options[selected_option_index] == "Music Volume":
                        settings.music_volume = max(0.0, settings.music_volume - 0.05)
                        pygame.mixer.music.set_volume(settings.music_volume)
                    elif options[selected_option_index] == "SFX Volume":
                        settings.sfx_volume = max(0.0, settings.sfx_volume - 0.05)
                        set_sfx_volume(settings.sfx_volume)
                        sfx["select"].play()

                elif event.key == pygame.K_RIGHT:
                    if options[selected_option_index] == "Display Mode":
                        selected_mode_index = (selected_mode_index + 1) % len(display_modes)
                    elif options[selected_option_index] == "Music Volume":
                        settings.music_volume = min(1.0, settings.music_volume + 0.05)
                        pygame.mixer.music.set_volume(settings.music_volume)
                    elif options[selected_option_index] == "SFX Volume":
                        settings.sfx_volume = min(1.0, settings.sfx_volume + 0.05)
                        set_sfx_volume(settings.sfx_volume)
                        sfx["select"].play()

                elif event.key == pygame.K_RETURN:
                    if options[selected_option_index] == "Display Mode":
                        selected_mode = display_modes[selected_mode_index]
                        screen_info = pygame.display.Info()
                        if selected_mode == "Windowed":
                            fullscreen_mode = False
                            NATIVE_WIDTH, NATIVE_HEIGHT = 800, 600
                            x = (screen_info.current_w - (NATIVE_WIDTH + UI_WIDTH)) // 2
                            y = (screen_info.current_h - NATIVE_HEIGHT) // 2
                            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
                            screen = pygame.display.set_mode((NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
                            render_surface = pygame.Surface((SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT))
                        elif selected_mode == "Fullscreen":
                            fullscreen_mode = True
                            NATIVE_WIDTH, NATIVE_HEIGHT = screen_info.current_w, screen_info.current_h
                            screen = pygame.display.set_mode((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.FULLSCREEN)
                            render_surface = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
                        elif selected_mode == "Borderless":
                            fullscreen_mode = True
                            NATIVE_WIDTH, NATIVE_HEIGHT = screen_info.current_w, screen_info.current_h
                            os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
                            screen = pygame.display.set_mode((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.NOFRAME)
                            render_surface = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
                    elif options[selected_option_index] == "Back":
                        settings.save()
                        return
                elif event.key == pygame.K_ESCAPE:
                    settings.save()
                    return

all_sprites = pygame.sprite.Group()
player_sprite = pygame.sprite.GroupSingle()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()
beams = pygame.sprite.Group()

def pause_menu(screen, render_surface):
    menu_options = ["Continue", "Quit to Main Menu"]
    selected_option = 0
    font_name = pygame.font.match_font('arial')
    option_font = pygame.font.Font(font_name, 30)
    paused_font = pygame.font.Font(font_name, 64)

    overlay = pygame.Surface((NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    while True:
        render_surface.blit(overlay, (0, 0))

        paused_text = paused_font.render("Paused", True, WHITE)
        paused_rect = paused_text.get_rect(center=((SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 4))
        render_surface.blit(paused_text, paused_rect)

        for i, option in enumerate(menu_options):
            color = WHITE if i == selected_option else (150, 150, 150)
            text_surface = option_font.render(option, True, color)
            text_rect = text_surface.get_rect(center=((SCREEN_WIDTH + UI_WIDTH) / 2, SCREEN_HEIGHT / 2 + i * 50))
            render_surface.blit(text_surface, text_rect)

        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                    sfx["select"].play()
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                    sfx["select"].play()
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:
                        return "CONTINUE"
                    elif selected_option == 1:
                        return "QUIT"
                elif event.key == pygame.K_ESCAPE:
                    return "CONTINUE"

def game_loop(new_game=True):
    global game_over, running, all_sprites, player_sprite, bullets, enemies, enemy_bullets, powerups, bosses

    frame_count = 0

    enemies = pygame.sprite.Group()
    player = Player(enemies)
    if not new_game:
        saved_data = load_game()
        if saved_data:
            for key, value in saved_data.items(): setattr(player, key, value)

    all_sprites = pygame.sprite.Group(player)
    player_sprite = pygame.sprite.GroupSingle(player)
    bullets, enemy_bullets, powerups, bosses = (pygame.sprite.Group() for _ in range(4))
    beams.empty()

    stage_manager = StageManager(player, all_sprites, enemies, enemy_bullets, bosses)
    
    welcome_animation = None
    if new_game and player.stage == 1:
        welcome_animation = WelcomeAnimation(frame_count)

    stage_music_playing = False

    game_over = False
    running = True
    clock = pygame.time.Clock()

    frame_count = 0

    while running:
        if game_over:
            pygame.mixer.Channel(0).stop()
            show_go_screen(clock)
            return

        clock.tick(60)
        frame_count += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.mixer.Channel(0).stop()
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x: player.use_bomb()
                if event.key == pygame.K_q: player.weapon_manager.switch_weapon()
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.Channel(0).stop()
                    action = pause_menu(screen, render_surface)
                    if action == "QUIT":
                        save_game(player)
                        return


        all_sprites.update(frame_count)

        if welcome_animation:
            welcome_animation.update(frame_count)
            if welcome_animation.finished:
                if not stage_music_playing:
                    pygame.mixer.music.load("media/OST/stage1-normal.wav")
                    pygame.mixer.music.set_volume(0.25)
                    pygame.mixer.music.play(-1)
                    stage_music_playing = True

                welcome_animation = None
        else:
            stage_manager.update(frame_count)

        beam_hits = pygame.sprite.groupcollide(enemies, beams, False, False)
        for enemy, hit_beams in beam_hits.items():
            for beam in hit_beams:
                enemy.debuffs["damage_vulnerability"] = {"start_time": frame_count, "duration": 600}
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
                    boss.debuffs["damage_vulnerability"] = {"start_time": frame_count, "duration": 600}
                    damage = 1 # beam damage
                    if boss.health / boss.max_health < 0.25:
                        damage *= 0.1
                    boss.health -= damage
                if boss.health <= 0:
                    boss.kill()
                    player.score += 10000
                    save_game(player)

            hits = pygame.sprite.groupcollide(bosses, bullets, False, True)
            for boss, hit_bullets in hits.items():
                damage = 10 * len(hit_bullets)
                if "damage_vulnerability" in boss.debuffs:
                    damage *= 1.5
                
                if boss.health / boss.max_health < 0.25:
                    damage *= 0.1

                boss.health -= damage
                if boss.health <= 0:
                    boss.kill()
                    player.score += 10000
                    save_game(player)

        if pygame.sprite.spritecollide(player, enemy_bullets, True, pygame.sprite.collide_mask) and not player.invincible:
            player.die(frame_count)

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

        game_surface.fill(BLACK)
        all_sprites.draw(game_surface)
        if welcome_animation:
            welcome_animation.draw(game_surface)
        player.draw_hitbox(game_surface)
        for boss in bosses:
            draw_boss_health_bar(game_surface, 5, 5, (boss.health / boss.max_health) * 100)

        if fullscreen_mode:
            scaled_game_surface = pygame.transform.scale(game_surface, (NATIVE_WIDTH, NATIVE_HEIGHT))
            screen.blit(scaled_game_surface, (0, 0))
        else:
            render_surface.fill(BLACK)
            render_surface.blit(game_surface, (0, 0))
            draw_ui(player)
            screen.blit(render_surface, (0, 0))

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

def chapter_screen():
    chapter_image = pygame.image.load("media/images/Chapter1.jpg").convert()
    chapter_image = pygame.transform.scale(chapter_image, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT))
    next_button_rect = pygame.Rect((SCREEN_WIDTH + UI_WIDTH) / 2 - 50, SCREEN_HEIGHT - 100, 100, 50)
    
    # Fade in
    for alpha in range(0, 256, 5):
        chapter_image.set_alpha(alpha)
        render_surface.blit(chapter_image, (0, 0))
        pygame.draw.rect(render_surface, BLACK, next_button_rect)
        draw_text(render_surface, "NEXT", 30, next_button_rect.centerx, next_button_rect.centery - 15)
        screen.blit(pygame.transform.scale(render_surface, (NATIVE_WIDTH + UI_WIDTH, NATIVE_HEIGHT)), (0, 0))
        pygame.display.flip()
        pygame.time.delay(10)

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "EXIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if next_button_rect.collidepoint(event.pos):
                    waiting = False
    
    # Fade out
    fade_to_black(1000)
    return "START"

if __name__ == "__main__":
    splash_screen()
    while True:
        choice = title_screen()
        if choice == "NEW GAME":
            sfx["start_game"].play()
            action = chapter_screen()
            if action == "START":
                game_loop()
        elif choice == "LOAD":
            game_loop(new_game=False)
        elif choice == "SETTINGS":
            options_screen()
        elif choice == "EXIT":
            break
    pygame.quit()
