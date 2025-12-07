import pygame
import sys

pygame.init()
WIDTH, HEIGHT = 1024, 576
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Debug Mode - Check Positions")

GLOW_COLOR = (255, 255, 100)

class SelectableItem:
    def __init__(self, x, y, image_path, name, target_width=None):
        self.name = name
        self.x = x
        self.y = y
        try:
            # 1. โหลดรูปมาตามปกติ
            raw_image = pygame.image.load(image_path).convert_alpha()
            
            # 2. เช็คขนาดรูปเดิม และย่อส่วน (ถ้ากำหนด target_width มา)
            if target_width:
                # คำนวณอัตราส่วน (Aspect Ratio) เพื่อไม่ให้ภาพเบี้ยว
                original_width = raw_image.get_width()
                original_height = raw_image.get_height()
                aspect_ratio = original_height / original_width
                
                new_width = target_width
                new_height = int(new_width * aspect_ratio)
                
                # ย่อรูป
                self.image = pygame.transform.smoothscale(raw_image, (new_width, new_height))
            else:
                self.image = raw_image

            self.rect = self.image.get_rect(topleft=(x, y))
            self.glow_surface = self.create_glow_effect()
            self.image_loaded = True
        except FileNotFoundError:
            # ถ้าหาไฟล์ไม่เจอ ให้สร้างสี่เหลี่ยมแทน เพื่อไม่ให้โปรแกรมพัง
            print(f"!! หาไฟล์ {image_path} ไม่เจอ !!")
            self.image = pygame.Surface((100, 100))
            self.image.fill((255, 0, 255)) # สีม่วง = ไฟล์หาย
            self.rect = self.image.get_rect(topleft=(x, y))
            self.glow_surface = pygame.Surface((100, 100))
            self.image_loaded = False

    def create_glow_effect(self):
        if not hasattr(self, 'image'): return pygame.Surface((1,1))
        mask = pygame.mask.from_surface(self.image)
        glow_surf = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
        mask_surf = mask.to_surface(setcolor=GLOW_COLOR, unsetcolor=(0,0,0,0))
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0: continue
                glow_surf.blit(mask_surf, (10 + i, 10 + j))
        return glow_surf

    def draw(self, surface, is_selected):
        # 1. วาดแสง (ถ้าถูกเลือก)
        if is_selected and self.image_loaded:
            surface.blit(self.glow_surface, (self.x - 10, self.y - 10), special_flags=pygame.BLEND_ADD)
        
        # 2. วาดรูปวัตถุ
        surface.blit(self.image, (self.x, self.y))

        # 3. [DEBUG] วาดกรอบสีแดงและชื่อ เพื่อเช็คตำแหน่ง
        color = (0, 255, 0) if is_selected else (255, 0, 0) # เขียวถ้าเลือก, แดงถ้าไม่เลือก
        pygame.draw.rect(surface, color, self.rect, 2)
        
        # แสดงชื่อวัตถุ
        font = pygame.font.SysFont("Arial", 20)
        text = font.render(self.name, True, (255, 255, 255))
        surface.blit(text, (self.x, self.y - 25))

def main():
    clock = pygame.time.Clock()
    
    # โหลด Background
    try:
        background = pygame.image.load("room_background.jpg")
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    except:
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((50, 50, 50))

    # สร้าง Object
    # ลองแก้ path ตรงนี้ให้ตรงกับไฟล์ในเครื่องคุณ
    pot = SelectableItem(44, 98, "pot.png", "POT", target_width=700)     
    chair = SelectableItem(580, 400, "chair.png", "CHAIR", target_width=200)
    
    items = [pot, chair]
    selected_index = 0
    adjust_speed = 1
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected_index = (selected_index - 1) % len(items)
                if event.key == pygame.K_RIGHT:
                    selected_index = (selected_index + 1) % len(items)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]: items[0].y -= adjust_speed # ขึ้น
            if keys[pygame.K_s]: items[0].y += adjust_speed # ลง
            if keys[pygame.K_a]: items[0].x -= adjust_speed # ซ้าย
            if keys[pygame.K_d]: items[0].x += adjust_speed # ขวา
        
        # กด P เพื่อดูพิกัดปัจจุบัน
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                print(f"พิกัดปัจจุบัน: x={items[0].x}, y={items[0].y}")

        screen.blit(background, (0, 0))

        for i, item in enumerate(items):
            item.draw(screen, i == selected_index)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()