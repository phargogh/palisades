import versioning
import sys
import glob
import os
import locale
import json

import palisades.i18n
_ = palisades.i18n.language.ugettext

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

# splash strings
SPLASH_MSG_CORE_APP = _('Building core application')
SPLASH_MSG_GUI = _('Building graphical interface')

def get_py2exe_datafiles():
    """Return a list of tuples of data required for a py2exe installation of
    palisades."""
    icon_path = 'palisades/gui/icons'
    local_icon_path = os.path.join(os.path.dirname(__file__), 'gui', 'icons')
    icons = map(os.path.abspath, glob.glob(local_icon_path + '/*'))
    return [(icon_path, icons)]

def locate_config(expected_uri):
    json_uri = expected_uri
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

    return found_json

def launch(json_uri, splash_img=None, runner=None):
    """Construct a core application instance based on the user-defined
    configuration file and then build a GUI instance off of that core
    application.  Once this latter component has been constructed, call its
    execute() function.

        json_uri - a URI to a palisades JSON configuration file.
        splash_img=None - a URI to a raster graphic to use for a splash image
            while the program is loading.  If None, no splash image will be
            used.
        runner=None - a subclass of execution.PythonRunner class to use to run
            the application.  If None, execution.PythonRunner will be used.

    Returns nothing."""
    from palisades import elements
    import palisades.gui

    found_json = locate_config(json_uri)
    if found_json is None:
        raise IOError(
            _('Configuration file %s could not be found in %s') % (json_uri,
                possible_paths))
    print found_json

    gui_app = palisades.gui.get_application()
    if splash_img is not None:
        print _('Showing splash %s') % splash_img
        gui_app.show_splash(splash_img)
        gui_app.set_splash_message(SPLASH_MSG_CORE_APP)
    ui = elements.Application(found_json, locate_dist_config()['lang'])

    if runner is not None:
        print _('Setting runner class to %s') % runner
        ui._window.set_runner(runner)

    if splash_img is not None:
        gui_app.set_splash_message(SPLASH_MSG_GUI)

    gui_app.add_window(ui._window)

    print _('Starting application')
    gui_app.execute()

def locate_dist_config():
    """Locate the distribution configration.  If the distribution does not have
    a configuration file in a known location, make reasonable assumptions for
    default values and return those.  Returns a dictionary of values:
        lang - the lowercase, 2-character ISO language code.

    This function looks in sys._MEIPASS (if we're in a pyinstaller frozen
    build) and in CWD for a file called dist_config.json.  If no JSON object
    can be decoded from a discovered configuration file, an error is printed
    to stdout and we try the next option.
    """

    # possible places:
    #    - sys._MEIPASS
    #    - CWD
    possible_paths = []
    config_filename = 'dist_config.json'

    if getattr(sys, 'frozen', False):
        dist_config_path = os.path.join(sys._MEIPASS, config_filename)
        possible_paths.append(dist_config_path)

    possible_paths.append(os.path.join(os.getcwd(), config_filename))

    config = None
    for possible_json_path in possible_paths:
        if os.path.exists(possible_json_path):
            try:
                config = json.load(open(possible_json_path))
            except Exception as error:
                print ('File %s exists, but an error was encountered: %s' %
                    (possible_json_path, str(error)))

    # if we can't find the distribution JSON configuration file, make
    # reasonable assumptions about default values and return the dictionary.
    if config is None:
        config = {
            'lang': palisades.i18n.os_default_lang(),
        }

    return config
