from palisades.gui import core

# A mapping of which UI Elements are configured to work with which GUI classes
#REPRESENTATIONS = {
#    elements.Text: core.Text,
#    elements.File: core.File,
#    elements.Group: core.Group,
#}

# app_structure is a list of pointers, or an element in the list can be a nested
# list of pointers.
def build(form_ptr):
    # Create a new GUI Window object
    # Return the new Window object
    app = core.Application()
    app.add_window(form_ptr)
