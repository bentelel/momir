import requests
import json

MAX_NUMBER_FACES = 2

def momirLoop(imageMode: bool):
    while True:
        inp = input('please enter a manavalue: ')
        if inp == 'o':
            inp = input('option: ')
            if inp == 'q':
                break
            if inp == 'i':
                imageMode = True
                print("Imagemode turned")
                continue
        try:
            _ = int(inp)
        except:
            print("Entered value was not an integer.")
            continue
        r = requests.get(f'https://api.scryfall.com/cards/random?q=mv={inp}%20t=creature%20is=transform')
        j = r.json()
        #print(j)
        try:
            if j['layout'] in ('split', 'flip', 'transform', 'meld', 'modal_dfc', ''):
                for i in range(MAX_NUMBER_FACES):
                    printCardInfo(j['card_faces'][i])
            else:
                printCardInfo(j)
        except:
            print('Could not fetch card.')
            print('Status code: '+str(j['status']))
            print('Details: '+j['details'])
        print('')

def printCardInfo(j: dict):
    print(j['name'])
    print(j['mana_cost'])
    print(j['type_line'])
    print(j['oracle_text'])
    if 'Creature' in j['type_line']:
        print(j['power']+'/'+j['toughness'])
    print('')

def main():
    imageMode = False
    momirLoop(imageMode)
    quit()

main()
