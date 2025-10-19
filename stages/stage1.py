import pygame
import random
from Enemy import EnemyTypeA, EnemyTypeB, EnemyTypeC, BossTypeA, Miniboss, pattern_simple_shot, pattern_burst_shot, pattern_spiral_shot, pattern_triple_shot, pattern_aimed_shot, pattern_emerald_shot
from config import SCREEN_WIDTH, SCREEN_HEIGHT

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
        self.miniboss_alive = False
        self.miniboss_fight_start_time = 0
        self.waves = [
            {"time": 60, "enemies": [{"type": "A", "x": 100, "y": -50, "waypoints": [(100, 100)], "bullet_pattern": pattern_aimed_shot}, {"type": "A", "x": 300, "y": -50, "waypoints": [(300, 100)], "bullet_pattern": pattern_aimed_shot}, {"type": "A", "x": 500, "y": -50, "waypoints": [(500, 100)], "bullet_pattern": pattern_aimed_shot}]},
            {"time": 300, "enemies": [{"type": "B", "x": 200, "y": -50, "waypoints": [(200, 150)], "bullet_pattern": pattern_emerald_shot}, {"type": "B", "x": 400, "y": -50, "waypoints": [(400, 150)], "bullet_pattern": pattern_aimed_shot}]},
            {"time": 600, "enemies": [{"type": "C", "x": 300, "y": -50, "waypoints": [(300, 200)], "bullet_pattern": pattern_aimed_shot, "speed": 1, "fast_entry": True}]},
            {"time": 720, "enemies": [{"type": "Miniboss", "x": 400, "y": -100, "waypoints": [(400, 100)]}]},
            {"time": 900, "enemies": [{"type": "A", "x": 100, "y": -50, "waypoints": [(100, 100)], "bullet_pattern": pattern_aimed_shot}, {"type": "B", "x": 300, "y": -50, "waypoints": [(300, 150)], "bullet_pattern": pattern_emerald_shot}, {"type": "A", "x": 500, "y": -50, "waypoints": [(500, 100)], "bullet_pattern": pattern_aimed_shot}]},
            {"time": 1200, "random": True, "count": 5},
            {"time": 1500, "enemies": [
                {"type": "A", "x": 100, "y": -50, "waypoints":  [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 100, "y": -100, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 100, "y": -150, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 100, "y": -200, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 100, "y": -250, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 100, "y": -300, "waypoints": [(100, 300), (400, 300), (700, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
            ]},
            {"time": 1560, "enemies": [
                {"type": "A", "x": 700, "y": -50, "waypoints":  [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 700, "y": -100, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 700, "y": -150, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 700, "y": -200, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 700, "y": -250, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
                {"type": "A", "x": 700, "y": -300, "waypoints": [(700, 300), (400, 300), (100, 300)], "speed": 5, "bullet_pattern": pattern_aimed_shot},
            ]}
        ]
        self.wave_index = 0
        self.stage_timer = 0

    def update(self, frame_count):
        self.spawn_enemies(frame_count)
        if not self.boss_spawned and frame_count - self.stage_timer > 1800:
            self.spawn_boss()
            self.boss_spawned = True

        if self.boss_spawned and not self.bosses:
            self.stage_complete = True

    def spawn_enemies(self, frame_count):
        if self.wave_index < len(self.waves):
            wave = self.waves[self.wave_index]
            if frame_count - self.stage_timer > wave["time"]:
                if wave.get("random"):
                    for _ in range(wave["count"]):
                        enemy_type = random.choice(["A", "B", "C"])
                        x = random.randrange(SCREEN_WIDTH - 30)
                        y = -50
                        bullet_pattern = random.choice([pattern_simple_shot, pattern_burst_shot, pattern_spiral_shot, pattern_emerald_shot])
                        self.spawn_enemy(enemy_type, x, y, None, 1, bullet_pattern, frame_count)
                else:
                    for enemy_info in wave["enemies"]:
                        self.spawn_enemy(enemy_info["type"], enemy_info["x"], enemy_info["y"], enemy_info.get("waypoints"), enemy_info.get("speed", 1), enemy_info.get("bullet_pattern"), frame_count, enemy_info.get("fast_entry", False))
                self.wave_index += 1

    def spawn_enemy(self, enemy_type, x, y, waypoints, speed, bullet_pattern, frame_count, fast_entry=False):
        if enemy_type == "A":
            enemy = EnemyTypeA(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry)
        elif enemy_type == "B":
            enemy = EnemyTypeB(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry)
        elif enemy_type == "C":
            enemy = EnemyTypeC(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints, speed=speed, bullet_pattern=bullet_pattern, fast_entry=fast_entry)
        elif enemy_type == "Miniboss":
            enemy = Miniboss(x, y, self.player, self.all_sprites, self.enemy_bullets, SCREEN_HEIGHT, waypoints=waypoints)
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

class Stage2(Stage): pass
class Stage3(Stage): pass
class Stage4(Stage): pass
class Stage5(Stage): pass
class Stage6(Stage): pass
class Stage7(Stage): pass
