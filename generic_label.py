from PIL import Image, ImageEnhance, ImageFont, ImageDraw
import textwrap

text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
text = 'Extension cables'

MARGIN = 50
MAX_W, MAX_H, PAD = 1285 - (MARGIN*2), 635 - (MARGIN*2), 5

im = Image.open('label.png')
width, height = im.size
draw = ImageDraw.Draw(im)

def fit_text(text, font_size):
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)

    for cols in range(100, 1, -4):
        print('trying size', font_size, 'cols', cols)

        paragraph = textwrap.wrap(text, width=cols, break_long_words=False)

        total_h = -PAD
        total_w = 0

        for line in paragraph:
            w, h = draw.textsize(line, font=font)
            if w > total_w:
                total_w = w
            total_h += h + PAD

        if total_w <= MAX_W and total_h < MAX_H:
            return True, paragraph, total_h

    return False, [], 0

font_size_range = [1, 500]

# Thanks to Alex (UDIA) for the binary search algorithm
while abs(font_size_range[0] - font_size_range[1]) > 1:
    font_size = sum(font_size_range) // 2
    image_fit, check_para, check_h = fit_text(text, font_size)
    if image_fit:
        print('Does fit')
        font_size_range = [font_size, font_size_range[1]]
        good_size = font_size
        paragraph = check_para
        total_h = check_h
    else:
        print('Does not fit')
        font_size_range = [font_size_range[0], font_size]

font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', good_size)
offset = height - MAX_H - MARGIN
start_h = (MAX_H - total_h) // 2 + offset

current_h = start_h
for line in paragraph:
    w, h = draw.textsize(line, font=font)
    x, y = (MAX_W - w) / 2, current_h
    draw.text((x+MARGIN, y), line, font=font, fill='black')
    current_h += h + PAD


im.save('tmp.png')

print('Dimentions:', height, width)
