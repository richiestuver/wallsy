"""
Gnomesplash - update Gnome background wallpaper with beautiful Unsplash photos

Gnomesplash allows users to refresh their wallpaper with random photos from Unsplash
that can be filtered by curated topics. Users can also schedule wallpapers
to auto update on a recurring interval. 
"""

import os.path

"""
Gnome desktop stores images that users add through the settings GUI to the directory
/home/{user}/.local/share/backgrounds'. Images found in this directory will show up in 
the GUI so for management this is the ideal location to store as a default. Note that the
popular Gnome Tweak Tool (not the built in settings app) does NOT save images to this location.
"""
# TODO: check that this location exists. if not, create it. download image and save to this location.
wallpaper_location = os.path.expanduser("~/.local/share/backgrounds")


if __name__ == "__main__":
    pass
