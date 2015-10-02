# -*- coding: utf-8 -*-

import unittest

import palisades.i18n.translation

class TrivialTranslationTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_default_strings(self):
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

class CompleteLanguageDetection(unittest.TestCase):
    def test_dict_detection(self):
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
        user_dict = {
            'extra_key': {
                'es': 'supported',
                'de': 'supported',
            }
        }
        self.assertEqual(palisades.i18n.translation.fetch_allowed_translations(
            user_dict, extra_keys=['extra_key']), ['de', 'es'])
