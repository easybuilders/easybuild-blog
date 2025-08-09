# Based on https://github.com/chipsenkbeil/distant.dev/blob/8894e68cdb0424e4ed707425ca77dff5458429be/macros.py
import uuid


def value_str(value):
    s = str(value)
    if isinstance(value, bool):
        s = s.lower()
    return s


def define_env(env):
    @env.macro
    def asciinema(file, **kwargs):

        html = ""

        # Options reference: https://docs.asciinema.org/manual/player/options/
        # Can override values (or append further options) using kwargs
        opts = {
            "autoPlay": True,
            "controls": "\"auto\"",
            "loop": True,
            "idleTimeLimit": 2,  # reduce inactivity in shell
            "cols": 110,  # define default width
            "rows": 20,  # define default height
            "theme": "\"dracula\""
        }

        # Adding this additional option to allow for a custom div width.
        # This is NOT a native asciinema option but one that will be used
        # to set the width of the div that contains the player
        opts["div_width"] = "100%"

        # Overwrite defaults with kwargs
        for key, value in kwargs.items():
            opts[key] = value

        # Create an empty div that we will use for the player
        div_id = "asciinema-" + str(uuid.uuid4())
        style_options = {
            "z-index": "1",
            "position": "relative",
            "width": opts.pop('div_width'),
            "box-sizing": "border-box",
            # "border": "transparent solid 10px",
        }
        div_style = "; ".join({f"{k}: {value_str(v)}" for k, v in style_options.items()})
        html += f"<div id='{div_id}' style='{div_style}'></div>"

        # Define JS representing creating the player
        player_opts = ", ".join({f"'{k}': {value_str(v)}" for k, v in opts.items()})
        create_player_js = f"AsciinemaPlayer.create('{file}', document.getElementById('{div_id}'), {{ {player_opts} }});"

        # Create script tag that will perform cast by either registering for the DOM to
        # load or firing immediately if already loaded
        html += "<script>"
        html += "if (document.readyState === 'loading') {"
        html += "document.addEventListener('DOMContentLoaded', function() {"
        html += create_player_js
        html += "});"
        html += "} else {"
        html += create_player_js
        html += "}"
        html += "</script>"

        return html
