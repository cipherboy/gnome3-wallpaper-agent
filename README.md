# gnome3-wallpaper-agent

From `~/Pictures/wallpapers`, randomly cycle through wallpapers

To clone:

```bash
git clone https://github.com/cipherboy/gnome3-wallpaper-agent
```

Edit the `Exec=` field in the [desktop file](https://github.com/cipherboy/gnome3-wallpaper-agent/blob/master/gnome3-wallpaper-agent.desktop#L4) with the correct path to the git repository.


Then, to run at startup:

```bash
cd gnome3-wallpaper-agent # if not already in the cloned git repository
mkdir -p ~/.config/autostart/
cp gnome3-wallpaper-agent.desktop ~/.config/autostart
```
