import json
import codecs
import platform
import ctypes
import os
import datetime

import palisades

def read_config(config_uri):
    """Read in the configuration file and parse out the structure of the target
    user interface.

        config_uri - a URI to a JSON file on disk.

    Returns a python dictionary."""

    config_file = open(config_uri).read()
    return json.loads(config_file)


def get_free_space(folder='/', unit='auto'):
    """Get the free space on the drive/folder marked by folder.  Returns a float
        of unit unit.

        folder - (optional) a string uri to a folder or drive on disk. Defaults
            to '/' ('C:' on Windows')
        unit - (optional) a string, one of ['B', 'MB', 'GB', 'TB', 'auto'].  If
            'auto', the unit returned will be automatically calculated based on
            available space.  Defaults to 'auto'.

        returns a string marking the space free and the selected unit.
        Number is rounded to two decimal places.'"""

    units = {'B': 1024,
             'MB': 1024**2.0,
             'GB': 1024**3.0,
             'TB': 1024**4.0}

    if platform.system() == 'Windows':
        if folder == '/':
            folder = 'C:'

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder),
            None, None, ctypes.pointer(free_bytes))
        free_space = free_bytes.value
    else:
        try:
            space = os.statvfs(folder)
        except OSError:
            # Thrown when folder does not yet exist
            # In this case, we need to take the path to the desired folder and
            # walk backwards along its directory tree until we find the mount
            # point.  This mount point is then used for statvfs.
            abspath = os.path.abspath(folder)
            while not os.path.ismount(abspath):
                abspath = os.path.dirname(abspath)
            space = os.statvfs(abspath)

        # space.f_frsize is the fundamental file system block size
        # space.f_bavail is the num. free blocks available to non-root user
        free_space = (space.f_frsize * space.f_bavail)

    # If antomatic unit detection is preferred, do it.  Otherwise, just get the
    # unit desired from the units dictionary.
    if unit == 'auto':
        units = sorted(units.iteritems(), key=lambda unit: unit[1], reverse=True)
        selected_unit = units[0]
        for unit, multiplier in units:
            free_unit = free_space / multiplier
            if free_unit % 1024 == free_unit:
                selected_unit = (unit, multiplier)
        factor = selected_unit[1]  # get the multiplier
        unit = selected_unit[0]
    else:
        factor = units[unit]

    # Calculate space available in desired units, rounding to 2 places.
    space_avail = round(free_space/factor, 2)

    # Format the return string.
    return str('%s %s' % (space_avail, unit))

def save_model_run(arguments, module, out_file):
    """Save an arguments list and module to a new python file that can be
    executed on its own.

        arguments - a python dictionary of arguments.
        module - the python module path in python package notation (e.g.
            invest_natcap.pollination.pollination)
        out_file - the file to which the output file should be written.  If the
            file exists, it will be overwritten.

    This function returns nothing."""

    # Open the file
    model_script = codecs.open(out_file, 'w', encoding='utf-8')

    def _write(line):
        """Utility function to write a string to the script file along with a
        newline character.

            line - a python string.  Assumed to be a line of text, but should
                not include a trailing newline.

        Returns nothing.  Side effect: writes the line to the model_script file
        object."""
        model_script.write(line + '\n')

    def _empty_lines(num_lines):
        """Utility function to write an arbitrary number of blank lines to the
        model_script file object.

            num_lines - Integer.  The number of empty lines to be written.

        Returns nothing.  Side effect: writes the user-defined number of empty
        lines to the model_script file."""
        for line in range(num_lines):
            _write("")

    def _is_string(string):
        """Utility function to check if an input object is a string.  This is
        done by checking the class of the object.  If it's a unicode or str
        object, it's a string.

            string - a python object to test.

        Returns a boolean indicating whether the input object is a string."""
        if isinstance(string, str) or isinstance(string, unicode):
            return True
        return False

    def _format_string(string):
        """Utility function to format a string to contain all the right
        characters for writing to the output file.  Escapes newline characters
        and adds string quoting based on the type of the input string.

            string - a string to be formatted.

        Returns the formatted string."""
        if isinstance(string, str):
            string = "'%s'" % string.replace('\n', '\\n')
        elif isinstance(string, unicode):
            string = "u'%s'" % string.replace('\n', '\\n')
        return string

    def _print_list(in_list, prefix):
        """Recursive utility function to format a list for printing.

        Returns nothing. Side effect: writes the formatted list object and all
        its contents (also formatted) to the model_script file object."""
        prefix = '   ' + prefix
        for item in sorted(in_list):
            if isinstance(item, list):
                if len(item) == 0:
                    _write('%s[],' % prefix)
                else:
                    _write('%s[' % prefix)
                    _print_list(item, prefix)
                    _write('%s],' % prefix)

            elif isinstance(item, dict):
                if len(item) == 0:
                    _write('%s{},' % prefix)
                else:
                    _write('%s{' % prefix)
                    _print_dict(item, prefix)
                    _write('%s},' % prefix)
            else:
                string = _format_string(item)
                _write('%s%s,' % (prefix, string))

    def _print_dict(in_dict, prefix):
        """Recursive utility function to format a python dictionary for
        printing.

        Returns nothing. Side effect: writes the formatted dictionary object and
        all its contents (also formatted) to the model_script file object."""
        prefix = '    ' + prefix
        for key, value in sorted(in_dict.iteritems(), key=lambda x: x[0]):
            key = _format_string(key)

            if isinstance(value, list):
                if len(value) == 0:
                    _write('%s%s: [],' % (prefix, key))
                else:
                    _write('%s%s: [' % (prefix, key))
                    _print_list(value, prefix)
                    _write('%s],' % prefix)
            elif isinstance(value, dict):
                if len(value) == 0:
                    _write('%s%s: {},' % (prefix, key))
                else:
                    _write('%s%s: {' % (prefix, key))
                    _print_dict(value, prefix)
                    _write('%s},' % prefix)
            else:
                string = _format_string(value)
                _write('%s%s: %s,' % (prefix, key, string))

    def print_args(args, prefix='    ', printHeader=True):
        """Utility function to write a python dictionary to the model_script
        file object."""
        if printHeader:
            _write('args = {')

        _print_dict(args, prefix)

        if printHeader:
            _write('}')

    # Print some auto-generated docstring with some version metadata, etc.
    current_time = datetime.datetime.now()
    metadata = [
        '""""',
        'This is a saved model run from %s.' % module,
        'Generated: %s' % current_time.strftime('%c'),
        'Palisades version: %s' % palisades.__version__,
        '"""'
    ]

    for line in metadata:
        _write(line)

    _empty_lines(1)

    # Enforce that we have at least a certain version of InVEST installed?

    # Print the import statement
    _write('import %s' % module)
    _empty_lines(2)

    # Print the arguements in sorted order.
    print_args(arguments)
    _empty_lines(1)

    # print the line to call the module.
    _write('%s.execute(args)' % module)

    model_script.flush()
    model_script.close()


