import requests, socket
import json
from PIL import Image
from pathlib import Path
import offline
from printer import POSPrinter
from dataclasses import dataclass, field
from typing import List
from config import load_config, Config

@dataclass
class AppState:
    debug_enabled: bool
    offline_enabled: bool
    image_mode: bool
    p_img_mode: bool
    p_text_mode: bool
    p_qr_mode: bool

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
        if self.state.p_img_mode or self.state.p_text_mode or self.state.p_qr_mode:
            self.printer = POSPrinter()
        self.session = requests.Session()
   

    def run(self) -> None:
        while True:
            inp = input('please enter a manavalue: ').lower()
            if inp == 'o':
                if self.handleOptions():
                    break
                continue
            try:
                _ = int(inp)
                if int(inp) < 0:
                    raise Exception('No valid mv provided.')
            except:
                print("Entered value was not a positive integer.")
                continue
            # build str to exclude sets
            attemptCounter = 0
            while True:
                try:
                    attemptCounter += 1
                    if attemptCounter > self.config.general.max_attempts:
                        print(( f"Could not fetch fitting card in " 
                                f"{self.config.general.max_attempts} attempts. Please try with another cmc."
                        ))
                        break
                    if not self.state.offline_enabled:
                        params = {
                            "q": f"{self.config.api.manavalue_filter}{inp} "
                                 f"{self.config.api.creature_filter} "
                                + " ".join(f"{self.config.api.set_exclusion}{s}" for s in self.config.api.sets_to_exclude)}
                        if self.state.debug_enabled:
                                params['q'] += f"{self.config.debug.test_query_options}"
                        response= self.fetchJson(self.config.api.random_card_uri, params)
                        if self.state.debug_enabled:
                            print(response)
                    if response['object'] == 'card':
                        break

                except:
                    err = f"""
                        Could not fetch card.\n
                        Status code: {str(response['status'])}\n
                        Details: {response['details']}\n
                        """
                    continue
            if response['object'] == 'error':
                continue
            self.parseCard(response) 
            if self.state.p_img_mode or self.state.p_text_mode or self.state.p_qr_mode:
                self.printer.feedLines(1)             
            self.printCard()
            if self.state.p_img_mode or self.state.p_text_mode or self.state.p_qr_mode:
                self.printer.finishPrinting()
    
    def handleOptions(self) -> bool:
        """
        Displays options and waits for user input.
        Sets the state attributes of the instance.
        Valid input: 
            q - quit
            d - toggle debug
            o - toggle offline
            i - toggle image mode
            c - toggle console output
        Returns: flag if run should be terminate.
        """
        terminateRun = True
        inp = input('   q-quit\n   d-toggle debugmode\n   o-toggle offlinemode\n   i-toggle imagemode\n').lower()
        if inp == 'q':
            return terminateRun
        elif inp == 'd':
            self.state.debug_enabled = not self.state.debug_enabled
            print('Debugmode turned '+('on.' if self.state.debug_enabled else 'off.'))
        elif inp == 'o':
            self.state.offline_enabled = not self.state.offline_enabled
            print('Offline mode was ' +('on - this might take some seconds.' if self.state.offline_enabled else 'off.'))
        elif inp == 'i':
            self.state.image_mode = not self.state.image_mode
            print('Imagemode turned '+('on.' if self.state.image_mode else 'off.'))
        elif inp == 'c':
            self.state.console_output = not self.state.console_output
            print('Imagemode turned '+('on.' if self.state.console_output else 'off.'))

        terminateRun = False
        return terminateRun


    def fetchJson(self, URI: str, params: dict | None = None) -> dict:
        """
        Fetches random card (json format) from Scryfall API filtered by adjustable parameters.
        Returns card in a dict.
        """
        self.session.trust_env = False
        self.session.headers.update({
            "User-Agent": "momir/0.1 (contact:bentelel@github.com)",
            "Accept": "application/json;q=0.9,*/*;q=0.8"
        })
        r = self.session.get(URI, params=params, timeout=(5, self.config.api.request_timeout_in_s))
        try:
            r.raise_for_status()
            if self.state.debug_enabled:
                print(r)
                print(r.elapsed.total_seconds())
            return r.json()
        except requests.exceptions.HTTPError as e:
            if self.state.debug_enabled:
                print(e)
            return r.json()
        finally:
            r.close()
            
    def parseCard(self, card: dict) -> None:
        """
        Parse a dictionary representing a mtg card from the Scryfall API.
        SEts the currentCard attr of the instance.
        """
        # Function should parse card information and output a common format containing 
        # all relevant information (name, type_line, oracle_text, toughness etc)
        # this is needed because normal cards, meld cards, flip cards etc have different layouts.
        self.currentCard = ParsedCard()
        if card['layout'] in self.config.api.splitcard_layouts:
            #check if fronside is a creature - this check ideally is moved somewhere else?
            self.currentCard.layout = card['layout']
            self.currentCard.card_is_dualfaced = True
            #self.currentCard.gatherer_url = card['related_uris']['gatherer']
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
            #self.gatherer_url=card['related_uris']['gatherer']
            self.currentCard.layout=card['layout']
        if self.state.debug_enabled:
            print('')
            print(self.currentCard) 
            print('')

    def printCard(self) -> None:
        """
        Prints card text and art according to instances state printing settings and card type.
        """
        if not self.currentCard.card_is_dualfaced:
            self.printCardText(self.currentCard) 
            if self.state.p_img_mode:
                self.getCardArt(self.currentCard.art_url)
                self.printCardArtwork('img/imgColor.png')
            return
        for i in range(self.config.api.max_number_faces):
            self.printCardText(self.currentCard.faces[i])       
            if self.state.p_img_mode:
                self.getCardArt(self.currentCard.faces[i].art_url)
                self.printCardArtwork('img/imgColor.png')

    def printCardText(self, card: ParsedCard) -> None:
        """
        Builds output string from currentCard attr and routes that output into the text printing functions
        appropriate for the current app state (print to printer, print to console).
        """
        output = (
            f"{card.name}\n"
            f"{card.mana_cost}\n"
            f"{card.type_line}\n"
            f"{card.oracle_text}\n"
        )
        if 'Creature' in card.type_line:
            output += f"{card.power}/{card.toughness}"
        if self.config.general.console_output:
            print(output)    
            print('')
        if self.state.p_text_mode:
            self.printer.printText(output)

    def download(self, URI: str, path: str) -> None:
        """
        Downloads whatever is behind the URI called and saves it to the specified path (please include the file extension in path).
        """
        r = self.session.get(URI, stream=True, allow_redirects=True, 
                             timeout=(5, self.config.api.request_timeout_in_s))
        try:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(256 * 1024):
                    if chunk:
                        f.write(chunk)
        finally:
            r.close()

    def getCardArt(self, URI: str) -> None:
        """
        Fetches Card Artwork from scryfall API and saves it to img/imgColor.png.
        Converts the artwork to black&white using dithering and saves it to img/imgBW.png.
        """
        self.download(URI, "img/imgColor.png")
        img = Image.open("img/imgColor.png").convert("1")
        img.save("img/imgBW.png")

    def printCardArtwork(self, path: str) -> None:
        """
        Prints currentCards artwork (through saved file in img/imgColor) on POSPrinter 
        """
        img = Image.open(path)
        self.printer.printImage(img)

def main() -> None:
    m = MomirGame(load_config())
    if m.state.debug_enabled:
        printer.testPrinter()
    Path("img/").mkdir(parents=False, exist_ok=True)
    m.run()
    if m.state.debug_enabled:
        o = offline.OfflineClient()
        o.printRandomCard()

if __name__ == "__main__":
    main()
