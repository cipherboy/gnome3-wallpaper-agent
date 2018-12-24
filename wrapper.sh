#!/bin/bash

script_dir="$(dirname "${BASH_SOURCE[@]}")"
config_dir="$HOME/.config/gnome3-wallpaper-agent"
pid_file="$config_dir/gnome3-wallpaper-agent.pid"
log_file="$config_dir/gnome3-wallpaper-agent.log"

mkdir -p "$config_dir"

echo "$BASHPID" > "$pid_file"

while true; do
    python3 "$script_dir/wallpaper_agent.py" 2>&1 >> "$log_file" 2>&1

    # Ensure some time between calls so that we don't lock the system when
    # wallpaper_agent.py keeps crashing.
    sleep 60
done
