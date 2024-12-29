#!/usr/bin/python3
import calendar
import locale
import logging
import os
import time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as TImage
from PIL.ImageDraw import ImageDraw as TImageDraw

from dataHelper import get_birthdays, get_events
from displayHelpers import clear_display, get_font_height, get_font_width, get_portal_images, init_display, set_sleep
from settings import DEBUG, LOCALE, ROTATE_IMAGE

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"),
                    format="%(asctime)s - %(levelname)s, %(module)s:%(lineno)s - %(message)s",
                    handlers=[logging.FileHandler(filename="info.log", mode='w'),
                    logging.StreamHandler()])
logger = logging.getLogger('app')

MAX_EVENTS = 12

CURRENT_DICT = os.path.dirname(os.path.realpath(__file__))
PICTURE_DICT = os.path.join(CURRENT_DICT, 'pictures')
FONT_DICT = os.path.join(CURRENT_DICT, 'fonts')

FONT_ROBOTO_DATE = ImageFont.truetype(os.path.join(FONT_DICT, 'Roboto-Black.ttf'), 150)
FONT_ROBOTO_H1 = ImageFont.truetype(os.path.join(FONT_DICT, 'Roboto-Black.ttf'), 40)
FONT_ROBOTO_H2 = ImageFont.truetype(os.path.join(FONT_DICT, 'Roboto-Black.ttf'), 30)
FONT_ROBOTO_P = ImageFont.truetype(os.path.join(FONT_DICT, 'Roboto-Black.ttf'), 20)
FONT_POPPINS_BOLT_P = ImageFont.truetype(os.path.join(FONT_DICT, 'Poppins-Bold.ttf'), 22)
FONT_POPPINS_P = ImageFont.truetype(os.path.join(FONT_DICT, 'Poppins-Regular.ttf'), 20)
LINE_WIDTH = 3

if DEBUG:
    class FakeEPD:
        def __init__(self):
            self.width = 800
            self.height = 480
else:
    from lib import epd7in5_V2


def main():
    logger.info(datetime.now())
    try:
        if DEBUG:
            logger.info("DEBUG-Mode activated...")
            epd = FakeEPD()
        else:
            epd = epd7in5_V2.EPD()

        image = Image.open(os.path.join(
            PICTURE_DICT, "blank-hk.bmp"))
        draw = ImageDraw.Draw(image)

        render_content(draw, image, epd.width, epd.height)
        show_content(epd, image)
        #clear_content(epd)

    except Exception as e:
        logger.exception(e)
        if not DEBUG:
            logger.info("Trying to module_exit()")
            epd7in5_V2.epdconfig.module_exit()
        raise e


def render_content(draw: TImageDraw, image: TImage,  height: int, width: int):
    locale.setlocale(locale.LC_ALL, LOCALE)

    PADDING_L = int(width/45)
    PADDING_R = int(width/30)
    PADDING_TOP = int(height/30)
    now = time.localtime()
    max_days_in_month = calendar.monthrange(now.tm_year, now.tm_mon)[1]
    day_str = time.strftime("%A")
    day_number = now.tm_mday
    month_str = time.strftime("%B")

    # Heading
    current_height = PADDING_TOP * 0.75
    draw.line((PADDING_L, current_height, width - PADDING_R, current_height), fill=1, width=LINE_WIDTH)
    draw.text((PADDING_L, current_height), month_str.upper(), font=FONT_ROBOTO_H2, fill=1)
    current_height += LINE_WIDTH
    current_height += get_font_height(FONT_ROBOTO_H2)

    # Date
    current_font_height = get_font_height(FONT_ROBOTO_DATE)
    draw.text((PADDING_L, current_height - current_font_height/10), str(day_number), font=FONT_ROBOTO_DATE, fill=1)
    current_height += current_font_height

    # Month-Overview (with day-string)
    current_height += PADDING_TOP
    day_of_month = str(day_number) + "/" + str(max_days_in_month)
    draw.text((PADDING_L, current_height), day_of_month, font=FONT_ROBOTO_P, fill=1)

    tmp_right_aligned = width - get_font_width(FONT_ROBOTO_P, day_str.upper()) - PADDING_R
    draw.text((tmp_right_aligned, current_height), day_str.upper(), font=FONT_ROBOTO_P, fill=1)

    current_height += get_font_height(FONT_ROBOTO_P) + PADDING_TOP
    draw.line((PADDING_L, current_height, width - PADDING_R, current_height), fill=1, width=LINE_WIDTH)

    # Month-Tally-Overview
    current_height += 10
    tally_height = height/50
    tally_width = LINE_WIDTH + width/120  # width + padding
    available_width = width - PADDING_L - PADDING_R
    tally_number = int(available_width / tally_width * (day_number / max_days_in_month))
    x_position = PADDING_L + LINE_WIDTH/2
    for i in range(0, tally_number):
        draw.line(
            (x_position, current_height, x_position, current_height + tally_height),
            fill=1, width=LINE_WIDTH
        )
        x_position += tally_width
    current_height += tally_height

    # Calendar
    current_height += height/50
    event_list = get_events(MAX_EVENTS)

    last_event_day = datetime.now().date()
    for event in event_list:
        # Draw new day
        if last_event_day != event.start.date():
            current_height += height/80
            last_event_day = event.start.date()
            day_string = last_event_day.strftime("%a %d")
            draw.text((PADDING_L, current_height), day_string, font=FONT_ROBOTO_P, fill=1)
            current_height += get_font_height(FONT_ROBOTO_P) * 1.5

        # Draw event
        if event.all_day:
            draw.text((PADDING_L, current_height), " - : -", font=FONT_POPPINS_P, fill=1)
        else:
            draw.text((PADDING_L, current_height), event.start.strftime("%H:%M"), font=FONT_POPPINS_P, fill=1)

        summmary_padding = 60
        draw.text((PADDING_L + summmary_padding, current_height), event.summary, font=FONT_POPPINS_P, fill=1)
        current_height += get_font_height(FONT_POPPINS_P) * 1.5

    # Portal-Icons
    current_height = int(height * 0.82)
    draw.line((PADDING_L, current_height, width - PADDING_R, current_height), fill=1, width=LINE_WIDTH)
    current_height += 10

    y = PADDING_L
    image_padding = PADDING_L
    max_image_height = 0

    bithday_persons = get_birthdays()
    draw_cake = len(bithday_persons) > 0
    for botton_image in get_portal_images(draw_cake):
        image.paste(botton_image, (image_padding, current_height))

        image_width, image_height = botton_image.size
        y += image_width + PADDING_TOP
        max_image_height = image_height if (
            image_height > max_image_height) else max_image_height
    current_height += max_image_height + PADDING_TOP

    # Draw name of birthday-person
    if draw_cake:
        bithday_persons_string = ", ".join(bithday_persons)
        draw.text((PADDING_L, current_height), f"Birthdays: {bithday_persons_string}", font=FONT_ROBOTO_P, fill=1)


def show_content(epd, image: TImage):
    logger.info("Exporting final image")
    image.save("EXPORT.bmp")
    if ROTATE_IMAGE:
        image = image.rotate(180)
    if not DEBUG:
        init_display(epd)
        logger.info("Writing on display")
        epd.display(epd.getbuffer(image))
        set_sleep(epd)


def clear_content(epd):
    if DEBUG:
        logger.warning("Clear has no effect while debugging")
    else:
        init_display(epd)
        clear_display(epd)
        set_sleep(epd)


if __name__ == '__main__':
    main()
