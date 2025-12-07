import pygame
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT, UI_WIDTH, font_name

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
DARK_OVERLAY = (0, 0, 0, 150)

class InterludeScreen:
    def __init__(self, player, stage_number, sfx):
        self.player = player
        self.stage_number = stage_number
        self.sfx = sfx # Store SFX dictionary
        self.state = "CUTSCENE" # CUTSCENE, ROOM, LOADOUT
        self.finished = False
        
        # Font setup
        self.font = pygame.font.Font(font_name, 24)
        self.title_font = pygame.font.Font(font_name, 48)
        
        # --- IMAGES ---
        self.bg_image = self.load_image("media/images/room_background.jpg", (SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT))
        
        # Characters (Images from media/Sprite/Character/)
        # Yukari = Loadout (Left side), Oliver = Next Mission (Right side)
        self.yukari_img = self.load_image("media/Sprite/Character/YukariTemp.webp", (300, 450))
        self.oliver_img = self.load_image("media/Sprite/Character/OliverTemp.png", (300, 450))
        
        # --- ROOM DATA ---
        self.selected_character = 0 # 0 = Yukari (Loadout), 1 = Oliver (Mission)
        self.room_options = [
            {"name": "Yukari", "action": "LOADOUT", "pos": (150, SCREEN_HEIGHT - 450)},
            {"name": "Oliver", "action": "NEXT_STAGE", "pos": (SCREEN_WIDTH + UI_WIDTH - 450, SCREEN_HEIGHT - 450)}
        ]
        
        # --- CUTSCENE DATA ---
        self.cutscene_text = [
            f"STAGE {stage_number} COMPLETE",
            "Returning to base...",
        ]
        self.cutscene_timer = 0
        self.cutscene_index = 0
        
        # --- LOADOUT UI DATA ---
        self.loadout_state = "SELECT_SLOT" # SELECT_SLOT or SELECT_INVENTORY
        self.selected_slot_type = "active" # "active" or "passive"
        self.selected_slot_index = 0
        self.selected_inv_index = 0
        
        # Unlock Sword after stage 1
        if stage_number >= 1:
            self.player.weapon_manager.add_weapon_to_inventory("Sword")

    def load_image(self, path, size=None):
        try:
            # Handle path normalization
            clean_path = path.replace("/", os.sep).replace("\\", os.sep)
            if os.path.exists(clean_path):
                img = pygame.image.load(clean_path).convert_alpha()
                if size:
                    img = pygame.transform.scale(img, size)
                return img
        except Exception as e:
            print(f"Error loading {path}: {e}")
        # Fallback surface
        surf = pygame.Surface(size if size else (100, 100))
        surf.fill(GRAY)
        return surf

    def update(self):
        keys = pygame.key.get_pressed()
        
        if self.state == "CUTSCENE":
            self.cutscene_timer += 1
            if self.cutscene_timer > 90:
                self.cutscene_timer = 0
                self.cutscene_index += 1
                if self.cutscene_index >= len(self.cutscene_text):
                    self.state = "ROOM"
                    
        elif self.state == "ROOM":
            return self.handle_room_input()
            
        elif self.state == "LOADOUT":
            return self.handle_loadout_input()

        return None 

    def handle_room_input(self):
        keys = pygame.key.get_pressed()
        
        # Left/Right to choose character
        if keys[pygame.K_LEFT]:
            if self.selected_character != 0:
                self.selected_character = 0
                self.sfx["select"].play()
                pygame.time.wait(150)
                
        if keys[pygame.K_RIGHT]:
            if self.selected_character != 1:
                self.selected_character = 1
                self.sfx["select"].play()
                pygame.time.wait(150)
            
        # Select
        if keys[pygame.K_z] or keys[pygame.K_RETURN]:
            self.sfx["select"].play()
            action = self.room_options[self.selected_character]["action"]
            if action == "LOADOUT":
                self.state = "LOADOUT"
            elif action == "NEXT_STAGE":
                self.finished = True
                return "NEXT_STAGE"
            pygame.time.wait(200) # Debounce
            
        return None

    def handle_loadout_input(self):
        keys = pygame.key.get_pressed()
        wm = self.player.weapon_manager
        
        if self.loadout_state == "SELECT_SLOT":
            # Navigation between Active and Passive slots
            if keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                self.selected_slot_type = "passive" if self.selected_slot_type == "active" else "active"
                self.selected_slot_index = 0 # Reset index when changing rows
                self.sfx["select"].play()
                pygame.time.wait(150)
            
            if keys[pygame.K_LEFT]:
                self.selected_slot_index = max(0, self.selected_slot_index - 1)
                self.sfx["select"].play()
                pygame.time.wait(150)
            if keys[pygame.K_RIGHT]:
                max_slots = wm.max_active_slots if self.selected_slot_type == "active" else wm.max_passive_slots
                self.selected_slot_index = min(max_slots - 1, self.selected_slot_index + 1)
                self.sfx["select"].play()
                pygame.time.wait(150)
                
            # Enter Inventory Selection
            if keys[pygame.K_z]:
                self.loadout_state = "SELECT_INVENTORY"
                self.selected_inv_index = 0 # <--- FIX: Reset index to avoid crash
                self.sfx["select"].play()
                pygame.time.wait(200)
            
            # Unequip (Remove)
            if keys[pygame.K_x]:
                wm.unequip_weapon(self.selected_slot_type, self.selected_slot_index)
                self.sfx["select"].play() # Using select sound for unequip too
                pygame.time.wait(200)
                
            # Exit Loadout
            if keys[pygame.K_ESCAPE]:
                self.state = "ROOM"
                self.sfx["select"].play()
                pygame.time.wait(200)

        elif self.loadout_state == "SELECT_INVENTORY":
            compatible_weapons = [w for w in wm.inventory if w.weapon_type == self.selected_slot_type]
            
            # Handle empty inventory case
            if not compatible_weapons:
                if keys[pygame.K_x]:
                    self.loadout_state = "SELECT_SLOT"
                    self.sfx["select"].play()
                    pygame.time.wait(200)
                return

            # SAFEGUARD: Clamp index to avoid out of range
            if self.selected_inv_index >= len(compatible_weapons):
                self.selected_inv_index = len(compatible_weapons) - 1
            if self.selected_inv_index < 0:
                self.selected_inv_index = 0

            if keys[pygame.K_UP]:
                self.selected_inv_index = max(0, self.selected_inv_index - 1)
                self.sfx["select"].play()
                pygame.time.wait(150)
            if keys[pygame.K_DOWN]:
                self.selected_inv_index = min(len(compatible_weapons) - 1, self.selected_inv_index + 1)
                self.sfx["select"].play()
                pygame.time.wait(150)
                
            if keys[pygame.K_z]:
                if compatible_weapons:
                    weapon = compatible_weapons[self.selected_inv_index]
                    real_index = wm.inventory.index(weapon)
                    wm.equip_weapon(real_index, self.selected_slot_type, self.selected_slot_index)
                    self.sfx["select"].play()
                self.loadout_state = "SELECT_SLOT"
                pygame.time.wait(200)
                
            if keys[pygame.K_x]:
                self.loadout_state = "SELECT_SLOT"
                self.sfx["select"].play()
                pygame.time.wait(200)

    def draw(self, surface):
        if self.state == "CUTSCENE":
            surface.fill(BLACK)
            if self.cutscene_index < len(self.cutscene_text):
                text = self.title_font.render(self.cutscene_text[self.cutscene_index], True, WHITE)
                rect = text.get_rect(center=(surface.get_width()//2, surface.get_height()//2))
                surface.blit(text, rect)
                
        elif self.state == "ROOM":
            # Draw Background
            if self.bg_image:
                surface.blit(self.bg_image, (0, 0))
            else:
                surface.fill((50, 30, 30)) # Fallback color

            # Draw Characters
            y_pos = self.room_options[0]["pos"]
            surface.blit(self.yukari_img, y_pos)
            
            o_pos = self.room_options[1]["pos"]
            surface.blit(self.oliver_img, o_pos)
            
            # Draw Highlight / Selection
            sel = self.room_options[self.selected_character]
            
            tag_rect = pygame.Rect(sel["pos"][0], sel["pos"][1] - 50, 300, 40)
            pygame.draw.rect(surface, (0, 0, 0, 180), tag_rect) 
            pygame.draw.rect(surface, GOLD, tag_rect, 3) 
            
            text = self.font.render(sel["name"], True, GOLD)
            text_rect = text.get_rect(center=tag_rect.center)
            surface.blit(text, text_rect)
            
            instr = self.font.render("Select Character [Z]", True, WHITE)
            surface.blit(instr, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 50))

        elif self.state == "LOADOUT":
            surface.fill((20, 20, 30))
            
            title = self.title_font.render("WEAPON LOADOUT", True, GOLD)
            surface.blit(title, (50, 30))
            
            wm = self.player.weapon_manager
            
            # --- ACTIVE SLOTS ROW ---
            lbl = self.font.render("ACTIVE WEAPONS (Max 3)", True, WHITE)
            surface.blit(lbl, (50, 100))
            
            for i in range(wm.max_active_slots):
                x = 50 + i * 220
                y = 140
                w, h = 200, 60
                
                color = GRAY
                if self.selected_slot_type == "active" and self.selected_slot_index == i:
                    color = GOLD 
                
                pygame.draw.rect(surface, color, (x, y, w, h), 2)
                
                if i < len(wm.weapons["active"]):
                    name = wm.weapons["active"][i].name
                    txt = self.font.render(name, True, WHITE)
                    surface.blit(txt, (x + 10, y + 15))
                else:
                    txt = self.font.render("[Empty]", True, GRAY)
                    surface.blit(txt, (x + 10, y + 15))

            # --- PASSIVE SLOTS ROW ---
            lbl = self.font.render("PASSIVE WEAPONS", True, WHITE)
            surface.blit(lbl, (50, 250))
            
            for i in range(wm.max_passive_slots):
                x = 50 + i * 220
                y = 290
                w, h = 200, 60
                
                color = GRAY
                if self.selected_slot_type == "passive" and self.selected_slot_index == i:
                    color = GOLD
                
                pygame.draw.rect(surface, color, (x, y, w, h), 2)
                
                if i < len(wm.weapons["passive"]):
                    name = wm.weapons["passive"][i].name
                    txt = self.font.render(name, True, WHITE)
                    surface.blit(txt, (x + 10, y + 15))
                else:
                    txt = self.font.render("[Empty]", True, GRAY)
                    surface.blit(txt, (x + 10, y + 15))

            # --- INVENTORY LIST ---
            if self.loadout_state == "SELECT_INVENTORY":
                overlay = pygame.Surface((SCREEN_WIDTH + UI_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                surface.blit(overlay, (0, 0))
                
                inv_x = 300
                inv_y = 100
                pygame.draw.rect(surface, (30, 30, 40), (inv_x, inv_y, 500, 500))
                pygame.draw.rect(surface, WHITE, (inv_x, inv_y, 500, 500), 2)
                
                title = self.font.render(f"Select {self.selected_slot_type.capitalize()}", True, GOLD)
                surface.blit(title, (inv_x + 20, inv_y + 20))
                
                compatible = [w for w in wm.inventory if w.weapon_type == self.selected_slot_type]
                
                if not compatible:
                    txt = self.font.render("No compatible items.", True, GRAY)
                    surface.blit(txt, (inv_x + 30, inv_y + 70))
                else:
                    for i, item in enumerate(compatible):
                        color = GOLD if i == self.selected_inv_index else WHITE
                        txt = self.font.render(f"> {item.name}", True, color)
                        surface.blit(txt, (inv_x + 30, inv_y + 70 + i * 40))
                        
                        if i == self.selected_inv_index:
                            desc = self.font.render(item.description, True, GRAY)
                            surface.blit(desc, (inv_x + 30, inv_y + 450))

            instr = self.font.render("[ARROWS] Navigate  [Z] Select/Equip  [X] Unequip/Back", True, GRAY)
            surface.blit(instr, (50, SCREEN_HEIGHT - 50))