from PIL import Image, ImageEnhance, ImageFont, ImageDraw
import os
import textwrap
import qrcode
import urllib.parse

location = os.path.dirname(os.path.realpath(__file__))

def print_consumable_label(item):
    im = Image.open(location + '/label.png')
    width, height = im.size
    draw = ImageDraw.Draw(im)

    #logging.info('Printing consumable label item: %s', item)

    encodeded = urllib.parse.quote(item)
    url = 'https://my.protospace.ca/out-of-stock?item=' + encodeded

    qr = qrcode.make(url, version=6, box_size=9)
    im.paste(qr, (840, 325))

    item_size = 150

    w = 9999
    while w > 1200:
        item_size -= 5
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', item_size)
        w, h = draw.textsize(item, font=font)

    x, y = (width - w) / 2, ((height - h) / 2) - 140
    draw.text((x, y), item, font=font, fill='black')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 100)
    draw.text((100, 410), 'Out of stock?', font=font, fill='black')
    draw.text((150, 560), 'Scan here:', font=font, fill='black')

    im.save('tmp.png')


print_consumable_label('Brown paper towel')
