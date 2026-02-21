#class for printer access
from escpos.printer import Dummy, Win32Raw
from config import load_config
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

PRINTER_NAME = 'POS-58'

def testPrinter():
    p = Dummy()
    p.text("printer test 1\n")
    p.text("printer test 2\n")
    p.text("printer test 3\n")
    print(p.output)

def printSomeShit(shit: str) -> None:
    printer = Win32Raw(PRINTER_NAME)
    printer._raw(b'\x1b\x40')
    printer.set(align='left', bold=False, width=2, height=2)
    printer.text(shit)
    printer.text('  ') # placeholder so last row isnt cut? last line is still cut
    printer.close()

def printImage(self, img) -> None:
        printer = Win32Raw(PRINTER_NAME)
        printer._raw(b'\x1b\x40')
        optimizedImg = img
        printer.set(align='left')
        printer.image(optimizedImg, impl="bitImageRaster")
        printer.cut()
        printer.close()

def optimizeImg(img):
    # Resize to printer width (max 384px for 58mm)
    max_width = 384 #image currently is cropped now matter what I set here. Maybe need more printer profile.
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int((float(img.height) * float(ratio)))
        img = img.resize((max_width, new_height))
    # Convert to proper 1-bit black & white
    img = img.convert("L")
    img = img.point(lambda x: 0 if x < 128 else 255, '1')
    return img

class POSPrinter:

    def __init__(self):
        #should probably pass the config info into this class and not pull it in here in order to allow more than 1 printer with different settings?
        self.config=load_config() 
        self.name=self.config.printer.win_printer_name
        self.maxImgWidth=self.config.printer.max_img_width_in_px
        self.imgPrintImpl=self.config.printer.img_print_implementation
        self.printer = Win32Raw(self.name)

    def printText(self, text: str) -> None:
        pass

    def printQRCode(self, text: str) -> None:
        self.printer.qr(text)
        self.printer.cut()

    def printImage(self, img) -> None:
        self.printer._raw(b'\x1b\x40')
        optimizedImg = img
        self.printer.set(align='left')
        self.printer.image(optimizedImg, impl=self.imgPrintImpl)
        self.printer.cut()
        self.printer.close()

    def printTestImage(self) -> None:
        self.printer._raw(b'\x1b\x40')
        img = Image.open('img/imgColor.png')
        optimizedImg = self.optimizeImg(img)
        self.printer.image(optimizedImg, impl=self.imgPrintImpl)
        self.printer.cut()
        self.printer.close()

    def optimizeImg(self, img):
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

if __name__=="__main__":
    try:
        p = POSPrinter()
        p.printTestImage()
    except Exception as e:
        print("Error:", e)

