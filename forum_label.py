from PIL import Image, ImageEnhance, ImageFont, ImageDraw
import os
import textwrap
import qrcode
import urllib.parse

location = os.path.dirname(os.path.realpath(__file__))

def print_forum_label(thread):
    im = Image.open(location + '/label.png')
    width, height = im.size
    draw = ImageDraw.Draw(im)

    #logging.info('Printing forum thread: %s', thread['title'])

    url = 'https://forum.protospace.ca/t/{}/'.format(thread['id'])

    qr = qrcode.make(url, version=6, box_size=9)
    im.paste(qr, (840, 325))

    item_size = 150

    w = 9999
    while w > 1200:
        item_size -= 5
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', item_size)
        w, h = draw.textsize(thread['title'], font=font)

    x, y = (width - w) / 2, ((height - h) / 2) - 140
    draw.text((x, y), thread['title'], font=font, fill='black')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 100)
    draw.text((100, 410), 'Out of stock?', font=font, fill='black')
    draw.text((150, 560), 'Scan here:', font=font, fill='black')

    im.save('tmp.png')


print_forum_label(dict(id=10197, title='Pitch: A wild split-flap display appeared!'))
