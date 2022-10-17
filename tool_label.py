from PIL import Image, ImageEnhance, ImageFont, ImageDraw
import requests


def print_tool_label(wiki_num):
    im = Image.open('blank.png')
    w1, h1 = im.size

    draw = ImageDraw.Draw(im)

    params = {'id': str(wiki_num), 'size': '4'}
    res = requests.get('https://labels.protospace.ca/', stream=True, params=params, timeout=5)
    res.raise_for_status()

    label = Image.open(res.raw)
    pixel_data = label.load()

    # remove yellow background
    for y in range(label.size[1]):
        for x in range(label.size[0]):
            r = min(pixel_data[x, y][0] + 4, 255)
            pixel_data[x, y] = (r, r, r, 255)

    new_size = (1280, 640)
    label = label.resize(new_size, Image.ANTIALIAS)

    w2, h2 = label.size

    x, y = int((w1 - w2) / 2), int((h1 - h2) / 2)

    im.paste(label, (x, y))

    im.save('tmp.png')


print_tool_label(152)

