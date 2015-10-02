# -*- coding: utf-8 -*-


import json
from types import DictType
from types import ListType

import palisades.utils

TRANS_KEYS = ['label', 'modelName', 'helpText']

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

    # Copying the input configuration prevents side effects and also allows us
    # to retain all the configuration options, whatever they may be.
    translated_config = config.copy()

    # these are the known keys to be checked for translation.  User-defined keys
    # are searched in addition to these predefined keys.
    translateable_keys = TRANS_KEYS + extra_keys

    for known_key in translateable_keys:
        # get the old value.  If it's a dictionary, assume that it's a
        # translation object and fetch the correct value.
        # if not a dict, return the original string.
        try:
            config_value = config[known_key]

            # If the value is a dictionary, it's expected to be a translation
            # dictionary mapping language code to the translated string.
            # if it's not a language dictionary, we just leave the value alone,
            # whatever it may be.
            if type(config_value) is DictType:
                translated_string = config_value[lang_code]
            else:
                translated_string = config_value
            translated_config[known_key] = translated_string
        except KeyError:
            # the translateable key was not found, so we can just pass.
            pass

    # If this element is a Group, we want to recurse through all contained
    # elements, translating as we go.
    if 'elements' in config:
        translated_elements_list = []
        for element_config in config['elements']:
            translated_element_config = translate_config(element_config,
                lang_code, extra_keys)
            translated_elements_list.append(translated_element_config)

        translated_config['elements'] = translated_elements_list

    return translated_config

def fetch_allowed_translations(user_config, extra_keys=[]):
    """Determine which languaes have complete translations in `config`.

    Returns:
        A sorted tuple of language codes.
    """

    # initialize this to the set of available languages.
    complete_translations = set(palisades.i18n.available_langs())

    translateable_keys = TRANS_KEYS + extra_keys

    def _recurse(config):
        for known_key in translateable_keys:
            try:
                config_value = config[known_key]
                if isinstance(config_value, dict):
                    config_langs = set(config_value.keys())
                    complete_translations.intersection_update(config_langs)
            except KeyError:
                # The translateable key was not found, so pass.
                pass

        try:
            for element_config in config['elements']:
                _recurse(element_config)
        except KeyError:
            pass

    _recurse(user_config)
    return sorted(complete_translations)

def translate_json(json_uri, lang_code):
    user_config = palisades.utils.load_json(json_uri)
    return translate_config(user_config, lang_code)
