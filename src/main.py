import requests
import json
from image import DrawImage
from PIL import Image
from pathlib import Path
import offline
import printer
from dataclasses import dataclass, field
from typing import List
from config import load_config, Config

@dataclass
class AppState:
    debug_enabled: bool
    offline_enabled: bool
    image_mode: bool

@dataclass
class ParsedCard:
    name: str | None = None
    mana_cost: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    power: str | None = None
    toughness: str | None = None
    art_url: str | None = None
    gatherer_url: str | None = None
    layout: str | None = None
    card_is_dualfaced: bool | None = False
    # if layout is a double or trippledfaced card we store the faces in a nested structure
    faces: List["ParsedCard"] = field(default_factory=list)

class MomirGame:
    def __init__(self, config: Config):
        self.config = config
        self.state =  AppState(
                debug_enabled=config.debug.debug_mode_enabled,
                offline_enabled=config.offline.offline_mode_enabled,
                image_mode=config.image.default_img_mode,
                p_img_mode = config.printer.print_image,
                p_text_mode = config.printer.print_text,
                p_qr_mode = config.printer.print_oracle_qr
            )
        self.currentCard = ParsedCard()
   

    def run(self) -> None:
        while True:
            inp = input('please enter a manavalue: ').lower()
            if inp == 'o':
                inp = input('   q-quit\n   d-toggle debugmode\n   o-toggle offlinemode\n   i-toggle imagemode\n').lower()
                if inp == 'q':
                    break
                elif inp == 'd':
                    self.state.debug_enabled = not self.state.debug_enabled
                    print('Debugmode turned '+('on.' if self.state.debug_enabled else 'off.'))
                    continue
                elif inp == 'o':
                    self.state.offline_enabled = not self.state.offline_enabled
                    print('Offline mode was ' +('on - this might take some seconds.' if self.state.offline_enabled else 'off.'))
                    continue
                elif inp == 'i':
                    self.state.image_mode = not self.state.image_mode
                    print('Imagemode turned '+('on.' if self.state.image_mode else 'off.'))
                    continue
            try:
                _ = int(inp)
            except:
                print("Entered value was not an integer.")
                continue
            # build str to exclude sets
            excludedSets = ''
            if len(self.config.api.sets_to_exclude) > 0:
                for s in self.config.api.sets_to_exclude:
                    excludedSets += self.config.api.set_exclusion + s + '%20'
            attemptCounter = 0
            while True:
                attemptCounter += 1
                if attemptCounter > self.config.general.max_attempts:
                    print(f"""Could not fetch fitting card in 
                            {self.config.general.max_attempts} attempts. Please try with another cmc.
                            """)
                    break
                if not self.state.offline_enabled:
                    uri =   f"""  
                            {self.config.api.random_card_uri}?q=
                            {self.config.api.manavalue_filter}{inp}%20
                            {self.config.api.creature_filter}%20{excludedSets}
                            """
                    if self.state.debug_enabled:
                        uri += f'%20{self.config.debug.test_query_options}'
                    responseObject = self.makeGetRequest(uri)
                    if self.state.debug_enabled:
                            print(responseObject.elapsed.total_seconds())
                    response = responseObject.json()

                    if self.state.debug_enabled:
                        print(response)
                    try:
                        self.parseCard(response) 
                        self.printCard()
                    except:
                        err = f"""
                            Could not fetch card.\n
                            Status code: {str(response['status'])}\n
                            Details: {response['details']}\n
                            """
                break

    def makeGetRequest(self, URI: str) -> requests.models.Response:
        r = requests.get(URI, timeout=self.config.api.request_timeout_in_s)    
        #j = r.json()
        return r

    def parseCard(self, card: dict) -> None:
        # Function should parse card information and output a common format containing 
        # all relevant information (name, type_line, oracle_text, toughness etc)
        # this is needed because normal cards, meld cards, flip cards etc have different layouts.
        self.currentCard = ParsedCard()
        if card['layout'] in self.config.api.splitcard_layouts:
            #check if fronside is a creature - this check ideally is moved somewhere else?
            self.currentCard.layout = card['layout']
            self.currentCard.card_is_dualfaced = True
            self.currentCard.gatherer_url = card['related_uris']['gatherer']
            for i in range(self.config.api.max_number_faces):
                self.currentCard.faces.append(
                    ParsedCard(
                        name=card['card_faces'][i]['name'],
                        mana_cost=card['card_faces'][i]['mana_cost'],
                        type_line=card['card_faces'][i]['type_line'],
                        oracle_text=card['card_faces'][i]['oracle_text'],
                        art_url=card['card_faces'][i]['image_uris']['art_crop'],
                        layout=card['layout'],
                        card_is_dualfaced=False,
                        faces=[]
                    )
                )
                if 'Creature' in self.currentCard.faces[i].type_line:
                    self.currentCard.faces[i].power=card['card_faces'][i]['power']
                    self.currentCard.faces[i].toughness=card['card_faces'][i]['toughness']
        # add meld card clause
        else:
            self.currentCard.name=card['name']
            self.currentCard.mana_cost=card['mana_cost']
            self.currentCard.type_line=card['type_line']
            self.currentCard.oracle_text=card['oracle_text']
            self.currentCard.power=card['power']
            self.currentCard.toughness=card['toughness'] 
            self.currentCard.art_url=card['image_uris']['art_crop']
            self.gatherer_url=card['related_uris']['gatherer']
            self.currentCard.layout=card['layout']
        if self.state.debug_enabled:
            print('')
            print(self.currentCard) 
            print('')

    def printCard(self) -> None:
        if not self.currentCard.card_is_dualfaced:
            self.printCardFace(self.currentCard) 
            if self.state.image_mode:
                self.getArt(self.currentCard.art_url)
                self.printArt(self.config.image.img_default_fetch_type, self.config.image.img_draw_type, self.currentCard.art_url)
            return
        for i in range(self.config.api.max_number_faces):
            self.printCardFace(self.currentCard.faces[i])       
            if self.state.image_mode:
                self.getArt(self.currentCard.faces[i].art_url)
                self.printArt(self.config.image.img_default_fetch_type, self.config.image.img_draw_type, self.currentCard.faces[i].art_url)

    def printCardFace(self, card: ParsedCard) -> str:
        output = (
            f"{card.name}\n"
            f"{card.mana_cost}\n"
            f"{card.type_line}\n"
            f"{card.oracle_text}\n"
        )
        if 'Creature' in card.type_line:
            output += f"{card.power}/{card.toughness}"
        print(output)    
        print('')
        #printer.printSomeShit(output)

    def getArt(self, URI: str) -> str:
        r = self.makeGetRequest(URI)
        with open('img/imgColor.png', 'wb') as f:
            f.write(r.content)
        img = Image.open('img/imgColor.png')
        img = img.convert('1') # convert to BW
        img.save('img/imgBW.png')
        return r.content

    def printArt(self, fetchMode:str, drawMode: str, path: str) -> None:
        if fetchMode=='uri':
            img = DrawImage.from_url(path, (self.config.image.img_width,self.config.image.img_height))
        elif fetchMode=='local':
            img = DrawImage.from_file(path, (self.config.image.img_width,self.config.image.img_height))
        if drawMode == 'colorBlocks': 
            img.draw_image()
        elif drawMode == 'ASCII':
            print('err: not yet implemented')
        #with open('img/imgColor.png', 'rb') as f:
        #    printer.printImage(f)

def main() -> None:
    m = MomirGame(load_config())
    if m.state.debug_enabled:
        printer.testPrinter()
    Path("img/").mkdir(parents=False, exist_ok=True)
    m.run()
    if m.state.debug_enabled:
        o = offline.OfflineClient()
        o.printRandomCard()
    quit()

if __name__ == "__main__":
    main()
