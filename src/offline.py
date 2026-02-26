import json
import random
import yaml
import config

CONFIG = load_config()

class OfflineClient:
    randomCard = {}
    cards = {}
    filteredCards = {}

    def __init__(self):
        with open(f"cards/{CONFIG['offline']['card_json']}", 'r', encoding='utf-8') as f:
            self.cards = json.load(f)
        self.getRandomCard()
        self.filterCards()

    def getRandomCard(self):
        self.randomCard = random.choice(self.cards)
    
    def printRandomCard(self):
        print(self.randomCard)

    def verifyCard(self, card: dict) -> bool:
        #method to verify a card is valid in the momir grab (manavalue, type_line?)
        if card['set'].upper() in CONFIG['api_options']['sets_to_exclude']:
            return False
        if 'Creature' not in card['type_line']:
            return False
        #add clause for meld cards
        if card['layout'] in CONFIG['api_options']['splitcard_layouts']: 
            # need to nest this because the non-double sided cards do not have the card_faces key
            if 'Creature' not in card['card_faces'][0]['type_line']:
                return False
        return True

    def filterCards(self):
        #method to filter the loaded json to only include momir valid cards
        self.filteredCards = [x for x in self.cards if self.verifyCard(x)]


if __name__ == "__main__":
    o = OfflineClient()
    o.printRandomCard()
    print(len(o.cards))
    print(len(o.filteredCards))
