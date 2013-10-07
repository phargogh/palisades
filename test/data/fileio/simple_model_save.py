""""
This is a saved model run from hello.world.
Generated: Mon Oct  7 12:20:13 2013
Palisades version: dev95:null [84233ff95d41]
"""

import hello.world


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

hello.world.execute(args)
