import pygame
import math
import os
from Enemy import Bullet
from config import SCREEN_HEIGHT, UI_WIDTH, font_name

# Base Item Class
class Item:
    def __init__(self, item_id, name, description=""):
        self.item_id = item_id
        self.name = name
        self.description = description

class Weapon(Item):
    def __init__(self, item_id, name, weapon_type, description=""):
        super().__init__(item_id, name, description)
        self.weapon_type = weapon_type 

    def shoot(self, player, frame_count, groups):
        pass

# --- PROJECTILES ---

class Beam(pygame.sprite.Sprite):
    def __init__(self, x, y, frame_count):
        super().__init__()
        self.width = 40
        self.height = SCREEN_HEIGHT
        self.spawn_time = frame_count
        self.lifetime = 12
        self.x = x
        self.y = y
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(x, y))
        
    def update(self, frame_count):
        age = frame_count - self.spawn_time
        if age > self.lifetime:
            self.kill()
            return
        fade_progress = 1.0 - (age / self.lifetime)
        self.image.fill((0, 0, 0, 0))
        for i in range(3):
            if i == 0:
                width = self.width
                alpha = int(100 * fade_progress)
                color = (255, 100, 100, alpha)
            elif i == 1:
                width = self.width * 0.6
                alpha = int(180 * fade_progress)
                color = (255, 50, 50, alpha)
            else:
                width = self.width * 0.3
                alpha = int(255 * fade_progress)
                color = (255, 255, 200, alpha)
            layer_surface = pygame.Surface([width, self.height], pygame.SRCALPHA)
            layer_surface.fill(color)
            offset_x = (self.width - width) // 2
            self.image.blit(layer_surface, (offset_x, 0))

class SwordSlash(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((120, 80), pygame.SRCALPHA)
        pygame.draw.arc(self.image, (200, 220, 255), (0, 0, 120, 80), 0, 3.14, 5)
        glow = pygame.Surface((120, 80), pygame.SRCALPHA)
        pygame.draw.arc(glow, (100, 200, 255, 100), (0, 0, 120, 80), 0, 3.14, 15)
        self.image.blit(glow, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.damage = 15 
        self.lifetime = 10
        self.timer = 0

    def update(self, frame_count):
        self.timer += 1
        self.rect.y -= 8 
        if self.timer > self.lifetime:
            self.kill()

class HomingMissile(Bullet):
    def __init__(self, x, y, speedx, speedy, enemies, bosses):
        super().__init__(x, y, speedx, speedy, "homing_missile")
        self.velocity = pygame.math.Vector2(speedx, speedy)
        self.speed_magnitude = 7 
        self.enemies = enemies
        self.bosses = bosses if bosses is not None else pygame.sprite.Group()
        self.target = None
        self.search_timer = 0 

    def update(self, frame_count):
        self.search_timer += 1
        if (not self.target or not self.target.alive()) and self.search_timer > 15:
            self.target = self.find_closest_target()

        if self.target and self.target.alive():
            target_vector = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.rect.center)
            if target_vector.length() > 0:
                target_vector.normalize_ip()
                target_vector *= self.speed_magnitude
                steer_force = target_vector - self.velocity
                max_turn_rate = 0.4 
                if steer_force.length() > max_turn_rate:
                    steer_force.scale_to_length(max_turn_rate)
                self.velocity += steer_force

        if self.velocity.length() > 0:
            self.velocity.scale_to_length(self.speed_magnitude)

        self.x += self.velocity.x
        self.y += self.velocity.y
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        if not pygame.display.get_surface().get_rect().inflate(150, 150).colliderect(self.rect):
            self.kill()

    def find_closest_target(self):
        closest_entity = None
        min_dist = float('inf')
        all_targets = []
        if self.enemies: all_targets.extend(self.enemies.sprites())
        if self.bosses: all_targets.extend(self.bosses.sprites())
        current_pos = pygame.math.Vector2(self.rect.center)
        for entity in all_targets:
            if entity.alive():
                dist = current_pos.distance_to(entity.rect.center)
                if dist < min_dist:
                    min_dist = dist
                    closest_entity = entity
        return closest_entity

# --- WEAPONS ---

class DefaultWeapon(Weapon):
    def __init__(self, sfx):
        super().__init__("wpn_default", "Plasma Vulcan", "active", "Standard rapid-fire energy weapon.")
        self.shooting_sound = sfx["shooting"]

    def shoot(self, player, frame_count, groups):
        if frame_count - player.last_shot > player.shoot_delay:
            player.last_shot = frame_count
            if not pygame.mixer.Channel(0).get_busy():
                pygame.mixer.Channel(0).play(self.shooting_sound)
            
            if player.focused:
                bullet = Bullet(player.rect.centerx, player.rect.top, 0, -10, "player")
                groups["all_sprites"].add(bullet)
                groups["bullets"].add(bullet)
            else:
                b1 = Bullet(player.rect.centerx, player.rect.top, 0, -7, "player")
                b2 = Bullet(player.rect.left, player.rect.centery, -2, -7, "player")
                b3 = Bullet(player.rect.right, player.rect.centery, 2, -7, "player")
                groups["all_sprites"].add(b1, b2, b3)
                groups["bullets"].add(b1, b2, b3)

class BeamCannon(Weapon):
    def __init__(self, sfx):
        super().__init__("wpn_beam", "Aether Beam", "active", "Fires a powerful piercing laser.")
        self.last_shot = 0
        self.shoot_delay = 120
        self.beam_sound = sfx["beam"]

    def shoot(self, player, frame_count, groups):
        if frame_count - self.last_shot > self.shoot_delay:
            self.last_shot = frame_count
            if not pygame.mixer.Channel(1).get_busy():
                pygame.mixer.Channel(1).play(self.beam_sound)
            beam = Beam(player.rect.centerx, player.rect.top, frame_count)
            groups["all_sprites"].add(beam)
            groups["beams"].add(beam)

class Sword(Weapon):
    def __init__(self, sfx):
        super().__init__("wpn_sword", "Clockwork Blade", "active", "Short range, high damage slash.")
        self.last_shot = 0
        self.shoot_delay = 40 
        self.sound = sfx["shooting"] 

    def shoot(self, player, frame_count, groups):
        if frame_count - self.last_shot > self.shoot_delay:
            self.last_shot = frame_count
            slash = SwordSlash(player.rect.centerx, player.rect.top)
            groups["all_sprites"].add(slash)
            groups["bullets"].add(slash) 

class HomingMissiles(Weapon):
    def __init__(self, enemies, bosses=None):
        super().__init__("wpn_homing", "Homing Missiles", "passive", "Automatically targets nearby enemies.")
        self.last_shot = 0
        self.shoot_delay = 6
        self.enemies = enemies
        self.bosses = bosses

    def set_bosses(self, bosses):
        self.bosses = bosses

    def shoot(self, player, frame_count, groups):
        if frame_count - self.last_shot > self.shoot_delay:
            self.last_shot = frame_count
            missile1 = HomingMissile(player.rect.left - 20, player.rect.centery, -2, -7, self.enemies, self.bosses)
            missile2 = HomingMissile(player.rect.right + 20, player.rect.centery, 2, -7, self.enemies, self.bosses)
            groups["all_sprites"].add(missile1, missile2)
            groups["bullets"].add(missile1, missile2)

class WeaponManager:
    def __init__(self, player, enemies, sfx):
        self.player = player
        self.sfx = sfx
        self.enemies = enemies # Store for creating new passives
        
        # INVENTORY: All weapons owned
        self.inventory = [
            DefaultWeapon(sfx), 
            BeamCannon(sfx),
            HomingMissiles(enemies)
        ]
        
        # SLOTS
        self.max_active_slots = 3
        self.max_passive_slots = 3
        
        # Default Loadout
        self.weapons = {
            "active": [self.inventory[0], self.inventory[1]], # Default Gun + Beam
            "passive": [self.inventory[2]] # Default Homing
        }
        self.active_weapon_index = 0

    def add_weapon_to_inventory(self, weapon_class_name):
        # Avoid duplicates
        for w in self.inventory:
            if w.name == "Clockwork Blade" and weapon_class_name == "Sword": return
            
        if weapon_class_name == "Sword":
            self.inventory.append(Sword(self.sfx))

    def equip_weapon(self, inv_index, slot_type, slot_index):
        """
        Equip a weapon from inventory to a specific slot.
        slot_type: "active" or "passive"
        """
        if inv_index < 0 or inv_index >= len(self.inventory): return
        
        weapon_to_equip = self.inventory[inv_index]
        
        # Check compatibility
        if weapon_to_equip.weapon_type != slot_type:
            print(f"Cannot equip {slot_type} weapon in {weapon_to_equip.weapon_type} slot!")
            return

        current_list = self.weapons[slot_type]
        
        # Check if already equipped
        if weapon_to_equip in current_list:
            # If we try to equip it to the exact same slot, do nothing
            if current_list.index(weapon_to_equip) == slot_index:
                return
            # If it's elsewhere, remove it first (move behavior)
            current_list.remove(weapon_to_equip)

        # Extend list if needed
        while len(current_list) <= slot_index:
            current_list.append(None)
            
        current_list[slot_index] = weapon_to_equip
        
        # Clean up None values
        self.weapons[slot_type] = [w for w in current_list if w is not None]

    def unequip_weapon(self, slot_type, slot_index):
        current_list = self.weapons[slot_type]
        if slot_index < len(current_list):
            # Constraint: Must have at least 1 active weapon
            if slot_type == "active" and len(current_list) <= 1:
                print("Cannot unequip: Must have at least one active weapon.")
                return
            current_list.pop(slot_index)

    def set_bosses(self, bosses):
        # Update boss reference for all passive homing missiles
        for w in self.inventory:
            if isinstance(w, HomingMissiles):
                w.set_bosses(bosses)

    def shoot_active(self, frame_count, groups):
        if not self.weapons["active"]: return
        if self.active_weapon_index >= len(self.weapons["active"]):
            self.active_weapon_index = 0
        self.weapons["active"][self.active_weapon_index].shoot(self.player, frame_count, groups)

    def shoot_passive(self, frame_count, groups):
        for weapon in self.weapons["passive"]:
            weapon.shoot(self.player, frame_count, groups)

    def switch_weapon(self):
        if not self.weapons["active"]: return
        self.active_weapon_index = (self.active_weapon_index + 1) % len(self.weapons["active"])

class WeaponUI:
    def __init__(self, weapon_manager):
        self.weapon_manager = weapon_manager
        self.center_x = UI_WIDTH // 2
        self.center_y = 300

    def draw(self, surface):
        active_weapons = self.weapon_manager.weapons["active"]
        passive_weapons = self.weapon_manager.weapons["passive"]
        all_equipped = active_weapons + passive_weapons
        
        start_x = self.center_x - (len(all_equipped) * 50) // 2
        y = self.center_y

        for i, weapon in enumerate(all_equipped):
            x = start_x + i * 50
            
            # Highlight currently selected ACTIVE weapon
            is_active_selected = (weapon in active_weapons and 
                                  active_weapons.index(weapon) == self.weapon_manager.active_weapon_index)
            
            color = (255, 255, 255) if is_active_selected else (100, 100, 100)
            radius = 25 if is_active_selected else 20
            
            pygame.draw.circle(surface, color, (int(x), int(y)), radius, 2)

            font_size = 14
            font = pygame.font.Font(font_name, font_size)
            
            # Abbreviate name
            name_text = font.render(weapon.name[:3], True, (200, 200, 200))
            text_rect = name_text.get_rect(center=(x, y))
            surface.blit(name_text, text_rect)

            # Type indicator
            type_char = "A" if weapon.weapon_type == "active" else "P"
            type_text = font.render(type_char, True, (150, 150, 150))
            surface.blit(type_text, (x - 5, y + 25))