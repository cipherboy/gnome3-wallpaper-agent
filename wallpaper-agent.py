#!/usr/bin/env python3

import os
import random
import sys
import time

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify
from gi.repository import Gio


## Configuration Options
WALLPAPER_PATH = os.path.expanduser("~/Pictures/wallpapers")
WALLPAPER_EXTS = ['.jpg', '.jpeg', '.png', '.bmp']
WALLPAPER_GIO_PATH = "org.gnome.desktop.background"
WALLPAPER_GIO_KEY = "picture-uri"
LOCKSCREEN_GIO_PATH = "org.gnome.desktop.screensaver"
LOCKSCREEN_GIO_KEY = "picture-uri"
SEND_NOTIFICATIONS = True
MIN_TIME = 1 * 60
MAX_TIME = 5 * 60


def has_updated_folder(last_read):
    m_time = os.stat(WALLPAPER_PATH).st_mtime
    return m_time > last_read


def list_wallpapers(last_read=0):
    result = []

    for candidate in os.listdir(WALLPAPER_PATH):
        full_path = os.path.abspath(os.path.join(WALLPAPER_PATH, candidate))
        m_time = os.stat(full_path).st_mtime
        _, extension = os.path.splitext(candidate)

        if extension.lower() in WALLPAPER_EXTS and m_time > last_read:
            result.append((candidate, m_time))

    results = sorted(result, key=lambda x: x[1], reverse=True)
    return list(map(lambda x: x[0], results))


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


def get_random_wallpaper(wallpapers):
    new_array = wallpapers[:]
    random.shuffle(new_array)
    return new_array[0]


def get_wallpaper_choice(wallpapers, unseen_wallpapers):
    if unseen_wallpapers:
        return unseen_wallpapers.pop()

    l_wallpapers = len(wallpapers)
    hl_wallpapers = l_wallpapers//2
    tql_wallpapers = hl_wallpapers + hl_wallpapers//2
    if l_wallpapers < 5:
        return get_random_wallpaper(wallpapers)

    num = random.randint(0, 20)
    one_half = len(wallpapers)
    if num <= 11:
        return get_random_wallpaper(wallpapers[0:hl_wallpapers])
    elif num <= 17:
        return get_random_wallpaper(wallpapers[hl_wallpapers:tql_wallpapers])
    return get_random_wallpaper(wallpapers[tql_wallpapers:])


def main():
    start_time = time.time()
    wallpapers = list_wallpapers()

    if not wallpapers:
        print("Please populate %s with at least one wallpaper!" %
              WALLPAPER_PATH, file=sys.stderr)
        return

    unseen_wallpapers = set()
    update_wallpaper = True

    if SEND_NOTIFICATIONS:
        Notify.init('Wallpapers')

    try:
        while True:
            if has_updated_folder(start_time):
                new_time = time.time()
                new_files = list_wallpapers(start_time)
                start_time = new_time
                wallpapers = new_files + wallpapers
                unseen_wallpapers.update(set(new_files))

            if update_wallpaper:
                wallpaper = get_wallpaper_choice(wallpapers, unseen_wallpapers)
                set_wallpaper(wallpaper)
                update_wallpaper = False
            else:
                wallpaper = get_random_wallpaper(wallpapers)
                set_lockscreen(wallpaper)
                update_wallpaper = True

            time.sleep(random.randint(MIN_TIME, MAX_TIME))
    except Exception as excpt:
        if SEND_NOTIFICATIONS:
            Notify.uninit()

        raise excpt


if __name__ == "__main__":
    main()
