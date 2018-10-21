#!/bin/bash

script_dir="$(dirname "${BASH_SOURCE[@]}")"
config_dir="$HOME/.config/gnome3-wallpaper-agent"

if [ -e "$config_dir/gnome3-wallpaper-agent.pid" ]; then
    pid="$(cat "$config_dir/gnome3-wallpaper-agent.pid")"

    kill "$pid"
    kill -9 "$pid"
fi

ps aux | grep 'wallpaper_agent.py' | awk '{print $2}' | xargs kill
