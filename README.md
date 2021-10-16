![build and test status](https://github.com/richiestuver/wallsy/actions/workflows/python-app.yml/badge.svg)
![code coverage](https://img.shields.io/codecov/c/github/richiestuver/wallsy)
![code style: black](https://img.shields.io/badge/code%20style-black-black)
# wallsy

Create beautiful images, effects, and desktop wallpapers through composable edits on the command line.

  * [Requirements](#requirements)
    * [Supported Platforms and Environments](#supported-platforms-and-environments)
  * [Installation](#installation)
    * [Dependencies](#dependencies)
    * [Development Installation](#development-installation)
  * [Quickstart](#quickstart)
  * [Usage](#usage)
  * [Examples](#examples)
    * [Specify an input image or grab a random image either online or locally](#specify-an-input-image-or-grab-a-random-image-either-online-or-locally)
    * [Apply effects to an image in a fully composable way](#apply-effects-to-an-image-in-a-fully-composable-way)
    * [Automatically update your desktop or use your current desktop image as input](#automatically-update-your-desktop-or-use-your-current-desktop-image-as-input)
  * [Fine Grained Controls](#fine-grained-controls)
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

MacOS and Windows are not supported at this time. Desktop wallpaper commands are not likely to work on these platforms currently.

## Installation

The latest version of `wallsy` can be downloaded from Github using pip:
```
$ pip install git+https://github.com/richiestuver/wallsy.git#egg=wallsy
```

An official PyPI package may be made available in the future. 

### Dependencies

`wallsy` requires the following Python packages:
- Click
- Pillow
- Rich
- Requests

### Development Installation
See [requirements.txt](https://github.com/richiestuver/wallsy/blob/master/requirements.txt) for dependencies. Recommended to create a virtual environment first: 

```
$ python -m venv .venv
$ source .venv/bin/activate
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
`wallsy` is designed to chain commands together into powerful **one-line** expressions to collect, edit, and compose images with a
focus on use in personal applications like wallpapers, background images for streaming/creative applications, etc.

### Sourcing images
- Give `wallsy` a file name or url pointing to an image
- Let `wallsy` grab an image from Unsplash using 'random'
    - Add search terms and image dimensions to filter the kind of images 'random' selects from
- Get a random image from a local directory 
- Use your current desktop wallpaper as input to `wallsy`

### Applying Effects
- Chain any number of effect commands together to create custom image manipulations:
    - 'blur' - add a Gaussian blur effect in varying sizes
    - 'noir' - convert a color image to black and white
    - 'posterize' - add a poster effect with varying number of colors

### Show the Results
- Set the resulting image as your desktop wallpaper
- Open images automatically in default image viewer

- To see all available commands, run `wallsy --help`
- For help on specific commands, run `wallsy [command] --help`

## Examples
---
### Specify an input image or grab a random image either online or locally

**Get a random image from [Unsplash](https://unsplash.com) and show it using default image viewer**

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
### Apply effects to an image in a fully composable way


**Create a poster effect of a favorite photo**
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
### Automatically update your desktop or use your current desktop image as input

**Generate a custom image and update your desktop wallpaper**
```
$ wallsy random --keyword="new york city" --keyword="skyline" noir desktop
```

**Use your current wallpaper as input for some cool effects then save it back to your wallpaper**
```
$ wallsy desktop blur noir posterize desktop
```

## Fine Grained Controls
`wallsy` tries to provide sensible defaults for simple usage but expose enough controls
to allow you to tweak edits to get the results you want. Most effect commands allow
you to vary the level of the effect.

---
**Apply a 20px blur to a photo and add a posterization effect reducing to 16 colors**
```
$ wallsy --file myfile.jpg blur --radius=20px posterize colors=16 show
```
---
## Help


To see what's available and for detailed help text add `--help` to the specified command, e.g.
```bash
$ wallsy random --help
$ wallsy posterize --help
```

### Uninstall `wallsy`

Uninstall `wallsy` with pip:

```
$ pip uninstall wallsy
```

This will not uninstall `wallsy`'s dependencies. If you need to do so, see [dependencies](#dependencies) and run `pip uninstall` for each you want to remove. 

### Uninstalling a virtual environment

If you used a virtual environment to install `wallsy`, you can simply delete the virtual environment directory to remove `wallsy`. 

If your virtual environment is in the folder myvirtualenv:
```bash
$ rm -r myvirtualenv
```

**Have fun with `wallsy`!**
