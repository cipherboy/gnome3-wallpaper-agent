#!/usr/bin/env python3

import os
import time
import random

from gi.repository import Gio

WALLPAPER_PATH = os.path.expanduser("~/Pictures/wallpapers")
WALLPAPER_EXTS = ['.jpg', '.jpeg', '.png', '.bmp']
WALLPAPER_GIO_PATH = "org.gnome.desktop.background"
WALLPAPER_GIO_KEY = "picture-uri"
LOCKSCREEN_GIO_PATH = "org.gnome.desktop.screensaver"
LOCKSCREEN_GIO_KEY = "picture-uri"
MIN_TIME = 5 * 60
MAX_TIME = 25 * 60


def list_wallpapers():
    result = []

    for candidate in os.listdir(WALLPAPER_PATH):
        full_path = os.path.abspath(os.path.join(WALLPAPER_PATH, candidate))
        _, extension = os.path.splitext(candidate)
        if extension.lower() in WALLPAPER_EXTS:
            result.append(full_path)
        else:
            print(extension.lower())

    return result


def set_path(g_path, g_key, image_path):
    file_uri = "file://%s" % (image_path)
    gso = Gio.Settings.new(g_path)
    gso.set_string(g_key, file_uri)


def set_wallpaper(image_path):
    set_path(WALLPAPER_GIO_PATH, WALLPAPER_GIO_KEY, image_path)
    print("Set wallpaper: %s" % (image_path))


def set_lockscreen(image_path):
    set_path(LOCKSCREEN_GIO_PATH, LOCKSCREEN_GIO_KEY, image_path)
    print("Set lockscreen: %s" % (image_path))


def main():
    while True:
        try:
            wallpapers = list_wallpapers()
            lockscreen_index = 1
            if len(wallpapers) == 0:
                print("Please populate %s with at least one wallpaper!" %
                      WALLPAPER_PATH, file=sys.stderr)
                return
            random.shuffle(wallpapers)
            set_wallpaper(wallpapers[0])
            set_lockscreen(wallpapers[-1])
        except Exception as e:
            print(e)

        time.sleep(random.randint(MIN_TIME, MAX_TIME))



if __name__ == "__main__":
    main()
