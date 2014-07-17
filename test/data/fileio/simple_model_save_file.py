""""
This is a saved model run for hello_world.py.
Generated: Thu Jul 17 11:15:18 2014
Palisades version: dev540:null [4047cc6]
"""

import imp
target_script = imp.load_source('target_script', 'hello_world.py')


args = {
        1: 'hello',
        5.5: 'world',
        'a': 1234,
        'b': 5.5,
        'c': [
           0,
           1,
           2,
           3,
        ],
        'd': {
            'a': 'b',
        },
        u'e': 'aaaa',
        u'f': u'qwerty',
}

target_script.execute(args)
