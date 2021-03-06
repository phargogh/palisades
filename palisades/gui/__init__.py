import os
import sys

# A mapping of which UI Elements are configured to work with which GUI classes
#REPRESENTATIONS = {
#    elements.Text: core.Text,
#    elements.File: core.File,
#    elements.Group: core.Group,
#}

if getattr(sys, 'frozen', False):
    # adapt to running in a PyInstaller executable
    base_dir = os.path.join(sys._MEIPASS, 'palisades', 'gui')
else:
    base_dir = os.path.dirname(__file__)
ICON_DIR = os.path.join(base_dir, 'icons')
_path = lambda icon: os.path.join(ICON_DIR, icon)

ICON_CLOSE = _path('dialog-close.png')
ICON_ERROR_BIG = _path('dialog-error.png')
ICON_BULB_BIG = _path('dialog-information.png')
ICON_ENTER = _path('dialog-ok.png')
ICON_WARN = _path('dialog-warning.png')
ICON_WARN_BIG = _path('dialog-warning-big.png')
ICON_FOLDER = _path('document-open.png')
ICON_UNDO = _path('edit-undo.png')
ICON_INFO = _path('info.png')
ICON_REFRESH = _path('refresh.png')  # TODO: not showing up.
ICON_ERROR = _path('validate-fail.png')
ICON_CHECKMARK = _path('validate-pass.png')
ICON_MINUS = _path('minus-icon.png')

# app_structure is a list of pointers, or an element in the list can be a nested
# list of pointers.
def build(form_ptr):
    from palisades.gui import core

    # Create a new GUI Window object
    # Return the new Window object
    app = core.ApplicationGUI()
    app.add_window(form_ptr)
    return app

def get_application():
    from palisades.gui import core
    return core.ApplicationGUI()
