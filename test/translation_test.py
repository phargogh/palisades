# -*- coding: utf-8 -*-

import unittest


class TrivialTranslationTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_default_strings(self):
        import palisades.i18n.translation
        config = {
            'id': 'sample_element',
            'label': {
                'en': 'hello world!',
                'de': 'Hallo, Weld!',
                'es': u'¡Hola, mundo!',
            },
        }

        expected_german = {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
        }
        self.assertEqual(palisades.i18n.translation.translate_config(config, 'de'),
            expected_german)

        expected_spanish = {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
        }
        self.assertEqual(palisades.i18n.translation.translate_config(config, 'es'),
            expected_spanish)

    def test_extra_keys(self):
        import palisades.i18n.translation
        config = {
            'id': 'sample_element',
            'label': {
                'en': 'hello world!',
                'de': 'Hallo, Weld!',
                'es': u'¡Hola, mundo!',
            },
            'some_attribute': {
                'en': 'another attribute',
                'de': 'noch einer Attribut',
                'es': 'otro atributo',
            }
        }

        expected_german = {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
            'some_attribute': 'noch einer Attribut',
        }
        self.assertEqual(palisades.i18n.translation.translate_config(config, 'de',
            ['some_attribute']), expected_german)

        expected_spanish = {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
            'some_attribute': 'otro atributo',
        }
        self.assertEqual(palisades.i18n.translation.translate_config(config, 'es',
            ['some_attribute']), expected_spanish)


    def test_contained_elements(self):
        import palisades.i18n.translation
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
        self.assertEqual(palisades.i18n.translation.translate_config(config, 'de'),
            expected_german)

    def test_nested_contained_elements(self):
        import palisades.i18n.translation
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
        self.assertEqual(palisades.i18n.translation.translate_config(config, 'de'),
            expected_german)


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


class CompleteLanguageDetection(unittest.TestCase):
    def test_dict_detection(self):
        import palisades.i18n.translation
        """Language code detection on trivial config dictionary."""
        user_dict = {
            'label': {
                'en': 'foo',
                'es': 'foo',
                'de': 'foo',
            }
        }
        self.assertEqual(palisades.i18n.translation.fetch_allowed_translations(
            user_dict), ['de', 'en', 'es'])

    def test_dict_with_elements_detection(self):
        """Language code detection with nested elements list."""
        import palisades.i18n.translation
        user_dict = {
            'label': {
                'en': 'foo',
                'es': 'foo',
                'de': 'foo',
            },
            'elements': [
                {
                    'label': {
                        'en': 'bar',
                        'es': 'bar',
                        'de': 'bar',
                    }
                }
            ]
        }
        self.assertEqual(palisades.i18n.translation.fetch_allowed_translations(
            user_dict), ['de', 'en', 'es'])

    def test_dict_with_palisades_unsupported_lang(self):
        """When a user lang is unsupportedi by palisades"""
        import palisades.i18n.translation
        user_dict = {
            'label': {
                'foo': 'this is an unsupported language',
                'es': 'supported',
                'de': 'supported',
            }
        }
        self.assertEqual(palisades.i18n.translation.fetch_allowed_translations(
            user_dict), ['de', 'es'])

    def test_dict_with_user_keys(self):
        """When a user defines extra translateable keys"""
        import palisades.i18n.translation
        user_dict = {
            'extra_key': {
                'es': 'supported',
                'de': 'supported',
            }
        }
        self.assertEqual(palisades.i18n.translation.fetch_allowed_translations(
            user_dict, extra_keys=['extra_key']), ['de', 'es'])
