import requests
import json
from image import DrawImage
from PIL import Image
from pathlib import Path
import offline
import printer
from dataclasses import dataclass
from config import load_config, Config

@dataclass
class AppState:
    debug_enabled: bool
    offline_enabled: bool
    image_mode: bool

def momirLoop(config: Config, state: AppState) -> None:
    while True:
        inp = input('please enter a manavalue: ').lower()
        if inp == 'o':
            inp = input('   q-quit\n   d-toggle debugmode\n   o-toggle offlinemode\n   i-toggle imagemode\n').lower()
            if inp == 'q':
                break
            elif inp == 'd':
                state.debug_enabled = not state.debug_enabled
            elif inp == 'o':
                state.offline_enabled = not state.offline_enabled
                if state.offline_enabled:
                    print('Enabling offline mode - this might take some seconds.')
            elif inp == 'i':
                state.image_mode = not state.image_mode
                print('Imagemode turned '+('on.' if state.image_mode else 'off.'))
                continue
        try:
            _ = int(inp)
        except:
            print("Entered value was not an integer.")
            continue
        # build str to exclude sets
        excludedSets = ''
        if len(config.api.sets_to_exclude) > 0:
            for s in config.api.sets_to_exclude:
                excludedSets += config.api.set_exclusion + s + '%20'
        attemptCounter = 0
        while True:
            attemptCounter += 1
            if attemptCounter > config.general.max_attempts:
                print(f'Could not fetch fitting card in {config.general.max_attempts} attempts. Please try with another cmc.')
                break
            if not state.offline_enabled:
                uri = f'{config.api.random_card_uri}?q={config.api.manavalue_filter}{inp}%20{config.api.creature_filter}%20{excludedSets}'
                if state.debug_enabled:
                    uri += f'%20{config.debug.test_query_options}'
                responseObject = makeGetRequest(uri,config.api.request_timeout_in_s)
                if state.debug_enabled:
                        print(responseObject.elapsed.total_seconds())
                response = responseObject.json()
                if state.debug_enabled:
                    print(response)
                try:
                # this should probably be broken into distinct try-except blocks. currently we catch all errors in the api call, printing and image drawing in the same block
                    if response['layout'] in config.api.splitcard_layouts:
                        #check if fronside is a creature
                        frontSideType = response['card_faces'][0]['type_line']
                        if 'Creature' not in frontSideType:
                            continue
                        for i in range(config.api.max_number_faces):
                            printCardInfo(response['card_faces'][i])
                            if state.image_mode:
                               getArt(response['card_faces'][i]['image_uris']['art_crop'], config.api.request_timeout_in_s)
                               printArt(config.image.img_default_fetch_type, config.image.img_draw_type, response['card_faces'][i]['image_uris']['art_crop'], config.image.img_width, config.image.img_height) 
                    # add meld card clause
                    else:
                        printCardInfo(response)
                        if state.image_mode:
                            getArt(response['image_uris']['art_crop'], config.api.request_timeout_in_s)
                            printArt(config.image.img_default_fetch_type, config.image.img_draw_type, response['image_uris']['art_crop'], config.image.img_width, config.image.img_height) 
                except:
                    print('Could not fetch card.')
                    print('Status code: '+str(response['status']))
                    print('Details: '+response['details'])

            break

def makeGetRequest(URI: str, timeout_in_s: str) -> requests.models.Response:
    r = requests.get(URI, timeout=timeout_in_s)    
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

def getArt(URI: str, timeout_in_s: str) -> str:
    r = makeGetRequest(URI, timeout_in_s)
    with open('img/imgColor.png', 'wb') as f:
        f.write(r.content)
    img = Image.open('img/imgColor.png')
    img = img.convert('1') # convert to BW
    img.save('img/imgBW.png')
    return r.content

def printArt(fetchMode:str, drawMode: str, path: str, width: str, height: str) -> None:
    if fetchMode=='uri':
        img = DrawImage.from_url(path, (width,height))
    elif fetchMode=='local':
        img = DrawImage.from_file(path, (width,height))
    if drawMode == 'colorBlocks': 
        img.draw_image()
    elif drawMode == 'ASCII':
        print('err: not yet implemented')
    

def main() -> None:
    config = load_config()
    state = AppState(
        debug_enabled=config.debug.debug_mode_enabled,
        offline_enabled=config.offline.offline_mode_enabled,
        image_mode=config.image.default_img_mode,
    )
    if state.debug_enabled:
        printer.testPrinter()
    Path("img/").mkdir(parents=False, exist_ok=True)
    momirLoop(config, state)
    if state.debug_enabled:
        o = offline.OfflineClient()
        o.printRandomCard()
    quit()

if __name__ == "__main__":
    main()
