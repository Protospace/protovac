#!/usr/bin/env python3

from PIL import Image, ImageEnhance, ImageFont, ImageDraw
from os import path

def fit_text(text, script_dir, font_path, label_path, font_size, anchor="lt"):
    img = Image.open(label_path)
    draw = ImageDraw.Draw(img)
    print(f"img.size: {img.size}")

    font = ImageFont.truetype(font_path, size=font_size)
    space_bbox = font.getbbox(" ", anchor=anchor)
    [space_left, space_upper, space_right, space_lower] = space_bbox
    space_width = abs(space_left) + abs(space_right)
    space_height = abs(space_upper) + abs(space_lower)
    print(f"font_size: {font_size} space_bbox: {space_bbox}")

    text_cur = [0, 0]
    line_bottom = 0

    for word in text.split():
        word_bbox = font.getbbox(word, anchor=anchor)
        [word_left, word_upper, word_right, word_lower] = word_bbox
        word_width = abs(word_left) + abs(word_right)
        word_height = abs(word_upper) + abs(word_lower)

        word_rec = [
            word_left + text_cur[0],
            word_upper + text_cur[1],
            word_right + text_cur[0],
            word_lower + text_cur[1],
        ]
        [rec_left, rec_upper, rec_right, rec_lower] = word_rec
        line_bottom = max(rec_lower, line_bottom)

        if rec_right > img.size[0]:
            # new line, move down, start at left
            text_cur = [0, line_bottom]
            word_rec = [
                word_left + text_cur[0],
                word_upper + text_cur[1],
                word_right + text_cur[0],
                word_lower + text_cur[1],
            ]
            [rec_left, rec_upper, rec_right, rec_lower] = word_rec
            line_bottom = max(rec_lower, line_bottom)


        if rec_right > img.size[0]:
            # word is currently extending off the right side of the page.
            # despite doing a new line.
            return False


        # print(f"{word:>10}, word_bbox: {word_bbox}, word_rec: {word_rec}")
        draw.text(text_cur, word, font=font, fill="black", anchor=anchor)
        draw.rectangle(
            word_rec, outline="#663399"
        )  # optional. draw a border around the text.

        # move over X direction
        text_cur[0] += word_width + space_width

    img.save(path.join(script_dir, "tmp.png"))

    return line_bottom <= img.size[1]



def main():
    # I'm trying to make text as big as possible within a rectangle for generating labels
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    #text = "UDIA"
    text = 'a'*100
    text = 'hello world sample sentence test'

    script_dir = path.dirname(path.abspath(__file__))
    label_path = path.join(script_dir, "label.png")
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

    font_size_range = [1, 1000]
    font_size = sum(font_size_range) // len(font_size_range)
    while abs(font_size_range[0] - font_size_range[1]) > 1:
        image_fit = fit_text(text, script_dir, font_path, label_path, font_size)
        print(f"image_fit: {image_fit}, font_size: {font_size}, font_size_range={font_size_range}")
        if image_fit:
            font_size_range = [font_size, font_size_range[1]]
        else:
            font_size_range = [font_size_range[0], font_size]
        font_size = sum(font_size_range) // len(font_size_range)

if __name__ == "__main__":
    main()
