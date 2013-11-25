import unittest

class TrivialTranslationTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_default_strings(self):
        config = {
            'id': 'sample_element',
            'label': 'hello world!',
            'some_attribute': 'another attribute',
            'translation': {
                'de': {
                    'label': 'Hallo, Weld!',
                    'some_attribute': 'noch einer Attribut'},
                'es': {
                    'label': '¡Hola, mundo!',
                    'some_attribute': 'otro atributo'}
            }
        }

        expected_german = {
            'id': 'sample_element',
            'label': 'Hallo, Weld!',
            'some_attribute': 'noch einer Attribut',
        }
        self.assertEqual(palisades.translation.translate_config(config, 'de'),
            expected_german)

        expected_spanish = {
            'id': 'sample_element',
            'label': '¡Hola, mundo!',
            'some_attribute': 'otro atributo',
        }
        self.assertEqual(palisades.translation.translate_config(config, 'es'),
            expected_spanish)
