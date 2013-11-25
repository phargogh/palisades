import json

import palisades.utils

def translate_config(config, lang_code):
    pass

def translate_json(json_uri, lang_code):
    user_config = palisades.utils.load_json(json_uri)
    return translate_config(user_config, lang_code)

