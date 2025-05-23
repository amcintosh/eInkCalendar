import logging
import os
from datetime import date
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from PIL.Image import Image as TImage
from PIL.ImageDraw import ImageDraw as TImageDraw

from holidays import get_todays_holiday

logger = logging.getLogger('app')
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
PICTURES_PATH = os.path.join(CURRENT_PATH, 'pictures')
_IMAGE = Image.new("RGB", (200, 100), (255, 255, 255))
DRAW = ImageDraw.Draw(_IMAGE)


def init_display(epd):
    logger.info("Init display")
    epd.init()


def clear_display(epd):
    logger.info("Clear display")
    epd.Clear()


def set_sleep(epd):
    logger.info("Set display to sleep-mode")
    epd.sleep()


def draw_text_centered(text: str, point: Tuple[float, float], canvas: TImageDraw, text_font: ImageFont.FreeTypeFont):
    # getsize removed in pillow 6
    # stead use bounded box
    # text_width, _ = text_font.getsize(text)
    bbox = DRAW.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    canvas.text((point[0] - text_width/2, point[1]),
                text, font=text_font, fill=0)


def get_font_height(font: ImageFont.FreeTypeFont):
    # getsize removed in pillow 6
    # stead use bounded box
    # _, text_height = font.getsize("A")
    bbox = DRAW.textbbox((0, 0), "A", font=font)
    text_height = bbox[3] - bbox[1]
    return text_height


def get_font_width(font: ImageFont.FreeTypeFont, text: str):
    bbox = DRAW.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    return text_width


def convert_image_to_screen(image: TImage) -> TImage:
    def convert_f(e):
        if (e > 0):
            return 0
        else:
            return 2
    vfunc = np.vectorize(convert_f)

    image_array = np.array(image)
    converted_image_array = vfunc(image_array)
    return Image.fromarray(converted_image_array, "RGB")


def get_footer_images(has_birthday=False) -> List[TImage]:
    def load_picture(name: str) -> TImage:
        file_path = os.path.join(PICTURES_PATH, name)
        if os.path.exists(file_path):
            image = Image.open(file_path)
            return ImageOps.invert(image.convert('RGB'))
        return None

    def bool_to_array_index(boolean: bool) -> int:
        if boolean:
            return 1
        else:
            return 0

    today = date.today()
    image_cake_names = ["Cake_icon.gif", "Cake_icon_on.gif"]

    image_list = []

    # Birthday Cake First
    image_list.append(load_picture(image_cake_names[bool_to_array_index(has_birthday)]))

    # Holidays
    holiday = get_todays_holiday()
    if holiday:
        holiday = holiday.replace("’", "").replace(" ", "_").capitalize()
        icon = load_picture(f"{holiday}_icon.png")
        if icon:
            image_list.append(icon)

    # Additional Special Days
    if today.month == 2 and today.day == 20:
        image_list.append(load_picture("Anniversary_icon.png"))
    if (today.month == 12 and today.day == 31):  # Also show on New Year's Eve
        image_list.append(load_picture("New_years_day_icon.png"))
    if today.month == 2 and today.day == 14:
        image_list.append(load_picture("Valentines_day_icon.png"))
    if today.month == 10 and today.day == 31:
        image_list.append(load_picture("Halloween_icon.png"))
    if today.month == 12 and today.day in [24, 25]:
        image_list.append(load_picture("Christmas_tree_icon.png"))
    if today.day == 13 and today.isoweekday() == 5:
        image_list.append(load_picture("Friday_13_icon.png"))

    return image_list
