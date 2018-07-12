#!/usr/bin/env python3

import os
import random
import sys
import time

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify
from gi.repository import Gio

WALLPAPER_PATH = os.path.expanduser("~/Pictures/wallpapers")
WALLPAPER_EXTS = ['.jpg', '.jpeg', '.png', '.bmp']
WALLPAPER_GIO_PATH = "org.gnome.desktop.background"
WALLPAPER_GIO_KEY = "picture-uri"
LOCKSCREEN_GIO_PATH = "org.gnome.desktop.screensaver"
LOCKSCREEN_GIO_KEY = "picture-uri"
SEND_NOTIFICATIONS = True
MIN_TIME = 1 * 60
MAX_TIME = 5 * 60


def list_wallpapers():
    result = []

    for candidate in os.listdir(WALLPAPER_PATH):
        _, extension = os.path.splitext(candidate)
        if extension.lower() in WALLPAPER_EXTS:
            result.append(candidate)

    return result


def send_notification(image_location, image_name):
    Notify.Notification.new(image_location, image_name, "image-x-generic-symbolic").show()


def set_path(g_path, g_key, image_name):
    image_path = os.path.abspath(os.path.join(WALLPAPER_PATH, image_name))

    # Read image to cache it before setting it
    open(image_path, 'rb').read()
    file_uri = "file://%s" % (image_path)
    gso = Gio.Settings.new(g_path)
    gso.set_string(g_key, file_uri)


def set_wallpaper(image_name):
    set_path(WALLPAPER_GIO_PATH, WALLPAPER_GIO_KEY, image_name)
    if SEND_NOTIFICATIONS:
        send_notification("Wallpaper", image_name)
    print("Set wallpaper: %s" % (image_name))


def set_lockscreen(image_name):
    set_path(LOCKSCREEN_GIO_PATH, LOCKSCREEN_GIO_KEY, image_name)
    if SEND_NOTIFICATIONS:
        send_notification("Lock Screen", image_name)
    print("Set lockscreen: %s" % (image_name))


def main():
    update_wallpaper = True
    if SEND_NOTIFICATIONS:
        Notify.init('Wallpapers')

    try:
        while True:
            wallpapers = list_wallpapers()
            if not wallpapers:
                print("Please populate %s with at least one wallpaper!" %
                      WALLPAPER_PATH, file=sys.stderr)
                return
            random.shuffle(wallpapers)

            if update_wallpaper:
                set_wallpaper(wallpapers[0])
                update_wallpaper = False
            else:
                set_lockscreen(wallpapers[0])
                update_wallpaper = True

            time.sleep(random.randint(MIN_TIME, MAX_TIME))
    except Exception as excpt:
        if SEND_NOTIFICATIONS:
            Notify.uninit()

        raise excpt


if __name__ == "__main__":
    main()
