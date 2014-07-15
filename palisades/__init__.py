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
    __version__ = versioning.REPO.version
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

def launch(json_uri, splash_img=None):
    """Construct a core application instance based on the user-defined
    configuration file and then build a GUI instance off of that core
    application.  Once this latter component has been constructed, call its
    execute() function.

        json_uri - a URI to a palisades JSON configuration file.
        splash_img=None - a URI to a raster graphic to use for a splash image
            while the program is loading.  If None, no splash image will be
            used.

    Returns nothing."""
    from palisades import elements
    import palisades.gui

    # if the user provided a relative path to the configuration file, it's
    # possible that we're in a frozen environment.  If this is the case, we
    # should check out the possible locations of the file.
    possible_paths = [json_uri]
    if not os.path.isabs(json_uri):
        if getattr(sys, 'frozen', False):
            # running within PyInstaller frozen application
            possible_paths.append(os.path.join(sys._MEIPASS, json_uri))

        # the current directory
        possible_paths.append(os.path.join(os.getcwd(), json_uri))

        # Helpful for PyInstaller --onedir builds
        possible_paths.append(os.path.join(os.path.dirname(sys.executable),
            json_uri))

    found_json = None
    for possible_path in possible_paths:
        if os.path.exists(possible_path):
            found_json = possible_path

    if found_json is None:
        raise IOError('Configuration file %s could not be found in %s',
            possible_paths)
    print found_json

    ui = elements.Application(found_json)
    gui = palisades.gui.build(ui._window)
    gui.execute()
