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

    if main.py or printer.py run into permission denied errors run:
        sudo tee /etc/udev/rules.d/99-pos58.rules >/dev/null <<'EOF'
        SUBSYSTEM=="usb", ATTR{idVendor}=="0416", ATTR{idProduct}=="5011", MODE="0666"
        EOF

        sudo udevadm control --reload-rules
        sudo udevadm trigger

        unplug+replug printer

    if request to API is really fucking slow, 
    might be that IPv6 route is broken/bad. In this case, try telling linux to prefere IPv4:
        sudo nano /etc/gai.conf
        uncomment this like:
            precedence ::ffff:0:0/96  100

To set up as easily runable on linux:
    create momir.sh in .local/bin/
        #!/bin/bash
        PROJECT_DIR="$HOME/path/to/your/project/momir"
        "$PROJECT_DIR/env/bin/python" "$PROJECT_DIR/momir/main.py"

    and:
        chmod +x momir.sh
