import pygame
import sys
import os

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Character Dialogue with Emotions")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
BG_COLOR = (30, 30, 50)
BOX_COLOR = (240, 240, 240)

# Font
font = pygame.font.Font(None, 28)
name_font = pygame.font.Font(None, 40)

# Character positions
LEFT_CHAR_POS = (200, 250)
RIGHT_CHAR_POS = (600, 250)

class Character:
    def __init__(self, name, sprite_prefix, position):
        self.name = name
        self.position = position
        self.sprites = {}
        self.current_emotion = "neutral"
        
        # Load emotion sprites
        # Expected filenames: miyorin_happy.png, miyorin_sad.png, etc.
        emotions = ["neutral", "happy", "sad", "surprised", "angry", "worried"]
        
        for emotion in emotions:
            filename = f"{sprite_prefix}_{emotion}.webp"
            try:
                # Try to load the sprite
                img = pygame.image.load(filename)
                # Scale to reasonable size (adjust as needed)
                img = pygame.transform.scale(img, (250, 400))
                self.sprites[emotion] = img
            except:
                # If sprite doesn't exist, create a placeholder
                placeholder = pygame.Surface((250, 400))
                placeholder.fill((100, 100, 100))
                text = font.render(f"{emotion}", True, WHITE)
                text_rect = text.get_rect(center=(125, 200))
                placeholder.blit(text, text_rect)
                self.sprites[emotion] = placeholder
    
    def set_emotion(self, emotion):
        """Change character's emotion"""
        if emotion in self.sprites:
            self.current_emotion = emotion
    
    def draw(self, surface, is_speaking):
        """Draw character with current emotion"""
        sprite = self.sprites[self.current_emotion]
        
        # Apply highlighting effect when speaking
        if is_speaking:
            # Keep sprite at full brightness (no effect)
            sprite = sprite.copy()
        else:
            # Darken when not speaking
            darkened = sprite.copy()
            dark = pygame.Surface(sprite.get_size())
            dark.fill((0, 0, 0))
            dark.set_alpha(120)
            darkened.blit(dark, (0, 0))
            sprite = darkened
        
        # Draw sprite centered at position
        rect = sprite.get_rect(center=self.position)
        surface.blit(sprite, rect)
        
        # Draw character name
        name_color = WHITE if is_speaking else GRAY
        name_text = name_font.render(self.name, True, name_color)
        name_rect = name_text.get_rect(center=(self.position[0], self.position[1] + 220))
        surface.blit(name_text, name_rect)

def draw_dialogue_box(surface, text, speaker_name):
    """Draw dialogue box at the bottom of screen"""
    box_rect = pygame.Rect(50, HEIGHT - 150, WIDTH - 100, 120)
    
    # Draw box with shadow
    shadow_rect = box_rect.copy()
    shadow_rect.x += 5
    shadow_rect.y += 5
    pygame.draw.rect(surface, (20, 20, 20), shadow_rect)
    pygame.draw.rect(surface, BOX_COLOR, box_rect)
    pygame.draw.rect(surface, BLACK, box_rect, 3)
    
    # Speaker name with background
    speaker_text = name_font.render(speaker_name, True, (50, 50, 150))
    speaker_bg = pygame.Rect(60, HEIGHT - 165, speaker_text.get_width() + 20, 35)
    pygame.draw.rect(surface, (200, 220, 255), speaker_bg)
    pygame.draw.rect(surface, BLACK, speaker_bg, 2)
    surface.blit(speaker_text, (70, HEIGHT - 162))
    
    # Dialogue text with word wrap
    words = text.split()
    lines = []
    current_line = []
    max_width = WIDTH - 140
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if font.size(test_line)[0] > max_width:
            current_line.pop()
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw lines
    y_offset = HEIGHT - 120
    for line in lines[:3]:  # Max 3 lines
        line_text = font.render(line, True, BLACK)
        surface.blit(line_text, (70, y_offset))
        y_offset += 32

# Initialize characters
miyorin = Character("Miyorin", "miyorin", LEFT_CHAR_POS)
mayuri = Character("Mayuri", "mayuri", RIGHT_CHAR_POS)

# Dialogue data: (speaker, emotion, text)
# speaker: 0 = miyorin (left), 1 = mayuri (right)
dialogues = [
    (0, "happy", "Tuturu~! It's a lovely day today!"),
    (1, "neutral", "Hello there! How have you been?"),
    (0, "worried", "I've been a bit concerned about something..."),
    (1, "surprised", "Oh no! What's wrong?"),
    (0, "sad", "I lost my favorite pocket watch..."),
    (1, "worried", "That's terrible! Let me help you find it!"),
    (0, "happy", "Really? Thank you so much!"),
    (1, "happy", "Of course! That's what friends are for!"),
    (0, "surprised", "Wait, I think I remember where I left it!"),
    (1, "neutral", "Where do you think it is?"),
    (0, "happy", "At the lab! Let's go check!"),
    (1, "happy", "Okay! Let's go together!"),
]

current_dialogue = 0
clock = pygame.time.Clock()

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                # Advance to next dialogue
                current_dialogue = (current_dialogue + 1) % len(dialogues)
            elif event.key == pygame.K_ESCAPE:
                running = False
    
    # Clear screen
    screen.fill(BG_COLOR)
    
    # Get current dialogue
    speaker, emotion, text = dialogues[current_dialogue]
    
    # Update emotions
    if speaker == 0:
        miyorin.set_emotion(emotion)
        mayuri.set_emotion("neutral")  # Other character stays neutral
    else:
        mayuri.set_emotion(emotion)
        miyorin.set_emotion("neutral")
    
    # Draw characters
    miyorin.draw(screen, speaker == 0)
    mayuri.draw(screen, speaker == 1)
    
    # Draw dialogue box
    speaker_name = miyorin.name if speaker == 0 else mayuri.name
    draw_dialogue_box(screen, text, speaker_name)
    
    # Draw instructions
    instruction = font.render("Press SPACE to continue | ESC to quit", True, WHITE)
    screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, 20))
    
    # Draw dialogue counter
    counter = font.render(f"{current_dialogue + 1}/{len(dialogues)}", True, GRAY)
    screen.blit(counter, (WIDTH - 100, 20))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()