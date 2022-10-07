from PIL import Image, ImageEnhance, ImageFont, ImageDraw

name = 'Tanner'
name_size = 305

quote = 'They made me wear this'
quote_size = 80

im = Image.open('label.png')
width, height = im.size

draw = ImageDraw.Draw(im)


w = 9999
while w > 1084:
    name_size -= 5
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', name_size)
    w, h = draw.textsize(name, font=font)

x, y = (width - w) / 2, (height - h) / 2
draw.text((x, y), name, font=font, fill='black')

w = 9999
while w > 1200:
    quote_size -= 5
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', quote_size)
    w, h = draw.textsize(quote, font=font)

x, y = (width - w) / 2, height - h - 30
draw.text((x, y), quote, font=font, fill='black')



im.save('tmp.png')



print('Dimentions:', height, width)


