**README**

create venv
pip install -r requirements.txt

to make offline-mode available, download "Oracle cards" bulk from scryfall and place in cards/
https://data.scryfall.io/oracle-cards/oracle-cards-20260217100533.json
adjust the entry offline/card_json in config.yaml


on windows > run printer software to register printer on windows as printer
    > copy printer name > add that config.yaml > win_printer_name

on linux > get printer path via
    lsusb
    dmesg | tail -n 50

    look for USB printer and something like this: usblp3
    > path from this: /dev/usb/lp3
    > also note VID and PID: p.e. 0x0416 0x5011
        >> add those to config.yaml

    test print:
    printf "\x1b@\nTest Print OK\n\n\n" > /dev/usb/lp3

    if denied, set permissions:
    sudo usermod -aG lp $USER
    newgrp lp
