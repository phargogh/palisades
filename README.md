palisades
=========

Configurable UI chunks for PyQt user interfaces

Let's assume that you already have an InVEST User Interface-compatible JSON configuration object.
Convert this to paliasades like so:

    $ python scripts/convert_config.py <iui_config>.json converted_config.json
    $ python
    >>> import palisades
    >>> palisades.launch('converted_config.json')

Converting iui config to palisades format
-----------------------------------------
    usage: convert_config.py [-h] [-l LANGUAGES [LANGUAGES ...]] [-d DEFAULT_LANG]
                         iui_uri out_uri
