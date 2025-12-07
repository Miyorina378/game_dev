import pygame
import random
from Enemy import Tutorial_Square, EnemyTypeB, EnemyTypeC, BossTypeA, Miniboss, pattern_simple_shot, pattern_burst_shot, pattern_spiral_shot, pattern_triple_shot, pattern_aimed_shot, pattern_emerald_shot
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from stages.stage1 import Stage, DialogueCharacter, DialogueManager

class Stage2(Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_color = (20, 20, 40) # Dark Midnight Blue
        self.miniboss_alive = False
        self.miniboss_fight_start_time = 0
        
        # --- Dialogue Setup ---
        self.marisa = DialogueCharacter("Marisa", "MarisaTemp.webp", "left", height=450, max_width=350, show_full_body=False)
        self.elysa = DialogueCharacter("Elysa", "Elastron.png", "right", height=500, max_width=380, show_full_body=True)
        
        dialogue_script = [
            (self.marisa, "It's getting darker. These outskirts are crawling with them."),
            (self.elysa, "Sensors indicate a high density of B-Type automatons ahead."),
            (self.marisa, "Green circles? My favorite target practice."),
            (self.elysa, "Focus, Marisa. A large energy signature is approaching."),
        ]
        
        self.dialogue_manager = DialogueManager(dialogue_script)
        self.dialogue_finished = False
        self.dialogue_start_frame = 60 # Start almost immediately
        
        # --- Wave Setup ---
        self.waves = [
            # Wave 1: Crossing simple enemies
            {"time": 100, "enemies": [
                {"type": "Tutorial_Square", "x": 0, "y": 100, "waypoints": [(SCREEN_WIDTH, 100)], "speed": 4, "bullet_pattern": pattern_simple_shot},
                {"type": "Tutorial_Square", "x": SCREEN_WIDTH, "y": 200, "waypoints": [(0, 200)], "speed": 4, "bullet_pattern": pattern_simple_shot}
            ]},
            # Wave 2: Burst enemies (Green Circles)
            {"time": 300, "enemies": [
                {"type": "B", "x": 200, "y": -50, "waypoints": [(200, 150)], "bullet_pattern": pattern_burst_shot},
                {"type": "B", "x": 600, "y": -50, "waypoints": [(600, 150)], "bullet_pattern": pattern_burst_shot}
            ]},
            # Wave 3: V-Formation of Star enemies (Spirals)
            {"time": 600, "enemies": [
                {"type": "C", "x": 400, "y": -50, "waypoints": [(400, 100)], "bullet_pattern": pattern_spiral_shot},
                {"type": "C", "x": 300, "y": -50, "waypoints": [(300, 150)], "bullet_pattern": pattern_spiral_shot},
                {"type": "C", "x": 500, "y": -50, "waypoints": [(500, 150)], "bullet_pattern": pattern_spiral_shot}
            ]},
            # Wave 4: Random chaotic burst
            {"time": 900, "random": True, "count": 8},
            
            # Mid-Boss
            {"time": 1200, "enemies": [{"type": "Miniboss", "x": 400, "y": -100, "waypoints": [(400, 150)]}]}
        ]
        self.wave_index = 0
        self.stage_timer = 0

    def update(self, frame_count):
        # Dialogue Logic
        if not self.dialogue_finished:
            if frame_count <= self.dialogue_start_frame: return 
            if not self.dialogue_manager.active: self.dialogue_manager.start()
            
            if self.dialogue_manager.active:
                self.dialogue_manager.update()
                if self.dialogue_manager.finished:
                    self.dialogue_finished = True
                    self.stage_timer = frame_count 
                return 

        # Stage Logic
        self.spawn_enemies(frame_count)
        
        # Boss Spawn (Late stage)
        if not self.boss_spawned and frame_count - self.stage_timer > 1800:
            self.spawn_boss()
            self.boss_spawned = True

        if self.boss_spawned and not self.bosses:
            self.stage_complete = True

    def draw(self, surface):
        if self.dialogue_manager.active:
            self.dialogue_manager.draw(surface)

    def spawn_enemies(self, frame_count):
        if self.wave_index < len(self.waves):
            wave = self.waves[self.wave_index]
            if frame_count - self.stage_timer > wave["time"]:
                if wave.get("random"):
                    for _ in range(wave["count"]):
                        enemy_type = random.choice(["Tutorial_Square", "B"])
                        x = random.randrange(SCREEN_WIDTH - 30)
                        y = -50
                        bullet_pattern = random.choice([pattern_simple_shot, pattern_burst_shot])
                        shoot_delay_ms = random.randint(500, 2000)
                        self.spawn_enemy(enemy_type, x, y, None, 3, bullet_pattern, frame_count, False, True, shoot_delay_ms)
                else:
                    for enemy_info in wave["enemies"]:
                        can_shoot = enemy_info.get("can_shoot", True)
                        shoot_delay_ms = enemy_info.get("shoot_delay_ms", 0)
                        self.spawn_enemy(enemy_info["type"], enemy_info["x"], enemy_info["y"], enemy_info.get("waypoints"), enemy_info.get("speed", 1), enemy_info.get("bullet_pattern"), frame_count, False, can_shoot, shoot_delay_ms)
                self.wave_index += 1

    def spawn_enemy(self, enemy_type, x, y, waypoints, speed, bullet_pattern, frame_count, fast_entry=False, can_shoot=True, shoot_delay_ms=0):
        # Reusing the exact same spawn logic as Stage1 for simplicity
        if enemy_type == "Tutorial_Square":
            enemy = Tutorial_Square(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
        elif enemy_type == "B":
            enemy = EnemyTypeB(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
        elif enemy_type == "C":
            enemy = EnemyTypeC(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
        elif enemy_type == "Miniboss":
            enemy = Miniboss(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, can_shoot=can_shoot, shoot_delay_ms=shoot_delay_ms)
            self.miniboss_alive = True
            self.miniboss_fight_start_time = frame_count
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def spawn_boss(self):
        for enemy in self.enemies:
            enemy.kill()
        boss = BossTypeA(self.player, self.all_sprites, self.enemy_bullets)
        self.all_sprites.add(boss)
        self.bosses.add(boss)