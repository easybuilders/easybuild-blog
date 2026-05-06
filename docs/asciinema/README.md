# asciinema

This folder contains the [asciinema](https://www.asciinema.org/) javascript and css files.
These have been downloaded from the [asciinema release page](https://github.com/asciinema/asciinema-player/releases).

## Update asciinema

1. Download `asciinema-player.css` and `asciinema-player.min.js` from the [latest asciinema release}(https://github.com/asciinema/asciinema-player/releases).
1. Rename both files to add in the version (`-VERSION`) they correspond too.
   * `mv asciinema-player.css asciinema-player-VERSION.css`
   * `mv asciinema-player.min.js asciinema-player-VERSION.min.js`
1. Edit `mkdocs.yml` to update the information in `extra_css` and `extra_javascript`.
1. Delete the old versions of these files.

