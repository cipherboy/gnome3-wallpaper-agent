#!/usr/bin/env python3

"""
GNOME3 Wallpaper Agent

Monitors for changes in a wallpaper directory and randomly cycles wallpapers
from found files.
"""

from __future__ import print_function

import os
import random
import sys
import time

import dbus

from PIL import Image

# pylint: disable=wrong-import-position
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
LOCKSCREEN_DBUS_NAME = "org.gnome.ScreenSaver"
LOCKSCREEN_DBUS_PATH = "/org/gnome/ScreenSaver"
SEND_NOTIFICATIONS = True
MIN_TIME = 1 * 60
MAX_TIME = 5 * 60
PRIMARY_ORIENTATION = "landscape"

SCREENSAVER_INTERFACE = None


def filter_wallpapers(full_path, m_time, last_read):
    """
    Given a path to an image, check to see if it is applicable to add to
    the new wallpaper list; criteria include aspect ratio, last modified
    time, and extension.
    """

    _, extension = os.path.splitext(full_path)

    is_valid_extension = extension.lower() in WALLPAPER_EXTS
    is_new_mtime = m_time > last_read
    if not is_valid_extension or not is_new_mtime:
        return is_valid_extension and is_new_mtime

    image = Image.open(full_path)
    is_correct_ratio = True
    if PRIMARY_ORIENTATION == "landscape":
        is_correct_ratio = image.width >= image.height
    else:
        is_correct_ratio = image.height >= image.width

    image.close()

    return is_correct_ratio



def list_wallpapers():
    """
    Return a list of all wallpapers added since last_read, sorted by last
    modified time.
    """

    result = []

    for candidate in os.listdir(WALLPAPER_PATH):
        result.append(candidate)

    return result


def send_notification(image_location, image_name):
    """
    Send a notification about the new image.
    """

    if bool(SCREENSAVER_INTERFACE.GetActive()):
        return None

    notification = Notify.Notification.new(image_location, image_name, "image-x-generic-symbolic")
    notification.show()
    return notification


def set_path(g_path, g_key, image_name):
    """
    Set wallpaper via Gio introspection calls.
    """

    image_path = os.path.abspath(os.path.join(WALLPAPER_PATH, image_name))

    file_uri = "file://%s" % (image_path)
    gso = Gio.Settings.new(g_path)
    gso.set_string(g_key, file_uri)


def set_wallpaper(image_name, last_notification):
    """
    Set the given image as a wallpaper photo.
    """

    notification = None
    set_path(WALLPAPER_GIO_PATH, WALLPAPER_GIO_KEY, image_name)

    if SEND_NOTIFICATIONS:
        if last_notification:
            last_notification.close()
        notification = send_notification("Wallpaper", image_name)

    print("Set wallpaper: %s" % (image_name))
    return notification


def set_lockscreen(image_name, last_notification):
    """
    Set the given image as a lockscreen photo.
    """

    notification = None
    set_path(LOCKSCREEN_GIO_PATH, LOCKSCREEN_GIO_KEY, image_name)

    if SEND_NOTIFICATIONS:
        if last_notification:
            last_notification.close()
        notification = send_notification("Lock Screen", image_name)

    print("Set lockscreen: %s" % (image_name))
    return notification


def get_random_wallpaper(wallpapers):
    """
    From a list of wallpapers, return a random item.
    """

    new_array = wallpapers[:]
    random.shuffle(new_array)
    return new_array[0]


def get_wallpaper_choice_internal(wallpapers, unseen_wallpapers):
    """
    Internal helper method for getting a wallpaper, prioritizing those which
    are unseen.
    """

    if unseen_wallpapers:
        return unseen_wallpapers.pop()

    l_wallpapers = len(wallpapers)
    hl_wallpapers = l_wallpapers//2
    ql_wallpapers = hl_wallpapers//2
    tql_wallpapers = hl_wallpapers + ql_wallpapers
    if l_wallpapers < 5:
        return get_random_wallpaper(wallpapers)

    num = random.randint(0, 20)
    if num <= 11:
        return get_random_wallpaper(wallpapers[0:ql_wallpapers])
    if num <= 17:
        return get_random_wallpaper(wallpapers[0:hl_wallpapers])
    if num <= 19:
        return get_random_wallpaper(wallpapers[0:tql_wallpapers])
    return get_random_wallpaper(wallpapers)


def get_wallpaper_choice(wallpapers, unseen_wallpapers):
    """
    Return a new wallpaper prioritizing those which are unseen and ensuring
    that the path is still valid.
    """

    path = ""
    wallpaper = None
    while not os.path.exists(path):
        wallpaper = get_wallpaper_choice_internal(wallpapers, unseen_wallpapers)
        path = os.path.join(WALLPAPER_PATH, wallpaper)

    return wallpaper


def main():
    """
    Main loop for setting wallpapers.
    """

    global SCREENSAVER_INTERFACE

    wallpapers = list_wallpapers()
    if not wallpapers:
        print("Please populate %s with at least one wallpaper!" %
              WALLPAPER_PATH, file=sys.stderr)
        return

    wallpaper_notification = None
    lockscreen_notification = None

    if SEND_NOTIFICATIONS:
        # Initialize notifications for this app
        Notify.init('Wallpapers')

        # Check the screensaver state: when not active, we'll send a
        # notification and update the wallpaper(s).
        session_bus = dbus.SessionBus()
        screensaver_obj = session_bus.get_object(LOCKSCREEN_DBUS_NAME,
                                                 LOCKSCREEN_DBUS_PATH)
        SCREENSAVER_INTERFACE = dbus.Interface(screensaver_obj,
                                               LOCKSCREEN_DBUS_NAME)

    # Whether or not to update the lockscreen photo the next time we're
    # unlocked.
    update_lockscreen = True

    try:
        while True:
            wallpapers = list_wallpapers()

            if not bool(SCREENSAVER_INTERFACE.GetActive()):
                wallpaper = get_random_wallpaper(wallpapers)
                wallpaper_notification = set_wallpaper(wallpaper, wallpaper_notification)

                # When we've been locked long enough to trigger this loop,
                # update_loockscreen will become True. Once unlocked, change
                # the lockscreen wallpaper as well. Then quit modifying it
                # until the next time.
                #
                # This lets us see new lockscreen photos and only trigger a
                # notification when the computer is awake, allowing it to
                # sleep longer.
                if update_lockscreen:
                    wallpaper = get_random_wallpaper(wallpapers)
                    lockscreen_notification = set_lockscreen(wallpaper, lockscreen_notification)
                    update_lockscreen = False
            else:
                update_lockscreen = True

            time.sleep(random.randint(MIN_TIME, MAX_TIME))
    except Exception as excpt:
        if SEND_NOTIFICATIONS:
            Notify.uninit()

        raise excpt


if __name__ == "__main__":
    main()
