from escpos.printer import Usb, Win32Raw
from config import load_config, Config
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

class POSPrinter:

    def __init__(self):
        #should probably pass the config info into this class and not pull it in here in order to allow more than 1 printer with different settings?
        self.config=load_config().printer 
        self.name=self.config.win_printer_name
        self.maxImgWidth=self.config.max_img_width_in_px
        self.imgPrintImpl=self.config.img_print_implementation
        self.p = self._open()

    def _open(self):
        p=self._makePrinter(self.config)
        p._raw(b"\x1b\x40")
        return p

    def _makePrinter(self, cfg: Config):
        backends = {
            'win32raw': lambda c: Win32Raw(c.win_printer_name),
            #implement more backends if wanted
        }
        key = cfg.backend.lower()
        try:
            return backends[key](cfg)
        except KeyError:
            raise ValueError(f"Unknown printer backend: {cfg.backend!r}")


    def printText(self, text: str) -> None:
        self.p._raw(b'\x1b\x40')
        self.p.set(align='left', bold=False, width=2, height=2)
        self.p.text(text)
        self._feedLines(1)
        self.p.close()

    def printQRCode(self, text: str) -> None:
        self.p.qr(text)
        self._feedLines(1)
        self.p.close()

    def printImage(self, img) -> None:
        self.p._raw(b'\x1b\x40')
        optimizedImg = self._optimizeImg(img)
        self.p.set(align='left')
        self.p.image(optimizedImg, impl=self.imgPrintImpl)
        self._feedLines(1)
        self.p.close()
    
    def finishePrinting(self) -> None:
        self._feedLines(3)

    def printTestImage(self) -> None:
        self.p._raw(b'\x1b\x40')
        img = Image.open('img/imgColor.png')
        self.printImage(img)

    def _optimizeImg(self, img):
        # Resize to printer width (max 384px for 58mm)
        #image currently is cropped now matter what I set here. Maybe need more printer profile.
        if img.width > self.maxImgWidth:
            ratio = self.maxImgWidth / float(img.width)
            new_height = int((float(img.height) * float(ratio)))
            img = img.resize((self.maxImgWidth, new_height))
        img = ImageEnhance.Brightness(img).enhance(1.3)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.convert("1")
        img = img.point(lambda x: 0 if x < 150 else 255, '1')
        return img

    # this should probably be implemented in a cleaner way so that my class extends the escpos class
    # so that dotnotation/ method access is cleaner and not scattered like it now is
    def _feedLines(self, n: int):
        # ESC d n  -> print and feed n lines
        self.p._raw(bytes([0x1B, 0x64, n]))

if __name__=="__main__":
    try:
        p = POSPrinter()
        text = 'This is some creature.\nManacost here\nTypeline here\noracletexthere\n1/1'
        p.printText(text)
        p.printTestImage()
        p.finishePrinting()
    except Exception as e:
        print("Error:", e)

