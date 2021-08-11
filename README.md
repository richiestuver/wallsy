# wallsy

The best image modifier for custom desktop wallpapers and other creative uses.

*** Software Under Construction! Stay tuned for updates.***
## TODO
- [ ] Write filter effects handler
- [ ] Write file handler
- [ ] Write search query handler
- [ ] Write scheduler
- [ ] Write pipeline processing logic for CLI
- [ ] Error handling on CLI 
- [ ] Unit tests for the above


## Usage:

Wallsy is designed to chain commands together into powerful one-line expressions to collect, edit, and use images.

1) (Required) specify an input image using either 'new' or 'random' commands, e.g. 

```
$ wallsy new --file="photo.jpg" [ADDITIONAL COMMANDS]
```

2) (Optional) apply desired image manipulations using 'effects' command, e.g. 

```
$ wallsy [new | random] effects --blur=20 [ADDITIONAL COMMANDS]
```

3) (Optional) save image or set the resulting image as a new desktop background using 'save' or 'desktop' commands, e.g. 

```
$ wallsy [new | random] save --name="myphoto" [ADDITIONAL COMMANDS]
```

## Examples:

- Update desktop background with a random wallpaper

    ```
    $ wallsy random background
    ```

- Add a blur to an image and set it as the desktop background

    ```
    $ wallsy new --file="my-wallpaper.jpg" effects --blur=20 background
    ```

- Convert random "mountain" image to grayscale and save as "myphoto" to the 'documents' directory

    ```
    $ wallsy random -q="mountain" effects --grayscale save --dest="~/documents" --name="myphoto"
    ```

## Help
For detailed help text run the --help modifier with the specified command, e.g.

```
$ wallsy background --help
```