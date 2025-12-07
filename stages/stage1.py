import pygame
import random
import os
from Enemy import Tutorial_Square, EnemyTypeB, EnemyTypeC, BossTypeA, Miniboss, pattern_simple_shot, pattern_burst_shot, pattern_spiral_shot, pattern_triple_shot, pattern_aimed_shot, pattern_emerald_shot, Bullet
from config import SCREEN_WIDTH, SCREEN_HEIGHT

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DIALOGUE_BOX_COLOR = (40, 26, 13) # Dark Wood/Steampunk background
DIALOGUE_BORDER_COLOR = (181, 166, 66) # Brass

# --- 3D BACKGROUND COLORS ---
DEEP_BLUE_BG = (5, 5, 25)     # สีน้ำเงินเข้มเกือบดำ (Void)
WIRE_BLUE = (0, 200, 255)     # สีฟ้าสะท้อนแสง (Cyber/Neon)

def lerp(start, end, factor):
    return start + (end - start) * factor

class DialogueCharacter:
    def __init__(self, name, relative_path, position_side, height=450, max_width=350, show_full_body=False):
        self.name = name
        self.position_side = position_side # 'left' or 'right'
        
        # Load Image logic
        possible_paths = [
            relative_path,
            os.path.join("media", "images", relative_path),
            os.path.join("media", relative_path),
            os.path.join("media", "Sprite", "Character", os.path.basename(relative_path))
        ]

        found_path = None
        for path in possible_paths:
            clean_path = path.replace("/", os.sep).replace("\\", os.sep)
            if os.path.exists(clean_path):
                found_path = clean_path
                break
        
        if found_path:
            try:
                loaded_img = pygame.image.load(found_path).convert_alpha()
                scale_h = height / loaded_img.get_height()
                scale_w = max_width / loaded_img.get_width()
                final_scale = min(scale_h, scale_w)
                new_size = (int(loaded_img.get_width() * final_scale), int(loaded_img.get_height() * final_scale))
                self.normal_image = pygame.transform.scale(loaded_img, new_size)
            except Exception as e:
                print(f"[ERROR] Found file but could not load {name}: {e}")
                self.create_placeholder(height, max_width)
        else:
            print(f"[ERROR] Could not find image for {name} in any expected location.")
            self.create_placeholder(height, max_width)

        # Create Dimmed Version
        if hasattr(self, 'normal_image'):
            self.dimmed_image = self.normal_image.copy()
            darkener = pygame.Surface(self.normal_image.get_size()).convert_alpha()
            darkener.fill((0, 0, 0, 100)) 
            self.dimmed_image.blit(darkener, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # --- POSITION LOGIC ---
        if hasattr(self, 'normal_image'):
            self.w = self.normal_image.get_width()
            self.h = self.normal_image.get_height()
            
            # Y Positions
            dialogue_box_top_y = SCREEN_HEIGHT - 170
            if show_full_body:
                self.target_y = dialogue_box_top_y - self.h + 15
            else:
                self.target_y = SCREEN_HEIGHT - self.h

            # X Positions (Idle vs Active vs Off-screen)
            if position_side == 'left':
                self.idle_x = 50
                self.active_x = 80 # Move RIGHT when talking
                self.off_screen_x = -self.w - 20 # Start off-screen LEFT
            else:
                self.idle_x = SCREEN_WIDTH - self.w - 50
                self.active_x = SCREEN_WIDTH - self.w - 80 # Move LEFT when talking
                self.off_screen_x = SCREEN_WIDTH + 20 # Start off-screen RIGHT
            
            # Initialize current position (start off-screen)
            self.x = self.off_screen_x
            self.y = self.target_y
            
            # Current Target (where we want to be right now)
            self.current_target_x = self.off_screen_x

    def create_placeholder(self, height, width):
        self.normal_image = pygame.Surface((width, height))
        self.normal_image.fill((100, 100, 150))
        self.dimmed_image = self.normal_image.copy()
        self.dimmed_image.set_alpha(128)
        self.w, self.h = width, height
        self.target_y = SCREEN_HEIGHT - height
        self.idle_x = 50 if self.position_side == 'left' else SCREEN_WIDTH - width - 50
        self.active_x = self.idle_x
        self.off_screen_x = -width if self.position_side == 'left' else SCREEN_WIDTH
        self.x = self.off_screen_x
        self.y = self.target_y
        self.current_target_x = self.off_screen_x

    def set_state(self, state):
        """
        state: 'hidden', 'idle', 'active'
        """
        if state == 'hidden':
            self.current_target_x = self.off_screen_x
        elif state == 'idle':
            self.current_target_x = self.idle_x
        elif state == 'active':
            self.current_target_x = self.active_x

    def update(self):
        # Smoothly interpolate current X to target X
        self.x = lerp(self.x, self.current_target_x, 0.15)

    def draw(self, surface, is_speaker):
        if not hasattr(self, 'normal_image'):
            return

        # If talking, use normal image. If not, use dimmed.
        img = self.normal_image if is_speaker else self.dimmed_image
        surface.blit(img, (self.x, self.y))

class DialogueManager:
    def __init__(self, dialogues):
        self.dialogues = dialogues 
        self.index = 0
        self.active = False
        self.finished = False
        
        # States: 'opening', 'playing', 'closing'
        self.state = 'opening'
        
        # Participants
        self.participants = []
        seen_names = set()
        for char_obj, _ in self.dialogues:
            if char_obj.name not in seen_names:
                self.participants.append(char_obj)
                seen_names.add(char_obj.name)

        # Fonts
        self.font = pygame.font.match_font('arial')
        self.text_font = pygame.font.Font(self.font, 24)
        self.name_font = pygame.font.Font(self.font, 28)
        
        self.z_pressed_last_frame = False
        self.cooldown = 0

        # Box Animation Variables
        self.box_height = 150
        self.box_target_y = SCREEN_HEIGHT - self.box_height - 20
        self.box_off_y = SCREEN_HEIGHT + 20 # Just off screen
        self.box_y = self.box_off_y # Start off screen

    def start(self):
        self.active = True
        self.finished = False  # <--- CRITICAL FIX: Reset finished state
        self.index = 0         # <--- CRITICAL FIX: Reset dialogue index
        self.state = 'opening'
        
        # Reset characters to off-screen
        for p in self.participants:
            p.set_state('hidden')
            p.x = p.off_screen_x # Force reset position

    def update(self):
        if not self.active or self.finished:
            return

        # 1. Update Animations (Box & Characters)
        for p in self.participants:
            p.update()

        # Update Box Position
        target_y = self.box_target_y if self.state != 'closing' else self.box_off_y
        self.box_y = lerp(self.box_y, target_y, 0.15)

        # 2. State Machine Logic
        current_speaker, text = self.dialogues[self.index]

        if self.state == 'opening':
            # Move everyone to IDLE positions to enter screen
            for p in self.participants:
                p.set_state('idle')
            
            # Check if animation is roughly done (box is close to target)
            if abs(self.box_y - self.box_target_y) < 5:
                self.state = 'playing'

        elif self.state == 'playing':
            # Update Character Targets based on who is speaking
            for p in self.participants:
                if p == current_speaker:
                    p.set_state('active')
                else:
                    p.set_state('idle')

            # Handle Input
            keys = pygame.key.get_pressed()
            z_pressed = keys[pygame.K_z] or keys[pygame.K_RETURN]
            if self.cooldown > 0: self.cooldown -= 1
            
            if z_pressed and not self.z_pressed_last_frame and self.cooldown == 0:
                if self.index < len(self.dialogues) - 1:
                    self.index += 1
                    self.cooldown = 10
                else:
                    self.state = 'closing'
            
            self.z_pressed_last_frame = z_pressed

        elif self.state == 'closing':
            # Send everyone away
            for p in self.participants:
                p.set_state('hidden')
            
            # Check if animation is roughly done (box is off screen)
            if abs(self.box_y - self.box_off_y) < 5:
                self.finished = True
                self.active = False

    def draw(self, surface):
        if not self.active or self.finished:
            return

        current_speaker, _ = self.dialogues[self.index]

        # 1. Draw Characters
        for char in self.participants:
            if char != current_speaker:
                char.draw(surface, is_speaker=False)
        current_speaker.draw(surface, is_speaker=True)

        # 2. Draw Dialogue Box
        box_rect = pygame.Rect(20, self.box_y, SCREEN_WIDTH - 40, self.box_height)
        
        pygame.draw.rect(surface, DIALOGUE_BOX_COLOR, box_rect)
        pygame.draw.rect(surface, DIALOGUE_BORDER_COLOR, box_rect, 3)

        if self.state == 'playing' or (self.state == 'opening' and abs(self.box_y - self.box_target_y) < 50):
            text = self.dialogues[self.index][1]

            # 3. Draw Name
            name_surf = self.name_font.render(current_speaker.name, True, (255, 200, 100))
            name_bg_rect = pygame.Rect(box_rect.x, box_rect.y - 35, name_surf.get_width() + 20, 35)
            pygame.draw.rect(surface, DIALOGUE_BOX_COLOR, name_bg_rect)
            pygame.draw.rect(surface, DIALOGUE_BORDER_COLOR, name_bg_rect, 2)
            surface.blit(name_surf, (box_rect.x + 10, box_rect.y - 30))

            # 4. Draw Text
            words = text.split(' ')
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                if self.text_font.size(test_line)[0] > box_rect.width - 40:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))

            y_offset = box_rect.y + 20
            for line in lines:
                line_surf = self.text_font.render(line, True, WHITE)
                surface.blit(line_surf, (box_rect.x + 20, y_offset))
                y_offset += 30
                
            # 5. Draw "Press Z" indicator
            prompt = self.text_font.render("Press Z", True, (150, 150, 150))
            surface.blit(prompt, (box_rect.right - 100, box_rect.bottom - 30))

class Stage:
    def __init__(self, player, all_sprites, enemies, enemy_bullets, bosses):
        self.player = player
        self.all_sprites = all_sprites
        self.enemies = enemies
        self.enemy_bullets = enemy_bullets
        self.bosses = bosses
        self.stage_complete = False
        self.boss_spawned = False
        self.background_color = (0, 0, 0)

    def update(self, frame_count): pass
    def spawn_enemies(self, frame_count): pass
    def spawn_boss(self): pass
    def draw(self, surface): pass

class Stage1(Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_color = DEEP_BLUE_BG 
        self.miniboss_alive = False
        self.miniboss_fight_start_time = 0
        
        # --- 3D Background Settings ---
        self.horizon_y = SCREEN_HEIGHT * 0.35 
        self.center_x = SCREEN_WIDTH / 2
        
        # Grid settings (Slower speed = 2.0)
        self.grid_speed_z = 2.0     
        self.grid_offset_z = 0.0    
        self.grid_gap_z = 80        
        self.grid_gap_x = 120       

        # --- Dialogue Setup ---
        self.marisa = DialogueCharacter("Marisa", "MarisaTemp.webp", "left", height=450, max_width=350, show_full_body=False)
        self.elysa = DialogueCharacter("Elysa", "Elastron.png", "right", height=500, max_width=380, show_full_body=True)
        
        # Dialogue Scripts
        self.start_script = [
            (self.marisa, "So, this is the training zone? It looks simpler than I expected."),
            (self.elysa, "Do not underestimate the basics, Marisa. Precision is key."),
            (self.marisa, "Yeah, yeah. Just point me to the targets!"),
            (self.elysa, "Very well. Prepare yourself. The automatons are activating."),
        ]
        self.end_script = [
            (self.marisa, "You see? This is like a cakewalk."),
            (self.elysa, "Don't get cocky. That was merely a perimeter guard."),
            (self.marisa, "A guard? It had enough firepower to level a city block!"),
            (self.elysa, "And yet, the core readings suggest far worse awaits us inside."),
            (self.marisa, "Fine, fine. Let's head back and restock first."),
        ]
        
        self.active_dialogue = None
        self.opening_dialogue_triggered = False
        self.boss_dead_dialogue_triggered = False
        self.dialogue_start_frame = 300 
        self.gameplay_frame_count = 0 # This timer pauses during dialogue

        # --- Wave Setup ---
        self.waves = [
            {"time": 60, "enemies": [{"type": "Tutorial_Square", "x": 100, "y": -50, "waypoints": [(100, 100)], "bullet_pattern": pattern_aimed_shot, "can_shoot": False}, {"type": "Tutorial_Square", "x": 300, "y": -50, "waypoints": [(300, 100)], "bullet_pattern": pattern_aimed_shot, "shoot_delay_ms": 1000}, {"type": "Tutorial_Square", "x": 500, "y": -50, "waypoints": [(500, 100)], "bullet_pattern": pattern_aimed_shot, "shoot_delay_ms": 2000}]},
            {"time": 300, "enemies": [{"type": "B", "x": 200, "y": -50, "waypoints": [(200, 150)], "bullet_pattern": pattern_emerald_shot}, {"type": "B", "x": 400, "y": -50, "waypoints": [(400, 150)], "bullet_pattern": pattern_aimed_shot}]},
            {"time": 600, "enemies": [{"type": "C", "x": 200, "y": -50, "waypoints": [(200, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 620, "enemies": [{"type": "C", "x": 240, "y": -50, "waypoints": [(240, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 640, "enemies": [{"type": "C", "x": 280, "y": -50, "waypoints": [(280, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 660, "enemies": [{"type": "C", "x": 320, "y": -50, "waypoints": [(320, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 680, "enemies": [{"type": "C", "x": 360, "y": -50, "waypoints": [(360, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 700, "enemies": [{"type": "C", "x": 400, "y": -50, "waypoints": [(400, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 720, "enemies": [{"type": "C", "x": 440, "y": -50, "waypoints": [(440, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 740, "enemies": [{"type": "C", "x": 480, "y": -50, "waypoints": [(480, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 900, "enemies": [{"type": "Miniboss", "x": 400, "y": -100, "waypoints": [(400, 100)]}]},
            {"time": 1100, "enemies": [{"type": "Tutorial_Square", "x": 100, "y": -50, "waypoints": [(100, 100)], "bullet_pattern": pattern_aimed_shot}, {"type": "B", "x": 300, "y": -50, "waypoints": [(300, 150)], "bullet_pattern": pattern_emerald_shot}, {"type": "Tutorial_Square", "x": 500, "y": -50, "waypoints": [(500, 100)], "bullet_pattern": pattern_aimed_shot}]},
            {"time": 1300, "random": True, "count": 5},
            {"time": 1600, "enemies": [
                {"type": "Tutorial_Square", "x": 100, "y": -50, "waypoints":  [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 100, "y": -100, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 100, "y": -150, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 100, "y": -200, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 100, "y": -250, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 100, "y": -300, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
            ]},
            {"time": 1660, "enemies": [
                {"type": "Tutorial_Square", "x": 700, "y": -50, "waypoints":  [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 700, "y": -100, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 700, "y": -150, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 700, "y": -200, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 700, "y": -250, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "Tutorial_Square", "x": 700, "y": -300, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
            ]}
        ]
        self.wave_index = 0
        
    def start_dialogue(self, script):
        self.active_dialogue = DialogueManager(script)
        self.active_dialogue.start()

    def update(self, frame_count):
        # --- 1. ALWAYS Update Background ---
        self.grid_offset_z = (self.grid_offset_z + self.grid_speed_z) % self.grid_gap_z

        # --- 2. DIALOGUE HANDLING (Top Priority) ---
        if self.active_dialogue:
            self.active_dialogue.update()
            if self.active_dialogue.finished:
                # If this was the post-boss dialogue, mark stage as complete
                if self.boss_dead_dialogue_triggered:
                    self.stage_complete = True
                self.active_dialogue = None
            return # Pause the rest of the stage update

        # === If we get here, no dialogue is active, so we advance the gameplay clock ===
        self.gameplay_frame_count += 1

        # --- 3. DIALOGUE TRIGGERS ---
        # Trigger Opening Dialogue (uses absolute frame_count once at the start)
        if not self.opening_dialogue_triggered and frame_count > self.dialogue_start_frame:
            self.start_dialogue(self.start_script)
            self.opening_dialogue_triggered = True
            # The 'return' in the block above will pause the game, so we don't need another one here.

        # Trigger Post-Boss Dialogue
        if self.boss_spawned and not self.bosses and not self.boss_dead_dialogue_triggered:
            for bullet in self.enemy_bullets:
                bullet.kill()
            self.start_dialogue(self.end_script)
            self.boss_dead_dialogue_triggered = True
            return # Pause game immediately after triggering

        # --- 4. Standard Stage Logic (runs if no dialogue is active) ---
        if self.opening_dialogue_triggered: # Only run game logic after opening dialogue is done
            self.spawn_enemies()
            if not self.boss_spawned and self.gameplay_frame_count > 1800:
                self.spawn_boss()
                self.boss_spawned = True

    def draw(self, surface):
        # 1. LAYER 1: 3D Background
        surface.fill(DEEP_BLUE_BG) 

        grid_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Draw Vertical Lines
        for i in range(-10, 20):
            base_x = self.center_x + (i * self.grid_gap_x)
            start_pos = (base_x, SCREEN_HEIGHT)
            end_pos = (self.center_x, self.horizon_y)
            pygame.draw.line(grid_surf, (*WIRE_BLUE, 100), start_pos, end_pos, 1)

        # Draw Horizontal Lines
        z_pos = self.grid_gap_z - self.grid_offset_z
        while z_pos < 1200: 
            if z_pos <= 10: 
                z_pos += self.grid_gap_z
                continue

            scale = 20000 
            projected_y = self.horizon_y + (scale / z_pos)
            
            if projected_y < SCREEN_HEIGHT:
                thickness = 2 if z_pos < 400 else 1
                alpha = min(255, int((projected_y - self.horizon_y) * 2))
                pygame.draw.line(grid_surf, (*WIRE_BLUE, alpha), (0, projected_y), (SCREEN_WIDTH, projected_y), thickness)
            
            z_pos += self.grid_gap_z

        surface.blit(grid_surf, (0, 0))

        # 2. LAYER 2: Game Sprites
        self.all_sprites.draw(surface)

        # 3. LAYER 3: Dialogue & UI (Draw on top)
        if self.active_dialogue:
            self.active_dialogue.draw(surface)

    def spawn_enemies(self):
        if self.wave_index < len(self.waves):
            wave = self.waves[self.wave_index]
            if self.gameplay_frame_count > wave["time"]:
                if wave.get("random"):
                    for _ in range(wave["count"]):
                        enemy_type = random.choice(["Tutorial_Square", "B", "C"])
                        x = random.randrange(SCREEN_WIDTH - 30)
                        y = -50
                        bullet_pattern = random.choice([pattern_simple_shot, pattern_burst_shot, pattern_spiral_shot, pattern_emerald_shot])
                        shoot_delay_ms = random.randint(500, 2000)
                        self.spawn_enemy(enemy_type, x, y, None, 1, bullet_pattern, self.gameplay_frame_count, False, True, shoot_delay_ms)
                else:
                    for enemy_info in wave["enemies"]:
                        can_shoot = enemy_info.get("can_shoot", True)
                        shoot_delay_ms = enemy_info.get("shoot_delay_ms", 0)
                        self.spawn_enemy(enemy_info["type"], enemy_info["x"], enemy_info["y"], enemy_info.get("waypoints"), enemy_info.get("speed", 1), enemy_info.get("bullet_pattern"), self.gameplay_frame_count, enemy_info.get("fast_entry", False), can_shoot, shoot_delay_ms)
                self.wave_index += 1

    def spawn_enemy(self, enemy_type, x, y, waypoints, speed, bullet_pattern, gameplay_frame_count, fast_entry=False, can_shoot=True, shoot_delay_ms=0):
        if enemy_type == "Tutorial_Square":
            enemy = Tutorial_Square(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
        elif enemy_type == "B":
            enemy = EnemyTypeB(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
        elif enemy_type == "C":
            enemy = EnemyTypeC(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
        elif enemy_type == "Miniboss":
            enemy = Miniboss(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
            self.miniboss_alive = True
            self.miniboss_fight_start_time = gameplay_frame_count
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def spawn_boss(self):
        for enemy in self.enemies:
            enemy.kill()
        boss = BossTypeA(self.player, self.all_sprites, self.enemy_bullets)
        self.all_sprites.add(boss)
        self.bosses.add(boss)

class Stage2(Stage): pass
class Stage3(Stage): pass
class Stage4(Stage): pass
class Stage5(Stage): pass
class Stage6(Stage): pass
class Stage7(Stage): pass