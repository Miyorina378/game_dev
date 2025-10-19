import json

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
UI_WIDTH = 250

class Settings:
    def __init__(self):
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        self.load()

    def load(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.music_volume = settings.get("music_volume", 1.0)
                self.sfx_volume = settings.get("sfx_volume", 1.0)
        except FileNotFoundError:
            pass

    def save(self):
        with open("settings.json", "w") as f:
            json.dump({
                "music_volume": self.music_volume,
                "sfx_volume": self.sfx_volume
            }, f)

settings = Settings()