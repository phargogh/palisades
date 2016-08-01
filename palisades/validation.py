"""This module provides validation functionality for the palisades package.  In a
nutshell, this module will validate a value if given a dictionary that
specifies how the value should be validated."""

import csv
import os
import re
import sys
import time
import threading
import traceback

from osgeo import gdal
from osgeo import ogr

from palisades.utils import Communicator
from palisades.utils import RepeatingTimer

# TODO: make these constants used instead of string conventions
V_PASS = None
V_FAIL = 'fail'
V_ERROR = 'error'


class ValidationError(ValueError):
    """Custom validation error."""
    pass


def check_filepath(path, mustExist=False, permissions='r'):
    if mustExist and not os.path.exists(path):
        raise ValidationError('Not found: %s', path)

    if permissions:
        if not os.path.exists(path):
            path = os.path.dirname(path)

        for letter, mode, descriptor in [
                ('r', os.R_OK, 'read'),
                ('w', os.W_OK, 'write'),
                ('x', os.X_OK, 'execute')]:
            if letter in permissions and not os.access(path, mode):
                raise ValidationError('You must have %s access to %s' %
                                      (descriptor, path))

def check_folder(path, mustExist=False, permissions='r', contains=None):
    check_filepath(path, mustExist, permissions)

    if contains:
        missing_files = []
        for relpath in contains:
            contained_filepath = os.path.join(path, relpath)
            if not os.path.exists(contained_filepath):
                missing_files.append(relpath)

        if missing_files:
            raise ValidationError('Directory %s is missing files: %s',
                                  (path, missing_files))


def check_raster(path):
    check_filepath(path, mustExist=True, permissions='r')

    gdal.PushErrorHandler('CPLQuietErrorHandler')
    dataset = gdal.Open(path)
    if not dataset:
        raise ValidationError('%s is not a GDAL-supported raster')


def check_number(num, gteq=None, greaterThan=None, lteq=None, lessThan=None,
                 pattern=None, flag=None):

    num = float(num)

    if gteq != None and not num >= gteq:
        raise ValidationError('%s must be greater than or equal to %s' %
                              (num, gteq))
    if greaterThan != None and not num > greaterThan:
        raise ValidationError('%s must be greater than %s' % (num, greaterThan))
    if lteq != None and not num <= lteq:
        raise ValidationError('%s must be less than or equal to %s' %
                              (num, lteq))
    if lessThan != None and not num < lessThan:
        raise ValidationError('%s must be less than %s' % (num, lessThan ))

    # Allowed default pattern types:
    #  * Decimal (e.g. 4.333112)
    #  * Scientific (e.g. 4.E-170, 9.442e10)
    if not pattern:
        pattern = (
            r'^\s*'  # preceeding whitespace
            r'(-?[0-9]*(\.[0-9]*)?([eE]-?[0-9]+)?)'
            r'\s*$')  # trailing whitespace

    if not flag:
        flag = None

    check_regexp(str(num), pattern=pattern, flag=flag)


def check_regexp(string, pattern='.*', flag=None):
    # Don't bother accepting  a regexp datastructure ... it's not used in
    # InVEST anyways and is easy enough to just write out.

    known_flags = {
        None: 0,  # Indicates no regex flags
        'ignoreCase': re.IGNORECASE,
        'verbose': re.VERBOSE,
        'debug': re.DEBUG,
        'locale': re.LOCALE,
        'multiline': re.MULTILINE,
        'dotAll': re.DOTALL,
    }

    if type(string) in [int, float]:
        string = str(string)

    matches = re.compile(pattern, known_flags[flag])
    if not matches.match(string):
        raise ValidationError('Value %s not allowed for pattern %s' %
                              (string, pattern))


def check_table_fields(table_fields, expected_fields):
    table_fields_set = set([f.upper() for f in table_fields])
    expected_fields_set = set([f.upper() for f in expected_fields])

    difference = expected_fields_set - table_fields_set
    if difference:
        raise ValidationError('Table is missing fields: %s' % list(difference))


def check_table_restrictions(row_dict, restriction_list):
    for restriction in restriction_list:
        field_details = restriction['field']
        if isinstance(field_details, basestring):
            # Then it's a fieldname
            label = field_details
            if field_details in row_dict:
                matching_fieldnames = [field_details]
            else:
                matching_fieldnames = []
        elif isinstance(field_details, dict):
            # If it's not a string, it's a dict that represents a regular
            # expression that could match many fields.
            label = field_details['pattern']
            regex = re.compile(field_details['pattern'])
            matching_fieldnames = []
            for key in row_dict:
                if type(key) in [int, float]:
                    key = str(key)

                if regex.match(key):
                    matching_fieldnames.append(key)
        else:
            raise Exception('Invalid field configuration: %s', field_details)

        try:
            if restriction['required'] and not matching_fieldnames:
                raise ValidationError('File is missing fields matching %s' %
                                      label)
        except KeyError:
            # field is not required by default, so ignore.
            pass

        for field in matching_fieldnames:
            restriction_type = restriction['validateAs']['type']
            try:
                restriction_params = restriction['validateAs']['allowedValues']
            except KeyError:
                restriction_params = {}

            if restriction_type == 'number':
                check_number(num=row_dict[field], **restriction_params)
            elif restriction_type == 'string':
                check_regexp(string=row_dict[field], **restriction_params)
            else:
                raise Exception('Unsupported restriction type %s' %
                                restriction_type)


def check_csv(path, fieldsExist=None, restrictions=None):
    # Before we actually open up the CSV for use, we need to check it for
    # consistency.  Specifically, all CSV inputs to InVEST must adhere to
    # the following:
    #    - All strings are surrounded by double-quotes
    #    - the CSV is comma-delimited.

    # using csv Sniffer not to see if it's a valid file, but to
    # determine the dialect.  csv.Sniffer requires that whole lines are
    # provided.
    with open(path, 'rbU') as csv_file:
        dialect = csv.Sniffer().sniff(
            '\n'.join(csv_file.readlines(1024)), delimiters=";,")
        csv_file.seek(0)
    opened_file = csv.DictReader(open(path), dialect=dialect)

    if fieldsExist:
        check_table_fields(opened_file.fieldnames, fieldsExist)

    if restrictions:
        for row_dict in opened_file:
            check_table_restrictions(row_dict, restrictions)


def check_vector(path, fieldsExist=None, restrictions=None, layers=None):
    check_filepath(path, mustExist=True, permissions='r')

    vector = ogr.Open(path)
    if not vector:
        raise ValidationError('Not a valid OGR vector: %s' % path)

    vector_fieldnames = [f.GetName() for f in vector.GetLayer().schema]

    if fieldsExist:
        check_table_fields(vector_fieldnames, fieldsExist)

    if restrictions:
        for layer_index, layer in enumerate(vector):
            for feature in layer:
                row_dict = dict((field, feature.GetField(field))
                                for field in vector_fieldnames)
                try:
                    check_table_restrictions(row_dict, restrictions)
                except ValidationError as validation_error:
                    raise ValidationError('Validation error in layer %s: %s' %
                                          (layer_index, validation_error))

    if layers:
        for layer_info in layers:
            layer_name = layer_info['name']
            if isinstance(layer_name, dict):
                # dict here represents {'inheritFrom': 'file'}.  The form is
                # inconsequential, it just means that we use the first layer
                # available.
                layer = vector.GetLayer(0)
                layer_name = layer.GetName()
            else:
                layer = vector.GetLayerByName(layer_name)

            if not layer:
                raise ValidationError('Vector is missing layer %s' %
                                      layer_name)

            reference = layer.GetSpatialRef()
            if 'projection' in layer_info:
                if not reference:
                    raise ValidationError('Could not read spatial reference '
                                          'information from vector')

                if 'units' in layer_info['projection']:
                    linear_units = reference.GetLinearUnitsName().lower()

                    # keys are JSON-understood projection units
                    # values are known projection wkt equivalents
                    known_units = {
                        'meters':  ['meter', 'metre'],
                        'US Feet': ['foot_us']
                    }

                    # NOTE: If the JSON-defined linear unit (the expected unit)
                    # is not in the known_units dictionary, this will
                    # throw a keyError, which causes a validation error to be
                    # printed.
                    required_unit = layer_info['projection']['units']
                    try:
                        expected_units = known_units[required_unit]
                    except:
                        raise ValidationError(
                            'Expected projection units must be '
                            'one of %s, not %s' % (known_units.keys(),
                                                   required_unit))

                    if linear_units not in expected_units:
                        raise ValidationError((
                            'Vector layer %s must be projected '
                            'in %s (one of %s, case-insensitive). \'%s\' '
                            'found.') % (layer_name, required_unit,
                                expected_units, linear_units))

                # Validate whether the layer should be projected
                projection = reference.GetAttrValue('PROJECTION')
                if 'exists' in layer_info['projection']:
                    should_be_projected = layer_info['projection']['exists']
                    if bool(projection) != should_be_projected:
                        if not should_be_projected:
                            negate_string = 'not'
                        else:
                            negate_string = ''
                        raise ValidationError((
                            'Vector layer %s should %s be ' +
                            'projected') % (layer_name, negate_string))

                # Validate whether the layer's projection matches the
                # specified projection
                if 'name' in layer_info['projection']:
                    projection_name = layer_info['projection']['name']
                    if projection != projection_name:
                        raise ValidationError(
                            'Shapefile layer %s must be '
                            'projected as %s' % (layer_name, projection_name))

            if 'datum' in layer_info:
                datum = reference.GetAttrValue('DATUM')
                if datum != layer_info['datum']:
                    raise ValidationError(
                        'Vector layer %s must have the datum %s' % (
                            layer_name, layer_info['datum']))


class Validator(object):
    types = {
        'disabled': lambda x: None,
        'GDAL': check_raster,
        'OGR': check_vector,
        'number': check_number,
        'file': check_filepath,
        'exists': check_filepath,
        'folder': check_folder,
        'CSV': check_csv,
        'string': check_regexp,
    }
    def __init__(self, type_str):
        self.finished = Communicator()
        self.func = self.types[type_str]

    def validate(self, value, config):
        try:
            cp_config = config.copy()
            try:
                del cp_config['type']
            except KeyError:
                pass

            self.func(value, **cp_config)
            error_msg = None
            status = V_PASS
        except ValidationError as e:
            error_msg = str(e)
            status = V_FAIL
        except Exception as e:
            error_msg = str(e)
            status = V_ERROR

        self.finished.emit((error_msg, status))
