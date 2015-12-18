# -*- coding: utf-8 -*-

import unittest


class TrivialTranslationTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    @staticmethod
    def _trivial_default_strings():
        return {
            'id': 'sample_element',
            'label': {
                'en': 'hello world!',
                'de': 'Hallo, Weld!',
                'es': u'¡Hola, mundo!',
            },
        }

    def test_default_strings_de(self):
        from palisades.i18n.translation import translate_config
        config = TrivialTranslationTest._trivial_default_strings()

        expected_german = {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
        }
        self.assertEqual(
            translate_config(config, 'de'),
            ([('de', 'en', 'es')], expected_german))

    def test_default_strings_es(self):
        from palisades.i18n.translation import translate_config
        config = TrivialTranslationTest._trivial_default_strings()

        expected_spanish = {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
        }
        self.assertEqual(
            translate_config(config, 'es'),
            ([('de', 'en', 'es')], expected_spanish))

    def test_extra_keys_de(self):
        from palisades.i18n.translation import translate_config
        config = TrivialTranslationTest._trivial_default_strings()

        config['some_attribute'] = {
            'en': 'another attribute',
            'de': 'noch einer Attribut',
            'es': 'otro atributo',
        }

        expected_german = {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
            'some_attribute': 'noch einer Attribut',
        }
        self.assertEqual(
            translate_config(config, 'de', ['some_attribute']),
            ([('de', 'en', 'es')], expected_german))

    def test_extra_keys_es(self):
        from palisades.i18n.translation import translate_config
        config = TrivialTranslationTest._trivial_default_strings()

        config['some_attribute'] = {
            'en': 'another attribute',
            'de': 'noch einer Attribut',
            'es': 'otro atributo',
        }

        expected_spanish = {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
            'some_attribute': 'otro atributo',
        }
        self.assertEqual(
            translate_config(config, 'es', ['some_attribute']),
            ([('de', 'en', 'es')], expected_spanish))

    def test_contained_elements(self):
        from palisades.i18n.translation import translate_config
        config = {
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

        expected_german = {
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
        self.assertEqual(
            translate_config(config, 'de'),
            ([('de', 'en', 'es')], expected_german))

    def test_nested_contained_elements(self):
        from palisades.i18n.translation import translate_config
        config = {
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
                    },
                    'elements': [
                        {
                            'id': 'element_10',
                            'label': {
                                'en': 'element ten',
                                'de': 'das Element zehn',
                                'es': 'elemento diez'
                            }
                        }
                    ]
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

        expected_german = {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
            'elements': [
                {
                    'id': 'element_1',
                    'label': 'das Element eins',
                    'elements': [
                        {
                            'id': 'element_10',
                            'label': 'das Element zehn'
                        },
                    ],
                },
                {
                    'id': 'element_2',
                    'label': 'das Element zwei',
                }
            ]
        }
        self.assertEqual(
            translate_config(config, 'de'),
            ([('de', 'en', 'es')], expected_german))


class LanguageExtractionTest(unittest.TestCase):
    @staticmethod
    def _basic_args():
        return {
            'label': {
                'en': 'foo',
                'es': 'foo',
                'de': 'foo',
            }
        }

    def test_primitive(self):
        """Test with a primitive dict."""
        from palisades.i18n.translation import extract_languages
        lang_args = LanguageExtractionTest._basic_args()
        self.assertEqual(extract_languages(lang_args), ['de', 'en', 'es'])

    def test_nested_with_list(self):
        """Test extraction when the config dict contains a list."""
        from palisades.i18n.translation import extract_languages
        lang_args = LanguageExtractionTest._basic_args()
        lang_args['list'] = [{'en':'foo'}, {'es', 'foo'}, {'zh': 'foo'}]
        self.assertEqual(extract_languages(lang_args), ['de', 'en', 'es', 'zh'])

    def test_nexted_with_list_and_dict(self):
        """Text lang extraction when config has nested dicts and lists."""
        from palisades.i18n.translation import extract_languages
        lang_args = LanguageExtractionTest._basic_args()
        lang_args['list'] = [lang_args.copy(), lang_args.copy()]
        lang_args['list'][0]['zh'] = 'foo'
        lang_args['list'][1]['zh'] = 'foo'
        lang_args['label']['zh'] = 'foo'
        self.assertEqual(extract_languages(lang_args), ['de', 'en', 'es', 'zh'])
