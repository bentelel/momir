import requests
import json
from image import DrawImage
from PIL import Image
from pathlib import Path
import yaml
import offline
import printer

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

MAX_ATTEMPTS = config['general']['max_attempts']

REQUEST_TIMEOUT_IN_S = config['api_options']['request_timeout_in_s']
RANDOM_CARD_URI = config['api_options']['random_card_uri']
MAX_NUMBER_FACES = config['api_options']['max_number_faces']
CREATURE_FILTER = config['api_options']['creature_filter']
MV_FILTER = config['api_options']['manavalue_filter']
SET_EXCLUSION = config['api_options']['set_exclusion']
SETS_TO_EXCLUDE = config['api_options']['sets_to_exclude']
SPLITCARD_LAYOUTS = config['api_options']['splitcard_layouts']

DEBUG_MODE_ENABLED = config['debug']['debug_mode_enabled']
TEST_INJECTION = config['debug']['test_query_options']#'name=Hostile%20Hostel'

DEFAULT_IMG_MODE = config['image_options']['default_img_mode']
IMG_DEFAULT_FETCH_TYPE = config['image_options']['img_default_fetch_type']
IMG_DRAW_TYPE = config['image_options']['img_draw_type']
IMG_WIDTH = config['image_options']['img_width']
IMG_HEIGHT = config['image_options']['img_height']


def momirLoop() -> None:
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
        attemptCounter = 0
        while True:
            attemptCounter += 1
            if attemptCounter > MAX_ATTEMPTS:
                print(f'Could not fetch fitting card in {MAX_ATTEMPTS} attempts. Please try with another cmc.')
                break
            responseObject = makeGetRequest(f'{RANDOM_CARD_URI}?q={MV_FILTER}{inp}%20{CREATURE_FILTER}%20{excludedSets}%20{TEST_INJECTION}')
            response = responseObject.json()
            if DEBUG_MODE_ENABLED:
                print(response)
            try:
                if response['layout'] in SPLITCARD_LAYOUTS:
                    #check if fronside is a creature
                    frontSideType = response['card_faces'][0]['type_line']
                    if frontSideType != 'Creature':
                        continue
                    for i in range(MAX_NUMBER_FACES):
                        printCardInfo(response['card_faces'][i])
                        if imageMode:
                           getArt(response['card_faces'][i]['image_uris']['art_crop'])
                           printArt(IMG_DEFAULT_FETCH_TYPE, IMG_DRAW_TYPE, response['card_faces'][i]['image_uris']['art_crop']) 
                # add meld card clause
                else:
                    printCardInfo(response)
                    if imageMode:
                        getArt(response['image_uris']['art_crop'])
                        printArt(IMG_DEFAULT_FETCH_TYPE, IMG_DRAW_TYPE, response['image_uris']['art_crop']) 
            except:
                print('Could not fetch card.')
                print('Status code: '+str(response['status']))
                print('Details: '+response['details'])
            break

def makeGetRequest(URI: str) -> requests.models.Response:
    r = requests.get(URI, timeout=REQUEST_TIMEOUT_IN_S)
    if DEBUG_MODE_ENABLED:
        print(r.elapsed.total_seconds())
    #j = r.json()
    return r

def printCardInfo(j: dict) -> None:
    output = (
        f"{j['name']}\n"
        f"{j['mana_cost']}\n"
        f"{j['type_line']}\n"
        f"{j['oracle_text']}\n"
    )
    if 'Creature' in j['type_line']:
        output += f"{j['power']}/{j['toughness']}"
    print(output)    
    print('')

def getArt(URI: str) -> str:
    r = makeGetRequest(URI)
    with open('img/imgColor.png', 'wb') as f:
        f.write(r.content)
    img = Image.open('img/imgColor.png')
    img = img.convert('1') # convert to BW
    img.save('img/imgBW.png')
    return r.content

def printArt(fetchMode:str, drawMode: str, path: str) -> None:
    if fetchMode=='uri':
        img = DrawImage.from_url(path, (IMG_WIDTH,IMG_HEIGHT))
    elif fetchMode=='local':
        img = DrawImage.from_file(path, (IMG_WIDTH, IMG_HEIGHT))
    if drawMode == 'colorBlocks': 
        img.draw_image()
    elif drawMode == 'ASCII':
        print('err: not yet implemented')
    

def main() -> None:
    if DEBUG_MODE_ENABLED:
        printer.testPrinter()
    Path("img/").mkdir(parents=False, exist_ok=True)
    momirLoop()
    if DEBUG_MODE_ENABLED:
        o = offline.OfflineClient()
        o.printRandomCard()
    quit()

if __name__ == "__main__":
    main()
