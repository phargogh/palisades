import json
from types import DictType
from types import ListType

import palisades.utils

# assume per-attribute translation
def translate_config(config, lang_code, extra_keys=[]):
    assert type(config) is DictType
    assert type(extra_keys) is ListType

    translated_config = config.copy()

    translateable_keys = ['label', 'modelName', 'helpText'] + extra_keys

    for known_key in translateable_keys:
        # get the old value.  If it's a dictionary, assume that it's a
        # translation object and fetch the correct value.
        # if not a dict, return the original string.
        try:
            config_value = config[known_key]
            if type(config_value) is DictType:
                translated_string = config_value[lang_code]
            else:
                translated_string = config_value
            translated_config[known_key] = translated_string
        except KeyError:
            # the translateable key was not found, so we can just pass.
            pass

    return translated_config






def translate_json(json_uri, lang_code):
    user_config = palisades.utils.load_json(json_uri)
    return translate_config(user_config, lang_code)

