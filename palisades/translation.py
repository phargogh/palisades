import json
from types import DictType
from types import ListType

import palisades.utils

# assume per-attribute translation
def translate_config(config, lang_code, extra_keys=[]):
    """Translate a dictionary containing element configuration options.  Any
        keys that are not translated are left untouched.

        config - a python dictionary contained configuration options
        lang_code - a python language code matching the language to translate
            to.  This absolutely must match the language identifier in the
            configuration.  See below for example configuration.
        extra_keys=[] - keys to be translated.  Default keys translated are:
            ['label', 'modelName', 'helpText']

        ========================
        A simple configuration dictionary such as:
        {
            'id': 'sample_element',
            'label': {
                'en': 'hello world!',
                'de': 'Hallo, Weld!',
                'es': u'¡Hola, mundo!',
            },
        }

        will translate to this when the 'de' language code is used:
        {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
        }

        The same dictionary will translate to this when 'es' is the input
        language code:
        {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
        }

        ========================
        A more complicated configuration dictionary:
        {
            'id': 'sample_element',
            'label': {
                'en': 'hello world!',
                'de': 'Hallo, Weld!',
                'es': u'¡Hola, mundo!',
            },
            'elements': [
                {
                    'id': 'element_1',
                    'label': {
                        'en': 'element one',
                        'de': 'das Element eins',
                        'es': 'elemento uno',
                    }
                },
                {
                    'id': 'element_2',
                    'label': {
                        'en': 'element two',
                        'de': 'das Element zwei',
                        'es': 'elemento dos',
                    }
                }
            ]
        }

        This will translate to German as so:
        {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
            'elements': [
                {
                    'id': 'element_1',
                    'label': 'das Element eins',
                },
                {
                    'id': 'element_2',
                    'label': 'das Element zwei',
                }
            ]
        }


        returns a python dictionary."""

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

    if 'elements' in config:
        translated_elements_list = []
        for element_config in config['elements']:
            translated_element_config = translate_config(element_config,
                lang_code, extra_keys)
            translated_elements_list.append(translated_element_config)

        translated_config['elements'] = translated_elements_list

    return translated_config




def translate_json(json_uri, lang_code):
    user_config = palisades.utils.load_json(json_uri)
    return translate_config(user_config, lang_code)

