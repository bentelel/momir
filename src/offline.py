import json
import random
import yaml

with open('config.yaml', 'r') as f:
        CONFIG = yaml.safe_load(f)

class OfflineClient:
    def __init__(self):
        with open(f"cards/{CONFIG['offline']['card_json']}", 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def getRandomCard(self):
        print(random.choice(self.data))

if __name__ == "__main__":
    o = OfflineClient()
    o.getRandomCard()
