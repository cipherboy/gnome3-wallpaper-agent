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
gi.require_version('Gdk', '3.0')
from gi.repository import Notify
from gi.repository import Gio
from gi.repository import Gdk

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
TEMP_DIRECTORY = os.path.expanduser("~/.cache/gnome3-wallpaper-agent")

SCREENSAVER_INTERFACE = None

GDK_SCREEN = Gdk.Screen.get_default()
GDK_DISPLAY = GDK_SCREEN.get_display()


def list_wallpapers():
    """
    Return a list of all wallpapers added since last_read, sorted by last
    modified time.
    """

    result = []

    for candidate in os.listdir(WALLPAPER_PATH):
        result.append(candidate)

    return result


def get_screen_sizes():
    results = []
    for index in range(0, GDK_DISPLAY.get_n_monitors()):
        monitor = GDK_DISPLAY.get_monitor(index)
        geometry = monitor.get_geometry()
        results.append((geometry.width, geometry.height))

    return results


def get_max_screen_size():
    results = get_screen_sizes()
    winner_area = 0
    winner = None

    for result in results:
        area = result[0] * result[1]
        if area > winner_area:
            winner_area = area
            winner = result

    return winner


def compute_ratio(image_width, image_height, screen_width, screen_height):
    resized_to_height = int(image_width / image_height * screen_height)
    resized_to_width = int(image_height / image_width * screen_width)

    if image_width < screen_width or image_height < screen_height:
        return image_width, image_height

    if resized_to_height >= screen_width:
        return resized_to_height, screen_height

    return screen_width, resized_to_width


def resize_all():
    if not os.path.exists(TEMP_DIRECTORY):
        os.makedirs(TEMP_DIRECTORY)

    screen_width, screen_height = get_max_screen_size()

    resized_mapping = dict()

    for wallpaper in list_wallpapers():
        full_path = os.path.join(WALLPAPER_PATH, wallpaper)
        name, ext = os.path.splitext(wallpaper)
        temp_name = f"{name}-{screen_width}x{screen_height}{ext}"
        temp_path = os.path.join(TEMP_DIRECTORY, temp_name)

        resized_mapping[wallpaper] = temp_path

        if os.path.exists(temp_path):
            continue

        img = Image.open(full_path)
        img_width, img_height = img.size

        new_width, new_height = compute_ratio(img_width, img_height, screen_width, screen_height)

        resized_img = img.resize((new_width, new_height), Image.BICUBIC)
        resized_img.save(temp_path, quality=95)

    return resized_mapping


def send_notification(image_location, image_name):
    """
    Send a notification about the new image.
    """

    if bool(SCREENSAVER_INTERFACE.GetActive()):
        return None

    notification = Notify.Notification.new(image_location, image_name, "image-x-generic-symbolic")
    notification.show()
    return notification


def set_path(g_path, g_key, image_name, mapping):
    """
    Set wallpaper via Gio introspection calls.
    """

    image_path = os.path.abspath(mapping[image_name])

    file_uri = "file://%s" % (image_path)
    gso = Gio.Settings.new(g_path)
    gso.set_string(g_key, file_uri)


def set_wallpaper(image_name, last_notification, mapping):
    """
    Set the given image as a wallpaper photo.
    """

    notification = None
    set_path(WALLPAPER_GIO_PATH, WALLPAPER_GIO_KEY, image_name, mapping)

    if SEND_NOTIFICATIONS:
        if last_notification:
            last_notification.close()
        notification = send_notification("Wallpaper", image_name)

    print("Set wallpaper: %s" % (image_name))
    return notification


def set_lockscreen(image_name, last_notification, mapping):
    """
    Set the given image as a lockscreen photo.
    """

    notification = None
    set_path(LOCKSCREEN_GIO_PATH, LOCKSCREEN_GIO_KEY, image_name, mapping)

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

    resized_mapping = resize_all()

    try:
        while True:
            wallpapers = list_wallpapers()

            if not bool(SCREENSAVER_INTERFACE.GetActive()):
                wallpaper = get_random_wallpaper(wallpapers)
                wallpaper_notification = set_wallpaper(wallpaper, wallpaper_notification, resized_mapping)

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
                    lockscreen_notification = set_lockscreen(wallpaper, lockscreen_notification, resized_mapping)
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
