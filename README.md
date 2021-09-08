# wallsy

Create beautiful images, effects, and desktop wallpapers through composable edits on the command line.

  * [Requirements](#requirements)
    * [Supported Platforms and Environments](#supported-platforms-and-environments)
  * [Installation](#installation)
    * [Dependencies](#dependencies)
    * [Development Installation](#development-installation)
  * [Quickstart](#quickstart)
  * [Usage](#usage)
    * [Specify an input image or grab a random image either online or locally](#specify-an-input-image-or-grab-a-random-image-either-online-or-locally)
    * [Apply effects to an image in a fully composable way](#apply-effects-to-an-image-in-a-fully-composable-way,-eg)
    * [Desktop wallpaper support - automatically update your desktop or use your current desktop image as input](#desktop-wallpaper-support---automatically-update-your-desktop-or-use-your-current-desktop-image-as-input,-eg)
  * [Fine Grained Controls](#fine-grained-controls:)
  * [Help](#help)
    * [Uninstall Wallsy](#uninstall-wallsy)
    * [Uninstalling a virtual environment](#uninstalling-a-virtual-environment)

## Requirements

- Python 3.9+
- Gnome Shell 3.38*

*required in order to use desktop wallpaper command

### Supported Platforms and Environments
- OS: Ubuntu 21.04
- DE: Gnome 3.38
- Shell: Bash, Zsh

MacOS and Windows are not supported at this time. Use at your own risk.

## Installation

The latest version of wallsy can be downloaded from Github using pip:
```
pip install git+https://github.com/richiestuver/wallsy.git#egg=wallsy
```

An official PyPI package may be made available in the future. 

### Dependencies

wallsy requires the following Python packages:
- Click
- Pillow
- Rich
- PyGObject 
- Requests

### Development Installation
See [requirements.txt](https://github.com/richiestuver/wallsy/blob/master/requirements.txt) for dependencies. Recommended to create a virtual environment first: 

```
python -m venv .venv
source .venv/bin/activate
``` 

```bash
$ git clone https://github.com/richiestuver/wallsy.git
$ cd wallsy
$ pip install -r requirements.txt
$ pip install .
```

## 
## Quickstart

**Change your desktop wallpaper with a random featured photo from Unsplash**
```
$ wallsy random desktop
```

**Add an effect (e.g. posterize or noir) to your current desktop wallpaper**
```
$ wallsy desktop posterize desktop
```


## Usage
Wallsy is designed to chain commands together into powerful one-line expressions to collect, edit, and compose images with a
focus on use in personal applications like wallpapers, background images for streaming/creative applications, etc.

- To see all available commands, run `wallsy --help`

- For help on specific commands, run `wallsy [command] --help`

---
### Specify an input image or grab a random image either online or locally

**Get a random image from Unsplash Source and show it using default image viewer**

```
$ wallsy random show
```

**Get a random image from your ~/wallsy folder**
```
$ wallsy random --local show
```

**Add a new image to your ~/wallsy folder**
```
$ wallsy --file myphoto.jpeg show
```

**Grab an image from a url**
```
$ wallsy --url https://example.com/myphoto.jpg show
```
---
### Apply effects to an image in a fully composable way, e.g.


**Create a poster effect of a photo of your dog**
```
$ wallsy --file mydog.jpeg posterize show
```

**Blur a random "nature" image from Unsplash Source**
```
$ wallsy random --keyword "nature" blur show
```

**Add blur and noir effects to a random 4k image of Tokyo, Japan**
```
$ wallsy random --keyword "tokyo" --size 3840 2160 blur noir show
```
---
### Desktop wallpaper support - automatically update your desktop or use your current desktop image as input, e.g.

**Generate a custom image and update your desktop wallpaper**
```
$ wallsy random --keyword="new york city" --keyword="skyline" noir desktop
```

**Use your current wallpaper as input for some cool effects then save it back to your wallpaper**
```
$ wallsy desktop blur noir posterize desktop
```

## Fine Grained Controls
Wallsy tries to provide sensible defaults for simple usage but expose enough controls
to allow you to tweak edits to get the results you want. Most effect commands allow
you to vary the level of the effect.

---
**Apply a 20px blur to a photo and add a posterization effect reducing to 16 colors**
```
wallsy --file myfile.jpg blur --radius=20px posterize colors=16 show
```
---
## Help


To see what's available and for detailed help text add `--help` to the specified command, e.g.
```bash
$ wallsy random --help
$ wallsy posterize --help
```

### Uninstall Wallsy

Uninstall wallsy with pip:

```
pip uninstall wallsy
```

This will not uninstall wallsy's dependencies. If you need to do so, see [dependencies](#dependencies) and run `pip uninstall` for each you want to remove. 

### Uninstalling a virtual environment

If you used a virtual environment to install wallsy, you can simply delete the virtual environment directory to remove wallsy. 

If your virtual environment is in the folder myvirtualenv:
```bash
$ rm -r myvirtualenv
```

**Have fun with Wallsy!**