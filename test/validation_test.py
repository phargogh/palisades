# -*- coding: utf-8 -*-
"""This file contains test cases for classes contained within the module
invest_natcap.iui.palisades.validation."""

import unittest
import os
import shutil
import tempfile
import random

from palisades import validation
import mock

TEST_DATA = os.path.join(os.path.dirname(__file__), 'data')
VALIDATION_DATA = os.path.join(TEST_DATA, 'validation')


class CheckerTester(unittest.TestCase):
    """This class defines commonly-used methods for checker classes in
    palisades.validation.  Since all of the checker classes have a uniform call
    structure, we can abstract certain logic away from the actual test classes
    into this convenient superclass."""

    def check(self):
        """Call the established checker's run_checks function with
        self.validate_as as input.

        prerequisites:
            * a checker object has been created at self.checker
            * the validation dictionary has been saved at self.validate_as.

        returns a string with length > 0 if an error is found.  None or '' if
        no error is found."""

        return self.checker.run_checks(self.validate_as)

    def assertNoError(self):
        """Call self.check and assert that no error is found with the input
        dictionary.

        returns nothing"""

        error = self.check()
        if error != None:
            self.assertEqual(error, '')

    def assertError(self):
        """Call self.check and assert that an error is found with the input
        dictionary.

        returns nothing"""

        error = self.check()
        self.assertNotEqual(error, '', msg='No error message produced')
        self.assertNotEqual(error, None, msg='No error message produced')

    def assertErrorWithMessage(self, substr):
        """Assert that an error with the given substring is produced.

        This is useful so we can make sure that the error that occurs is the
        one that we expect.

        returns nothing"""
        error = self.check()
        self.assertIn(substr, error)


class TestFileValidation(unittest.TestCase):

    """Test fixture for file existence and permissions checking."""

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Teardown, overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    @staticmethod
    def make_file(workspace):
        """Create a primitive text file within the workspace.

        The file will be created within the workspace and will have the
        filename 'file.txt'.

        Parameters:
            workspace (string): The string path to the workspace.

        Returns:
            The string path to the new file on disk.
        """
        filepath = os.path.join(workspace, 'file.txt')
        with open(filepath, 'w') as open_file:
            open_file.write('hello!')

        return filepath

    def test_filepath_exists(self):
        """Validation: verify filepath existence."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)
        validation.check_filepath(filepath, mustExist=True, permissions=None)

    def test_filepath_not_found(self):
        """Validation: verify failure when file not found."""
        from palisades import validation

        filepath = os.path.join(self.workspace_dir, 'foo.txt')

        with self.assertRaises(validation.ValidationError):
            validation.check_filepath(filepath, mustExist=True)

    def test_filepath_read_permissions_fails(self):
        """Validation: verify failure when read access required, not found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with self.assertRaises(validation.ValidationError):
            with mock.patch('os.access', lambda x, y: False):
                validation.check_filepath(filepath, permissions='r')

    def test_filepath_write_permissions_fails(self):
        """Validation: verify failure when write access required, not found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with self.assertRaises(validation.ValidationError):
            with mock.patch('os.access', lambda x, y: False):
                validation.check_filepath(filepath, permissions='w')

    def test_filepath_execute_permissions_fails(self):
        """Validation: verify failure when ex. access required, not found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with self.assertRaises(validation.ValidationError):
            with mock.patch('os.access', lambda x, y: False):
                validation.check_filepath(filepath, permissions='x')

    def test_all_permissions_pass(self):
        """Validation: verify all permissions required and found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with mock.patch('os.access', lambda x, y: True):
            validation.check_filepath(filepath, permissions='rwx')

    def test_read_permissions_dirname(self):
        """Validation: verify read permissions on dirname of a given file."""
        from palisades import validation

        fake_filepath = os.path.join(self.workspace_dir, 'foo.txt')

        with mock.patch('os.access', lambda x, y: True):
            validation.check_filepath(fake_filepath, permissions='r')


class TestFolderValidation(unittest.TestCase):

    """Test fixture for folder validation.

    While folder validation allows for finer control of existence and
    permissions checking, these capabilities are tested in the file
    existence and permissions fixture, above.
    """

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Teardown, overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    def test_folder_no_contains_requirement(self):
        """Validation: verify folder can skip file existence checks."""
        from palisades import validation
        validation.check_folder(self.workspace_dir, contains=None)

    def test_folder_contains_files(self):
        """Validation: verify folder can check contained file existence."""
        from palisades import validation

        filename = 'example.txt'
        with open(os.path.join(self.workspace_dir, filename), 'w') as fd:
            fd.write('hello!')

        validation.check_folder(self.workspace_dir, contains=[filename])

    def test_folder_missing_files(self):
        """Validation: verify failure when expected files are missing."""
        from palisades import validation

        with self.assertRaises(validation.ValidationError):
            validation.check_folder(self.workspace_dir,
                                    contains=['missing.txt'])


class TestRasterValidation(unittest.TestCase):

    """Test fixture for GDAL-supported raster validation."""

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Teardown, overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    def test_bad_filepath(self):
        """Validation: verify that a missing file raises an error."""
        from palisades import validation

        bad_filename = os.path.join(self.workspace_dir, 'not_found.tif')

        with self.assertRaises(validation.ValidationError):
            validation.check_raster(bad_filename)

    def test_valid_raster(self):
        """Validation: verify that a valid raster checks out."""
        from palisades import validation
        from osgeo import gdal

        raster_filepath = os.path.join(self.workspace_dir, 'raster.tif')

        driver = gdal.GetDriverByName('GTiff')
        driver.Create(raster_filepath, 1, 1, 1, gdal.GDT_Float32)

        validation.check_raster(raster_filepath)

    def test_invalid_raster(self):
        """Validation: verify that an invalid raster raises an error."""
        from palisades import validation

        raster_filepath = os.path.join(self.workspace_dir, 'bad_raster.tif')
        with open(raster_filepath, 'w') as bad_raster:
            bad_raster.write('this cannot possibly be a valid raster')

        with self.assertRaises(validation.ValidationError):
            validation.check_raster(raster_filepath)


class TestNumberValidation(unittest.TestCase):

    """Test fixture for numeric validation."""

    def test_string(self):
        """Validation: Check a string representation of a number."""
        from palisades import validation
        validation.check_number('123')

    def test_nonnumeric_string(self):
        """Validation: Verify failure for a nonnumeric string."""
        from palisades import validation
        with self.assertRaises(ValueError):
            validation.check_number('foo')

    def test_gteq(self):
        """Validation: Verify gteq comparison."""
        from palisades import validation
        validation.check_number(1, gteq=0)

    def test_gteq_fails(self):
        """Validation: Verify gteq failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, gteq=2)

    def test_gt(self):
        """Validation: Verify gt comparison."""
        from palisades import validation
        validation.check_number(1, greaterThan=0)

    def test_gt_fails(self):
        """Validation: Verify gt failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, greaterThan=2)

    def test_lteq(self):
        """Validation: Verify lteq comparison."""
        from palisades import validation
        validation.check_number(1, lteq=2)

    def test_lteq_fails(self):
        """Validation: Verify lteq failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, lteq=0)

    def test_lt(self):
        """Validation: Verify gt comparison."""
        from palisades import validation
        validation.check_number(1, lessThan=2)

    def test_lt_fails(self):
        """Validation: Verify lt failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, lessThan=0)

    def test_matching_pattern(self):
        """Validation: Verify numeric regex can be user-defined."""
        from palisades import validation
        validation.check_number(0.555, allowedValues={'pattern': '0.5+'})

    def test_matching_pattern_scientific(self):
        """Validation: Verify default regex supports scientific notation."""
        from palisades import validation
        validation.check_number(0.3e10)

    def test_matching_pattern_negative_scientific(self):
        """Validation: Verify default regex supports negative sci. notation."""
        from palisades import validation
        validation.check_number(0.3e-10)

    def test_matching_pattern_decimal(self):
        """Validation: Verify default regex supports decimal notation."""
        from palisades import validation
        validation.check_number(0.3)

    def test_matching_pattern_int(self):
        """Validation: Verify default regex supports int notation."""
        from palisades import validation
        validation.check_number(12345)


class TestTableRestrictions(unittest.TestCase):

    """Test fixture for testing table restrictions."""

    def test_invalid_restriction_config(self):
        """Validation: verify vailure on bad restriction type."""
        from palisades import validation

        restrictions = [{'type': 'bad type!'}]
        with self.assertRaises(Exception):
            validation.check_table_restrictions({}, restrictions)

    def test_invalid_field_config(self):
        """Validation: verify failure on bad field configuration."""
        from palisades import validation

        restrictions = [123]
        with self.assertRaises(Exception):
            validation.check_table_restrictions({}, restrictions)

    def test_missing_required_fieldnames(self):
        """Validation: verify failure on required but missing fieldnames."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'number'},
                         'required': True,
                         'field': 'field_a'}]
        table_row = {'field_b': 'value'}

        with self.assertRaises(validation.ValidationError):
            validation.check_table_restrictions(table_row, restrictions)

    def test_matching_numeric_field_restrictions(self):
        """Validation: verify basic numeric field restriction."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'number'}, 'field': 'field_a'}]
        table_row = {'field_a': 1.234}

        validation.check_table_restrictions(table_row, restrictions)

    def test_matching_string_field_restrictions(self):
        """Validation: verify basic string field restriction."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'string'}, 'field': 'field_a'}]
        table_row = {'field_a': 'hello!'}

        validation.check_table_restrictions(table_row, restrictions)

    def test_fieldname_pattern(self):
        """Validation: verify user-defined field pattern matching."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'string'},
                         'field': {'pattern': 'hello+!'}}]
        table_row = {
            'foo': 1,
            'hello!': 2,
            'hellooo!': 3,
        }
        validation.check_table_restrictions(table_row, restrictions)


class TestVectorValidation(unittest.TestCase):

    """Test fixture for OGR validation."""

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Teardown function overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    def test_missing_file(self):
        """Validation: Vector can check that the file is missing."""
        from palisades import validation

        filepath = os.path.join(self.workspace_dir, 'missing_file.txt')
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filepath)

    def test_invalid_vector(self):
        """Validation: OGR cannot open an invalid vector."""
        from palisades import validation

        filepath = os.path.join(self.workspace_dir, 'new_file.txt')
        with open(filepath, 'w') as open_file:
            open_file.write('This should not be valid.')

        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filepath)

    def test_fields_exist(self):
        """Validation: check that expected fields exist."""
        from palisades import validation
        from osgeo import ogr

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        driver = ogr.GetDriverByName('ESRI Shapefile')
        vector = driver.CreateDataSource(filename)
        layer = vector.CreateLayer('vector')

        fieldnames = ['field 1', 'field 2']
        for fieldname in fieldnames:
            field_defn = ogr.FieldDefn(fieldname, ogr.OFTReal)
            layer.CreateField(field_defn)

        layer = None
        vector = None

        validation.check_vector(filename, fieldsExist=fieldnames)

    @staticmethod
    def create_vector_with_fields(filename, fieldnames):
        """Create a primitive vector with one feature and a few fields.

        This static method creates an ESRI shapefile at the target filepath
        with a single point feature in it.  For each fieldname passed in via
        the ``fieldnames`` parameter, a new field of type ``ogr.OFTReal`` will
        be created with a seeded, random value.

        Parameters:
            filename (string): The path to the new file on disk.
            fieldnames (list): A list of string fieldnames to be created.

        Returns: None
        """
        from osgeo import ogr

        driver = ogr.GetDriverByName('ESRI Shapefile')
        vector = driver.CreateDataSource(filename)
        layer = vector.CreateLayer('vector')

        for fieldname in fieldnames:
            field_defn = ogr.FieldDefn(fieldname, ogr.OFTReal)
            layer.CreateField(field_defn)
        layer_defn = layer.GetLayerDefn()

        # Create a single sample feature
        new_feature = ogr.Feature(layer_defn)
        new_geometry = ogr.CreateGeometryFromWkt('POINT (10 10)')
        new_feature.SetGeometry(new_geometry)

        random.seed(1234)
        for field in fieldnames:
            new_feature.SetField(field, round(random.random(), 5))

        layer.CreateFeature(new_feature)

        layer = None
        vector = None

    def test_simple_table_restrictions_pass(self):
        """Validation: check that using basic restrictions can pass."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        fieldnames = ['field 1', 'field 2']
        TestVectorValidation.create_vector_with_fields(filename,
                                                       fieldnames=fieldnames)

        restrictions = [
            {
                'field': 'field 1',
                'required': True,
                'validateAs': {
                    'type': 'number'
                }
            },
            {
                'field': 'field 2',
                'required': True,
                'validateAs': {
                    'type': 'number'
                }
            }
        ]
        validation.check_vector(filename, fieldsExist=fieldnames,
                                restrictions=restrictions)

    def test_simple_table_restrictions_fail(self):
        """Validation: check that using basic restrictions can fail."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        fieldnames = ['field 1', 'field 2']
        TestVectorValidation.create_vector_with_fields(filename,
                                                       fieldnames=fieldnames)

        restrictions = [
            {
                'field': 'field 1',
                'required': True,
                'validateAs': {
                    'type': 'number'
                }
            },
            {
                'field': 'field 3',
                'required': True,
                'validateAs': {
                    'type': 'number'
                }
            }
        ]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, fieldsExist=fieldnames,
                                    restrictions=restrictions)

    @staticmethod
    def create_simple_vector(filepath, epsg_code=3157, layername='auto'):
        """Create a simple ESRI Shapefile without fields or features.

        Parameters:
            filepath (string): The string filepath to the location where the
                vector will be stored on disk.
            epsg_code (int or None): The EPSG code to use to set the
                spatial reference of the created vector.  If ``None``, the
                spatial reference will not be set.
            layername (string or None): The string layername to use.
                If ``auto``, the basename of the filepath (without the
                extension) will be used.  If ``None``, a layer will not be
                created at all.

        Returns:
            ``None``
        """
        from osgeo import ogr, osr

        driver = ogr.GetDriverByName('ESRI Shapefile')
        vector = driver.CreateDataSource(filepath)
        if epsg_code:
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(epsg_code)
        else:
            srs = None

        if layername:
            if layername == 'auto':
                layername = os.path.splitext(os.path.basename(filepath))[0]
            layer = vector.CreateLayer(layername, srs=srs)
            layer = None

        vector = None

    def test_named_layer_missing(self):
        """Validation: fail when an expected layer can't be found."""
        from palisades import validation
        from osgeo import ogr

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename, layername=None)

        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=[{'name': 'foo'}])

    def test_inherited_layer(self):
        """Validation: pass when expected layername is inherited."""
        from palisades import validation
        from osgeo import ogr

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        validation.check_vector(
            filename, layers=[{'name': {'inheritFrom': 'file'}}])

    def test_no_spatial_reference(self):
        """Validation: fail when vector SRS not found but needed."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename, epsg_code=None)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'units': 'meters'
            }
        }]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=layer_config)

    def test_projection_units_meter(self):
        """Validation: pass when projected units match expected units."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'units': 'meters'
            }
        }]
        validation.check_vector(filename, layers=layer_config)

    def test_projection_units_error(self):
        """Validation: fail when units do not match expected units."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'units': 'feet'
            }
        }]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=layer_config)

    def test_projection_exists(self):
        """Validation: verify vector is projected."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'exists': True
            }
        }]
        validation.check_vector(filename, layers=layer_config)

    def test_projection_should_not_exist(self):
        """Validation: fail when vector is projected but not supposed to be."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'exists': False
            }
        }]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=layer_config)

    def test_vector_should_not_be_projected(self):
        """Validation: verify vector is unprojected."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename, epsg_code=4269)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'exists': False
            }
        }]
        validation.check_vector(filename, layers=layer_config)

    def test_vector_projection_name_does_not_match(self):
        """Validation: fail when projection name does not match expected."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'projection': {
                'name': 'Mercator'
            }
        }]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=layer_config)

    def test_vector_datum_does_not_match(self):
        """Validation: fail when datum does not match."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'datum': 'D_Uranus_2000'  # like with EPSG 79975
        }]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=layer_config)


class DBFCheckerTester(CheckerTester):
        """Test the class palisades.validation.DBFChecker"""
        def setUp(self):
            self.validate_as = {'type': 'DBF',
                                'value': os.path.join(VALIDATION_DATA,
                                'harv_samp_cur.dbf'),
                                'fieldsExist': []}
            self.checker = validation.DBFChecker()

        def test_fields_exist(self):
            """Assert that DBFChecker can verify fields exist."""
            self.validate_as['fieldsExist'] = ['BCEF_cur', 'C_den_cur',
                                               'Start_date']
            self.assertNoError()

        def test_nonexistent_fields(self):
            """Assert that DBFChecker fails if a bad fieldname is provided."""
            self.validate_as['fieldsExist'].append('nonexistent_field')
            self.assertError()

        def test_restrictions(self):
            """Assert that DBFchecker can handle per-field restrictions."""
            regexp_int = {'pattern': '[0-9]*'}
            date_regexp = {'pattern': '[0-9]{4}|0'}
            num_restriction = {'field': 'BCEF_cur',
                               'validateAs': {'type': 'number',
                                              'allowedValues': regexp_int}}
            const_restriction = {'field': 'BCEF_cur',
                                 'validateAs': {'type': 'number',
                                                'greaterThan': 0,
                                                'gteq': 1,
                                                'lteq': 2,
                                                'lessThan': 2}}
            field_restriction = {'field': 'C_den_cur',
                                 'validateAs': {'type': 'number',
                                                'lessThan': 'BCEF_cur'}}
            str_restriction = {'field': 'Start_date',
                               'validateAs': {'type': 'string',
                                              'allowedValues': date_regexp}}

            self.validate_as['restrictions'] = [num_restriction,
                                                const_restriction,
                                                str_restriction]
            self.assertNoError()

            self.validate_as['restrictions'] = [field_restriction]
            print self.validate_as
            self.assertNoError()

class UnicodeDBFCheckerTester(DBFCheckerTester):
    """Test the class palisades.validation.DBFChecker"""
    def setUp(self):
        self.unicode_dir = u'folder_тамквюам'
        self.validate_as = {
            'type': 'DBF',
            'value': os.path.join(self.unicode_dir, 'harv_samp_cur.dbf'),
            'fieldsExist': [],
        }
        self.checker = validation.DBFChecker()

        # copy the whole validation data dir to the new folder for this suite
        # of tests.
        if os.path.exists(self.unicode_dir):
            shutil.rmtree(self.unicode_dir)
        shutil.copytree(unicode(VALIDATION_DATA, 'utf-8'), self.unicode_dir)

    def tearDown(self):
        shutil.rmtree(self.unicode_dir)

class CSVCheckerTester(CheckerTester):
        """Test the class palisades.validation.CSVChecker"""
        def setUp(self):
            self.validate_as = {'type': 'CSV',
                                'value': os.path.join(VALIDATION_DATA,
                                'Machine_PelamisParamCSV.csv'),
                                'fieldsExist': []}
            self.checker = validation.CSVChecker()

        def test_fields_exist(self):
            """Assert that CSVChecker can verify fields exist"""
            self.validate_as['fieldsExist'] = ['NAME', 'VALUE', 'NOTE']
            self.assertNoError()

            self.validate_as['fieldsExist'] = [
                {'field': {'pattern': "VALUE", "flag": "ignoreCase"},
                    'required': {'min': 1, 'max': 2}}
            ]
            self.assertNoError()

        def test_fields_exist_case_sensitive(self):
            """Assert that CSVChecker can verify fields exist (case-sens.)"""
            self.validate_as['fieldsExist'] = ['nAmE', 'VALue', 'NoTE']
            self.assertNoError()

        def test_nonexistent_fields(self):
            """Assert that CSVChecker fails fails if given a bad fieldname."""
            self.validate_as['fieldsExist'].append('nonexistent_field')
            self.assertError()

        def test_restrictions(self):
            """Assert that CSVChecker can validate per-field restrictions."""
            regexp_name = {'pattern': '[a-z]+', 'flag': 'ignoreCase'}
            regexp_float = {'pattern': '[0-9]*\\.?[0-9]+'}
            num_restriction = {'field': 'VALUE',
                               'validateAs': {'type': 'number',
                                              'allowedValues': regexp_float}}
            const_restriction = {'field': 'VALUE',
                                 'validateAs': {'type': 'number',
                                                'greaterThan': 0}}
            str_restriction = {'field': 'NAME',
                               'validateAs': {'type': 'string',
                                              'allowedValues': regexp_name}}

            self.validate_as['restrictions'] = [num_restriction,
                                                const_restriction,
                                                str_restriction]
            self.assertNoError()

        def test_regexp_fieldname_restriction(self):
            """Assert that CSVChecker can select fields based on regex."""
            self.validate_as['value'] = os.path.join(VALIDATION_DATA, 'Guild.csv')
            field_restriction = {'field': {'pattern': 'NS_.*', 'flag':
                                           'ignoreCase'}}
            self.validate_as['restrictions'] = [field_restriction]
            self.assertNoError()

        def test_regexp_fieldname_not_exists(self):
            """Assert that CSVChecker fails when selecting a nonexist. field"""
            self.validate_as['value'] = os.path.join(VALIDATION_DATA, 'Guild.csv')
            field_restriction = {'field': {'pattern': 'AA_.*', 'flag':
                                           'ignoreCase'},
                                 'required': True}
            self.validate_as['restrictions'] = [field_restriction]
            self.assertError()

        def test_non_comma_delimiting(self):
            """Assert that CSVChecker fails when a CSV is semicolon-delim."""
            self.validate_as['value'] = os.path.join(VALIDATION_DATA,
                    'semicolon-delimited.csv')
            self.assertNoError()

        def test_guilds_table(self):
            """Assert that CSVChecker works when given the pollination example."""
            self.validate_as = {
                "type": "CSV",
                "fieldsExist": ["SPECIES", "ALPHA", "SPECIES_WEIGHT"],
                "restrictions": [{"field": "ALPHA",
                                 "validateAs": {"type": "number",
                                                "allowedValues": {"pattern": "^\\s*[0-9]*\\.[0-9]*\\s*$"}}
                                },
                                {"field": {"pattern": "NS_.*", "flag": "ignoreCase"},
                                 "validateAs": {
                                     "type": "number",
                                     "allowedValues": {"pattern": "^(1\\.?0*)|(0\\.?0*)$"}}
                                },
                                {"field": {"pattern": "FS_.*", "flag": "ignoreCase"},
                                 "validateAs": {
                                     "type": "number",
                                     "gteq": 0.0,
                                     "lteq": 1.0}
                                },
                                {"field": {"pattern": "crp_.*", "flag": "ignoreCase"},
                                 "validateAs": {
                                     "type": "number",
                                     "allowedValues": {"pattern": "^(1\\.?0*)|(0\\.?0*)$"}}
                                }]}
            self.validate_as['value'] = os.path.join(VALIDATION_DATA, 'Guild_with_crops.csv')
            self.assertNoError()

            self.validate_as['value'] = os.path.join(VALIDATION_DATA, 'Guild_bad_numbers.csv')
            self.assertNoError()

            # Try default numeric validation on the bad guilds file.
            self.validate_as['restrictions'][0]['validateAs'] = {'type': 'number'}
            self.assertNoError()

class UnicodeCSVCheckerTester(CSVCheckerTester):
    """Test the class palisades.validation.CSVChecker"""
    def setUp(self):
        self.unicode_dir = u'folder_тамквюам'
        self.validate_as = {
            'type': 'CSV',
            'value': os.path.join(self.unicode_dir, 'Machine_PelamisParamCSV.csv'),
            'fieldsExist': [],
        }
        self.checker = validation.CSVChecker()

        # copy the whole validation data dir to the new folder for this suite
        # of tests.
        if os.path.exists(self.unicode_dir):
            shutil.rmtree(self.unicode_dir)
        shutil.copytree(unicode(VALIDATION_DATA, 'utf-8'), self.unicode_dir)

    def tearDown(self):
        shutil.rmtree(self.unicode_dir)

class FlexibleTableCheckerTester(CheckerTester):
    """Test the class palisades.validation.FlexibleTableChecker"""
    def setUp(self):
        self.validate_as = {'type': 'table',
                            'fieldsExist': []}
        self.checker = validation.FlexibleTableChecker()

    def setCSVData(self, include_suffix=True):
        # CSV file. There are two copies of the file, one with a '.csv' suffix and one without.
        uri = os.path.join(VALIDATION_DATA, 'Machine_PelamisParam')
        if include_suffix:
            uri += 'CSV.csv'
        self.validate_as['value'] = uri

    def setDBFData(self, include_suffix=True):
        # DBF file. There are two copies of the file, one with the '.dbf' suffix and one without.
        uri = os.path.join(VALIDATION_DATA, 'harv_samp_cur', 'harv_samp_cur')
        if include_suffix:
            uri += '.dbf'
        self.validate_as['value'] = uri

    def setNonTableData(self):
        # A file which is not a valid table format.
        uri = os.path.join(VALIDATION_DATA, 'harv_samp_cur.shp')
        self.validate_as['value'] = uri

    def setBadCSV(self):
        # A file which isn't actually CSV-format, but has the .csv suffix.
        uri = os.path.join(VALIDATION_DATA, 'shp_as_csv.csv')
        self.validate_as['value'] = uri

    def test_csv_fields_exist(self):
        """Assert that FlexibleTableChecker can verify fields exist in a CSV file"""
        self.setCSVData()
        self.validate_as['fieldsExist'] = ['NAME', 'VALUE', 'NOTE']
        self.assertNoError

        self.validate_as['fieldsExist'] = [
            {'field': {'pattern': "VALUE", "flag": "ignoreCase"},
             'required': {'min': 1, 'max': 2}}
            ]
        self.assertNoError()

    def test_csv_nonexistent_fields(self):
        self.setCSVData(False)
        self.validate_as['fieldsExist'] = ['nonexistent_field']
        self.assertErrorWithMessage('Required field')

    def test_csv_no_suffix(self):
        """Assert that FlexibleTableChecker works for CSV files without a .csv suffix"""
        self.setCSVData(False)
        self.validate_as['fieldsExist'] = ['NAME', 'VALUE', 'NOTE']
        self.assertNoError()

        self.validate_as['fieldsExist'] = [
            {'field': {'pattern': "VALUE", "flag": "ignoreCase"},
             'required': {'min': 1, 'max': 2}}
            ]
        self.assertNoError()

    def test_csv_regexp_fieldname_restrictions(self):
        """Assert that FlexibleTableChecker can do field selection based on regexps in a CSV."""
        self.setCSVData(False)
        regexp_name = {'pattern': '[a-z]+', 'flag': 'ignoreCase'}
        regexp_float = {'pattern': '[0-9]*\\.?[0-9]+'}
        num_restriction = {'field': 'VALUE',
                           'validateAs': {'type': 'number',
                                          'allowedValues': regexp_float}}
        const_restriction = {'field': 'VALUE',
                             'validateAs': {'type': 'number',
                                            'greaterThan': 0}}
        str_restriction = {'field': 'NAME',
                           'validateAs': {'type': 'string',
                                          'allowedValues': regexp_name}}

        self.validate_as['restrictions'] = [num_restriction,
                                            const_restriction,
                                            str_restriction]
        self.assertNoError()

    def test_bad_csv(self):
        """Assert that FlexibleTableChecker returns an error for a bad CSV file.

        This file is not a CSV, but its .csv suffix should cause FlexibleTableChecker to treat
        it as one, so it should fail.
        """
        self.setBadCSV()
        self.validate_as['fieldsExist'] = ['blah']
        self.assertError()

    def test_dbf_fields_exist(self):
        """Assert that FlexibleTableChecker can verify fields exist in a DBF file"""
        self.setDBFData()
        self.validate_as['fieldsExist'] = ['BCEF_cur', 'C_den_cur',
                                           'Start_date']
        self.assertNoError()


    def test_dbf_no_suffix(self):
        """Assert that FlexibleTableChecker works for DBF files without a .dbf suffix"""
        self.validate_as['value'] = os.path.join(VALIDATION_DATA,
                'harv_samp_cur', 'harv_samp_cur.dbf')
        self.validate_as['fieldsExist'] = ['BCEF_cur', 'C_den_cur',
                                           'Start_date']
        self.assertNoError()


    def test_dbf_nonexistent_fields(self):
        """Assert that FlexibleTableChecker fails if a bad fieldname is provided in a DBF."""
        self.setDBFData()
        self.validate_as['fieldsExist'].append('nonexistent_field')
        self.assertErrorWithMessage('"nonexistent_field" not found')

    def test_nontable_file(self):
        """Assert that FlexibleTableChecker return an error when passed a non-table file."""
        self.setNonTableData()
        self.assertError()

class PrimitiveCheckerTester(CheckerTester):
    """Test the class palisades.validation.PrimitiveChecker."""
    def setUp(self):
        self.validate_as = {'type': 'string',
                            'allowedValues': {'pattern': '[a-z]+'}}
        self.checker = validation.PrimitiveChecker()

    def test_unicode(self):
        """Assert that PrimitiveChecker can validate a unicode regex."""
        self.validate_as['value'] = unicode('aaaaaakljh')

    def test_value(self):
        """Assert that PrimitiveChecker can validate a regexp."""
        self.validate_as['value'] = 'aaaabasd'
        self.assertNoError()

    def test_value_not_allowed(self):
        """Assert that PrimitiveChecker fails on a non-matching string."""
        self.validate_as['value'] = '12341aasd'
        self.assertError()

    def test_ignore_case_flag(self):
        """Assert that PrimitiveChecker recognizes 'ignoreCase' flag."""
        self.validate_as['value'] = 'AsdAdnS'
        self.validate_as['allowedValues']['flag'] = 'ignoreCase'
        self.assertNoError()

    def test_dot_all_flag(self):
        """Assert that PrimitiveChecker regognizes 'dotAll' flag."""
        self.validate_as['value'] = 'asda\n'
        self.validate_as['allowedValues']['flag'] = 'dotAll'
        self.validate_as['allowedValues']['pattern'] = '[a-z]+.+'
        self.assertNoError()

    def test_list_pattern(self):
        """Assert that PrimitiveChecker uses list pattern like '|'"""
        self.validate_as['value'] = 'a'
        self.validate_as['allowedValues']['pattern'] = ['a', 'b', 'c']
        self.assertNoError()

        # Now check something that should fail
        self.validate_as['value'] = 'aa'
        self.assertError()

    def test_pattern_dictionary(self):
        """Assert that PrimitiveChecker supports dict regexp definitions"""
        self.validate_as['value'] = 'a'
        self.validate_as['allowedValues']['pattern'] = {'join': '|',\
            'sub': '^%s$', 'values': ['a', 'b', 'c']}
        self.assertNoError()

        del self.validate_as['allowedValues']['pattern']['join']
        self.assertNoError()

        del self.validate_as['allowedValues']['pattern']['sub']
        self.assertNoError()

        del self.validate_as['allowedValues']['pattern']['values']
        self.assertNoError()


class NumberCheckerTester(CheckerTester):
    """Test the class palisades.validation.NumberChecker"""
    def setUp(self):
        self.validate_as = {'type':'number',
                            'value': 5}
        self.checker = validation.NumberChecker()

    def test_gt(self):
        """Assert that NumberChecker validates 'greaterThan'"""
        self.validate_as['greaterThan'] = 2
        self.assertNoError()

    def test_lt(self):
        """Assert that NumberChecker validates 'lessThan'"""
        self.validate_as['lessThan'] = 7
        self.assertNoError()

    def test_gteq(self):
        """Assert that NumberChecker validates 'gteq'"""
        self.validate_as['gteq'] = 5
        self.assertNoError()

    def test_lteq(self):
        """Assert that NumberChecker validates 'lteq'"""
        self.validate_as['lteq'] = 5
        self.assertNoError()

    def test_all(self):
        """Assert that NumberChecker validates combinations of flags."""
        self.validate_as['lteq'] = 5
        self.validate_as['lessThan'] = 6
        self.validate_as['gteq'] = 5
        self.validate_as['greaterThan'] = 4
        self.assertNoError()

    def test_default_regex(self):
        """Assert that NumberChecker has proper default validation."""
        self.validate_as['value'] = ' 5 '
        self.assertNoError()

        self.validate_as['value'] = 'aaa5b'
        self.assertError()

        self.validate_as['value'] = ' 5gg'
        self.assertError()

        self.validate_as['value'] = '-3.3'
        self.assertNoError()

        self.validate_as['value'] = '-3.3e10'
        self.assertNoError()

        self.validate_as['value'] = '4.E-70'
        self.assertNoError()
