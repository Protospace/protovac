from PIL import Image, ImageEnhance, ImageFont, ImageDraw
import requests
import pytz
from datetime import datetime, timezone

TIMEZONE_CALGARY = pytz.timezone('America/Edmonton')


def print_sheet_label(name, contact):
    def get_date():
        d = datetime.now(tz=timezone.utc)
        d = d.astimezone(TIMEZONE_CALGARY)
        return d.strftime('%b %-d, %Y')

    name_size = 85
    contact_size = 65
    date_size = 65

    im = Image.open('label.png')

    draw = ImageDraw.Draw(im)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', name_size)
    draw.text((20, 300), name, font=font, fill='black')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', contact_size)
    draw.text((20, 425), contact, font=font, fill='black')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', date_size)
    date_line = 'Printed: ' + get_date()
    draw.text((20, 625), date_line, font=font, fill='black')

    im.save('tmp.png')


print_sheet_label('Christopher Reallylongname', 'mail@christopherreallylongname.com')

