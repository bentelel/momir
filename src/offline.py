import json
import random
import yaml

with open('config.yaml', 'r') as f:
        CONFIG = yaml.safe_load(f)

class OfflineClient:
    randomCard = {}

    def __init__(self):
        with open(f"cards/{CONFIG['offline']['card_json']}", 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.getRandomCard()

    def getRandomCard(self):
        self.randomCard = random.choice(self.data)
    
    def printRandomCard(self):
        print(self.randomCard)

    def verifyCard(self):
        pass

if __name__ == "__main__":
    o = OfflineClient()
    o.printRandomCard()
