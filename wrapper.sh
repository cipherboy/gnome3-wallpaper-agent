#!/bin/bash

script_dir="$(dirname "${BASH_SOURCE[@]}")"
config_dir="$HOME/.config/gnome3-wallpaper-agent"

mkdir -p "$config_dir"

echo "$BASHPID" > "$config_dir/gnome3-wallpaper-agent.pid"

while [ 1 ]; do
    python3 "$script_dir/wallpaper_agent.py" 2>&1 > "$config_dir/gnome3-wallpaper-agent.log" 2>&1
done
