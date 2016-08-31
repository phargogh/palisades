import sys
import glob
import os
import json
import logging

import palisades.i18n
_ = palisades.i18n.language.ugettext

import natcap.versioner
__version__ = natcap.versioner.get_version('palisades')
LOGGER = logging.getLogger(__name__)


# Layouts, for later reference.
LAYOUT_VERTICAL = 1
LAYOUT_HORIZONTAL = 2
LAYOUT_GRID = 3

# Splash strings.  Making these anonymous functions isn't exactly kosher, but
# it allows me to generate the strings AFTER the language has been set and
# still keep these as module-level attributes.
SPLASH_MSG_CORE_APP = lambda: _('Building core application')
SPLASH_MSG_GUI = lambda: _('Building graphical interface')

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

    if found_json is None:
        raise IOError(
            _(('Configuration file %(json_uri)s could not be found '
                   'in %(possible_paths)s')) % {
                "json_uri": json_uri,
                "possible_paths": possible_paths
            })
    LOGGER.debug('Found json file %s', found_json)
    return found_json

def launch(json_uri, splash_img=None, runner=None, interactive=False):
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
        interactive=False - A boolean.  If True, an interactive python shell
            will be created in the current shell process.

    Returns nothing."""
    from palisades import elements
    import palisades.gui

    dist_language = locate_dist_config()['lang']
    palisades.i18n.language.set(dist_language)

    found_json = locate_config(json_uri)
    gui_app = palisades.gui.get_application()

    if splash_img is not None:
        LOGGER.info(_('Showing splash %s'), splash_img)
        gui_app.show_splash(splash_img)
        gui_app.set_splash_message(SPLASH_MSG_CORE_APP())

    ui = elements.Application(found_json, dist_language)

    if runner is not None:
        LOGGER.info(_('Setting runner class to %s'), runner)
        ui._window.set_runner(runner)

    if splash_img is not None:
        gui_app.set_splash_message(SPLASH_MSG_GUI())

    gui_app.add_window(ui._window)

    LOGGER.info(_('Starting application'))
    gui_app.execute(interactive=interactive)

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
                LOGGER.warning(
                    'File %s exists, but an error was encountered: %s',
                    possible_json_path, str(error))

    # if we can't find the distribution JSON configuration file, make
    # reasonable assumptions about default values and return the dictionary.
    if config is None:
        lang_to_use = palisades.i18n.os_default_lang()
        config = {
            'lang': lang_to_use,
        }
        LOGGER.warning("Defaulting to OS language: %s", lang_to_use)

    return config
