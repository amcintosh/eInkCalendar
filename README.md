# Portal eInk Calendar

A small desk-calendar.

It displays the current date, the next few events in your calendar and whether a person in your
contact list has a birthday (inc. their name).

Forked from [13Bytes](https://github.com/13Bytes/eInkCalendar) but I've been heavily modifying it:

- Updating all the dependencies as many of them did not work with the latest Raspberry Pi OSes
- Updated to pull data from multiple calendars, including Google Calendars (which I use)
- Updated to pull birthdays from Google Contacts
- Removed the Python schedule library and run updates with just cron
- I bought a slightly different eInk display which doesn't handle the red colours
- Removed the [portal](https://store.steampowered.com/app/620/Portal_2/) chamber theme as it's not my thing

## Table of Contents

1. [About The Project](#about-the-project)
2. [Components](#components)
3. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation]("#installation)
4. [Frame](#frame)
    [Questions]("#questions)
    [Contact]("#contact)
5. [Acknowledgments]("#acknowledgments)

## About The Project

Pictures of the original finished project:

<img src="https://user-images.githubusercontent.com/12069002/150647924-80f5f8fa-098a-4592-b257-7ac27326abfb.jpg" height=300>
<img src="https://user-images.githubusercontent.com/12069002/150647951-48b0ee2c-e09c-45f7-ba01-4635f47f1a91.jpg" height=300>

The pie is displayed when a person in your contacts has a birthday (along with the name below it).

The other three icons are currently displayed randomly.

### Components

This repo includes the software (100% python) and the STLs of the frame.

I used the following hardware:

- [Waveshare 800×480, 7.5inch E-Ink display (13505)](https://www.waveshare.com/product/displays/7.5inch-e-paper-hat-b.htm)
- [Raspberry Pi 3b](https://www.raspberrypi.com/products/raspberry-pi-3-model-b/)
  The Raspi is a bit overkill if you only want to update the calendar. But since it's powered on
  anyways, I use it to host many other things as well. If you only want to use it for the calendar,
  you should take a look at the Raspberry Pi Zero series

## Getting Started

### Prerequisites

The prerequisites are based on [this](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_(B)) waveshare
instruction to get your rapi ready for the display:

- Enable the SPI interface on your raspi

  ```shell
  sudo raspi-config
  # Choose Interfacing Options -> SPI -> Yes  to enable SPI interface
  ```

- Install BCM2835 libraries

  ```shell
  wget wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.75.tar.gz
  tar zxvf bcm2835-1.75.tar.gz
  cd bcm2835-1.75.tar.gz/
  sudo ./configure && sudo make && sudo make check && sudo make install
  ```

- Install wiringPi libraries

  ```shell
  sudo apt-get install wiringpi

  # For Pi 4, you need to update it：
  wget https://github.com/WiringPi/WiringPi/releases/download/3.10/wiringpi_3.10_arm64.deb
  sudo dpkg -i wiringpi_3.10_arm64.deb
  # or
  wget https://github.com/WiringPi/WiringPi/releases/download/3.10/wiringpi_3.10_armhf.deb
  sudo dpkg -i wiringpi_3.10_armhf.deb
  ```

#### Google Contacts Integration

Follow the steps [here](https://developers.google.com/people/quickstart/python) to setup authorization
for the Google Contacts API.

### Installation

1. Clone the repo

   ```sh
   git clone https://github.com/amcintosh/eInkCalendar.git
   cd eInkCalendar
   ```

2. Create config-file

   ```sh
   cp settings.py.sample settings.py
   ```

   Now edit `settings.py` and set all your settings:

   `LOCALE: "en_US"` (or e.g. `en-GB.UTF-8`) Select your desired format and language.
   It needs to be installed on your device (which 95% of time is already the case - as it's you system-language.
   You can list all installed local-packages with `locale -a`.
   If the desired one is missing, add it in this menu `sudo dpkg-reconfigure locales` (for Raspberry Pis)
   or take a look at the general [Debian Wiki](https://wiki.debian.org/Locale)).

   `CALENDAR_URLS` The addresses of your shared calendars.

   `CALDAV_CONTACT_USER = "louis"` Username for logging into your CALDAV contact-list.

   `CALDAV_CONTACT_PWD = "secret"` Password for logging into your CALDAV contact-list.

   `ROTATE_IMAGE = True` This will rotate the image 180° before printing it to the calendar. `True` is required if you use my STL, as the dipay is mounted upside-down.

3. Add the start-script to your boot-process:\
   (You might need to adapt the path `/home/pi/eInkCalendar/run_calendar.sh` acordingly)

   Make `run_calendar.sh` executable

   ```sh
   chmod +x /home/pi/eInkCalendar/run_calendar.sh
   ```

   and add it to crontab, as follows:

   ```sh
   crontab -e
   ```

   and add following lines:

   ```text
   @reboot sleep 60 && /home/pi/eInkCalendar/run_calendar.sh
   1 */6 * * * /home/pi/eInkCalendar/run_calendar.sh
   ```

## Frame

The STLs of the frame can be found in [hardware](https://github.com/13Bytes/eInkCalendar/tree/main/hardware).
It's designed for 3D-printing.
The two parts can be screwed together in three of the four corners.

The raspi is held in place by threaded heat set inserts.

<img src="https://user-images.githubusercontent.com/12069002/150642718-5a24c717-1a19-4883-b932-1f1588f124fa.png" height=400>
<img src="https://user-images.githubusercontent.com/12069002/150642799-6145283c-6e35-43b8-842b-40c608fecd77.png" height=400>

## Acknowledgments

As mentioned, I forked this from [13Bytes](https://github.com/13Bytes/eInkCalendar), who got the idea
from [reddit](https://www.reddit.com/r/RASPBERRY_PI_PROJECTS/comments/qujt3i/wip_portal_desktop_calendar/).
