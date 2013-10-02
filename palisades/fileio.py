import json

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
