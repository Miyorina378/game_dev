from .stage1 import Stage
import pygame
import random
from Enemy import Tutorial_Square, EnemyTypeB, EnemyTypeC, BossTypeA, Miniboss, pattern_simple_shot, pattern_burst_shot, pattern_spiral_shot, pattern_triple_shot, pattern_aimed_shot, pattern_emerald_shot
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class Stage2(Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Stage 2 will have no enemies initially
        self.waves = []
        self.wave_index = 0
        self.stage_timer = 0
        self.waves = [
            {"time": 60, "enemies": [{"type": "Tutorial_Square", "x": 100, "y": -50, "waypoints": [(100, 100)], "bullet_pattern": pattern_aimed_shot}]}
        ]

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