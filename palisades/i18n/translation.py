# -*- coding: utf-8 -*-


import json
from types import DictType
from types import ListType

import palisades.utils

TRANS_KEYS = ['label', 'modelName', 'helpText', 'options']

# assume per-attribute translation
def translate_config(config, lang_code, extra_keys=[], allowed_translations=[]):
    """Translate a dictionary containing element configuration options.

    Any keys that are not translated are left untouched.

    config - a python dictionary contained configuration options
    lang_code - a python language code matching the language to translate
        to.  This absolutely must match the language identifier in the
        configuration.  See below for example configuration.
    extra_keys=[] - keys to be translated.  Default keys translated are:
        ['label', 'modelName', 'helpText']
    allowed_translations=[] - initialize the allowed translations for
        this run through the configuration dictionary.

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
                # track the translations available so we can check which
                # languages are complete.
                allowed_translations.append(config_value.keys())
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
            local_translations, translated_element_config = translate_config(
                element_config, lang_code, extra_keys, allowed_translations)
            allowed_translations = local_translations
            translated_elements_list.append(translated_element_config)

        translated_config['elements'] = translated_elements_list

    if len(allowed_translations) > 0:
        complete_translations = [tuple(reduce(lambda x, y: x.intersection(y),
                                         [set(z) for z in allowed_translations]))]
    else:
        complete_translations = []

    return complete_translations, translated_config

def translate_json(json_uri, lang_code):
    user_config = palisades.utils.load_json(json_uri)
    translations, translated_config = translate_config(user_config, lang_code)
    return list(translations[0]), translated_config

def extract_languages(config):
    """Returns a list of language codes found in this configuration object."""

    max_key_len = lambda y: max(map(lambda x: len(x), y))
    min_key_len = lambda y: min(map(lambda x: len(x), y))
    language_sets = []

    def recurse(dict_config):
        # check if this is a language dict.
        keys = dict_config.keys()
        if max_key_len(keys) == 2 and min_key_len(keys) == 2:
            langauge_sets.append(dict_config.keys())
        else:
            for key, value in dict_config.iteritems():
                if type(value) is DictType:
                    recurse(value)

    # start the recursion to get the list of language keys.
    recurse(config)

    # get max and min element len.
    if max_key_len(language_sets) == min_key_len(language_sets):
        return language_sets[0]
    else:
        # we need to determine the minimal subset that are in all of the
        # translation dictionaries.
        raise Exception("Not yet implemented!")

