# -*- coding: utf-8 -*-

import unittest

import palisades.translation

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
        self.assertEqual(palisades.translation.translate_config(config, 'de'),
            expected_german)

        expected_spanish = {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
        }
        self.assertEqual(palisades.translation.translate_config(config, 'es'),
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
        self.assertEqual(palisades.translation.translate_config(config, 'de',
            ['some_attribute']), expected_german)

        expected_spanish = {
            'id': 'sample_element',
            'label': u'¡Hola, mundo!',
            'some_attribute': 'otro atributo',
        }
        self.assertEqual(palisades.translation.translate_config(config, 'es',
            ['some_attribute']), expected_spanish)
