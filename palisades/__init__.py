import versioning
import sys
import glob
import os

# The __version__ attribute MUST be set to 'dev'.  It is changed automatically
# when the package is built.  The build_attrs attribute is set at the same time,
# but it instead contains a list of attributes of __init__.py that are related
# to the build.
__version__ = 'dev'
build_data = None

if __version__ == 'dev' and build_data == None:
    __version__ = versioning.version()
    build_data = versioning.build_data()
    for key, value in sorted(build_data.iteritems()):
        setattr(sys.modules[__name__], key, value)

    del sys.modules[__name__].key
    del sys.modules[__name__].value


# Layouts, for later reference.
LAYOUT_VERTICAL = 1
LAYOUT_HORIZONTAL = 2
LAYOUT_GRID = 3

def get_py2exe_datafiles():
    """Return a list of tuples of data required for a py2exe installation of
    palisades."""
    icon_path = 'palisades/gui/icons'
    local_icon_path = os.path.join(os.path.dirname(__file__), 'gui', 'icons')
    icons = map(os.path.abspath, glob.glob(local_icon_path + '/*'))
    return [(icon_path, icons)]

