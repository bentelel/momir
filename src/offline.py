import json
import random

class OfflineClient:
    def __init__(self):
        with open('cards/oracle-cards-20260217100533.json', 'r') as f:
            self.data = json.load(f)

    def getRandomCard(self):
        print(random.choice(self.data))

if __name__ == "__main__":
    o = OfflineClient()
    o.getRandomCard()
