import requests
import json
from image import DrawImage
from PIL import Image
from pathlib import Path

MAX_ATTEMPTS = 3
MAX_NUMBER_FACES = 2
DEFAULT_IMG_MODE = True
SETS_TO_EXCLUDE = ('UGL','UNH', 'UST', 'UND', 'UNF')
SET_EXCLUSION = '-set:'
RANDOM_CARD_URI = 'https://api.scryfall.com/cards/random?'
MV_FILTER = 'mv='
CREATURE_FILTER = 't=creature'
TEST_INJECTION = ''#'name=Hostile%20Hostel'

def momirLoop(imageMode: bool):
    while True:
        inp = input('please enter a manavalue: ')
        if inp == 'o':
            inp = input('option: ')
            if inp == 'q':
                break
            if inp == 'i':
                imageMode = not imageMode
                print('Imagemode turned '+('on.' if imageMode else 'off.'))
                continue
        try:
            _ = int(inp)
        except:
            print("Entered value was not an integer.")
            continue
        # build str to exclude sets
        excludedSets = ''
        if len(SETS_TO_EXCLUDE) > 0:
            for s in SETS_TO_EXCLUDE:
                excludedSets += SET_EXCLUSION + s + '%20'

## need to filter the request (or probably the response) to not give us cards of types like 'Land // Artifact Creature — Horror Construct' > front face is a land not a creature!
## example: Hostile Hostel
## Not sure if we can filter scryfall for this?
        attemptCounter = 0
        while True:
            attemptCounter += 1
            if attemptCounter > MAX_ATTEMPTS:
                print(f'Could not fetch fitting card in {MAX_ATTEMPTS} attempts. Please try with another cmc.')
                break
            r = requests.get(f'https://api.scryfall.com/cards/random?q={MV_FILTER}{inp}%20{CREATURE_FILTER}%20{excludedSets}%20{TEST_INJECTION}')
            j = r.json()
            print(j)
            try:
                if j['layout'] in ('split', 'flip', 'transform', 'meld', 'modal_dfc', ''):
                    #check if fronside is a creature
                    frontSideType = j['card_faces'][0]['type_line']
                    if frontSideType != 'Creature':
                        continue
                    for i in range(MAX_NUMBER_FACES):
                        printCardInfo(j['card_faces'][i])
                        if imageMode:
                            artwork = getArt(j['card_faces'][i])
                else:
                    printCardInfo(j)
                    if imageMode:
                        artwork = getArt(j)
            except:
                print('Could not fetch card.')
                print('Status code: '+str(j['status']))
                print('Details: '+j['details'])
            break

def printCardInfo(j: dict):
    print(j['name'])
    print(j['mana_cost'])
    print(j['type_line'])
    print(j['oracle_text'])
    if 'Creature' in j['type_line']:
        print(j['power']+'/'+j['toughness'])
    print('')

def getArt(j: dict):
    imgURI = j['image_uris']['art_crop']
    r = requests.get(imgURI)
    with open('img/imgColor.png', 'wb') as f:
        f.write(r.content)
    img = Image.open('img/imgColor.png')
    img = img.convert('1') # convert to BW
    img.save('img/imgBW.png')
    #img.show()
    img = DrawImage.from_url(imgURI, (48,24))
    img.draw_image()
    return r.content

def main():
    Path("img/").mkdir(parents=False, exist_ok=True)
    imageMode = DEFAULT_IMG_MODE
    momirLoop(imageMode)
    quit()

main()
