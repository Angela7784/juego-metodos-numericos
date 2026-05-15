import json

class LevelManager:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        self.niveles = self.data["niveles"]

    def get_level(self, index):
        if 0 <= index < len(self.niveles):
            return self.niveles[index]
        return None

    def total_levels(self):
        return len(self.niveles)