import requests
import json
from image import DrawImage
from PIL import Image
from pathlib import Path
import printer

MAX_ATTEMPTS = 3
MAX_NUMBER_FACES = 2
DEFAULT_IMG_MODE = True
SETS_TO_EXCLUDE = ('UGL','UNH', 'UST', 'UND', 'UNF')
SET_EXCLUSION = '-set:'
RANDOM_CARD_URI = 'https://api.scryfall.com/cards/random?'
MV_FILTER = 'mv='
CREATURE_FILTER = 't=creature'
TEST_INJECTION = ''#'name=Hostile%20Hostel'
DEBUG_MODE = False
REQUEST_TIMEOUT_IN_S = 30
IMG_WIDTH = 48
IMG_HEIGHT = 24
IMG_TYPE = 'colorBlocks' #either colorBlocks or ASCII


def momirLoop():
    imageMode = DEFAULT_IMG_MODE
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
            responseObject = makeGetRequest(f'https://api.scryfall.com/cards/random?q={MV_FILTER}{inp}%20{CREATURE_FILTER}%20{excludedSets}%20{TEST_INJECTION}')
            response = responseObject.json()
            if DEBUG_MODE:
                print(response)
            try:
                if response['layout'] in ('split', 'flip', 'transform', 'meld', 'modal_dfc', ''):
                    #check if fronside is a creature
                    frontSideType = response['card_faces'][0]['type_line']
                    if frontSideType != 'Creature':
                        continue
                    for i in range(MAX_NUMBER_FACES):
                        printCardInfo(response['card_faces'][i])
                        if imageMode:
                           getArt(response['card_faces'][i]['image_uris']['art_crop'])
                           printArt('uri', response['card_faces'][i]['image_uris']['art_crop']) 
                else:
                    printCardInfo(response)
                    if imageMode:
                        getArt(response['image_uris']['art_crop'])
                        printArt('uri', response['image_uris']['art_crop']) 
            except:
                print('Could not fetch card.')
                print('Status code: '+str(response['status']))
                print('Details: '+response['details'])
            break

def makeGetRequest(URI: str) -> json:
    r = requests.get(URI, timeout=REQUEST_TIMEOUT_IN_S)
    if DEBUG_MODE:
        print(r.elapsed.total_seconds())
    #j = r.json()
    return r

def printCardInfo(j: dict) -> None:
    print(j['name'])
    print(j['mana_cost'])
    print(j['type_line'])
    print(j['oracle_text'])
    if 'Creature' in j['type_line']:
        print(j['power']+'/'+j['toughness'])
    print('')

def getArt(URI: str):
    r = makeGetRequest(URI)
    with open('img/imgColor.png', 'wb') as f:
        f.write(r.content)
    img = Image.open('img/imgColor.png')
    img = img.convert('1') # convert to BW
    img.save('img/imgBW.png')
    return r.content

def printArt(mode:str, path: str) -> None:
    if mode=='uri':
        img = DrawImage.from_url(path, (IMG_WIDTH,IMG_HEIGHT))
    elif mode=='local':
        img = DrawImage.from_file(path, (IMG_WIDTH, IMG_HEIGHT))
    img.draw_image()
    

def main() -> None:
    if DEBUG_MODE:
        printer.testPrinter()
    Path("img/").mkdir(parents=False, exist_ok=True)
    momirLoop()
    quit()

if __name__ == "__main__":
    main()
