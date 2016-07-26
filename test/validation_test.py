# -*- coding: utf-8 -*-
"""This file contains test cases for classes contained within the module
invest_natcap.iui.palisades.validation."""

import unittest
import os
import shutil
import tempfile
import random

import mock

TEST_DATA = os.path.join(os.path.dirname(__file__), 'data')
VALIDATION_DATA = os.path.join(TEST_DATA, 'validation')
UTF8_STRING = u'тамквюам'


class TestFileValidation(unittest.TestCase):

    """Test fixture for file existence and permissions checking."""

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp(suffix=UTF8_STRING)
        print self.workspace_dir

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
        """Validation (file): verify filepath existence."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)
        validation.check_filepath(filepath, mustExist=True, permissions=None)

    def test_filepath_not_found(self):
        """Validation (file): verify failure when file not found."""
        from palisades import validation

        filepath = os.path.join(self.workspace_dir, 'foo.txt')

        with self.assertRaises(validation.ValidationError):
            validation.check_filepath(filepath, mustExist=True)

    def test_filepath_read_permissions_fails(self):
        """Validation (file): verify failure when read access required, not found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with self.assertRaises(validation.ValidationError):
            with mock.patch('os.access', lambda x, y: False):
                validation.check_filepath(filepath, permissions='r')

    def test_filepath_write_permissions_fails(self):
        """Validation (file): verify failure when write access required, not found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with self.assertRaises(validation.ValidationError):
            with mock.patch('os.access', lambda x, y: False):
                validation.check_filepath(filepath, permissions='w')

    def test_filepath_execute_permissions_fails(self):
        """Validation (file): verify failure when ex. access required, not found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with self.assertRaises(validation.ValidationError):
            with mock.patch('os.access', lambda x, y: False):
                validation.check_filepath(filepath, permissions='x')

    def test_all_permissions_pass(self):
        """Validation (file): verify all permissions required and found."""
        from palisades import validation

        filepath = TestFileValidation.make_file(self.workspace_dir)

        with mock.patch('os.access', lambda x, y: True):
            validation.check_filepath(filepath, permissions='rwx')

    def test_read_permissions_dirname(self):
        """Validation (file): verify read permissions on dirname of a given file."""
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
        """Validation (dir): verify folder can skip file existence checks."""
        from palisades import validation
        validation.check_folder(self.workspace_dir, contains=None)

    def test_folder_contains_files(self):
        """Validation (dir): verify folder can check contained file existence."""
        from palisades import validation

        filename = 'example.txt'
        with open(os.path.join(self.workspace_dir, filename), 'w') as fd:
            fd.write('hello!')

        validation.check_folder(self.workspace_dir, contains=[filename])

    def test_folder_missing_files(self):
        """Validation (dir): verify failure when expected files are missing."""
        from palisades import validation

        with self.assertRaises(validation.ValidationError):
            validation.check_folder(self.workspace_dir,
                                    contains=['missing.txt'])


class TestRasterValidation(unittest.TestCase):

    """Test fixture for GDAL-supported raster validation."""

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp(suffix=UTF8_STRING)

    def tearDown(self):
        """Teardown, overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    def test_bad_filepath(self):
        """Validation (GDAL): verify that a missing file raises an error."""
        from palisades import validation

        bad_filename = os.path.join(self.workspace_dir, 'not_found.tif')

        with self.assertRaises(validation.ValidationError):
            validation.check_raster(bad_filename)

    def test_valid_raster(self):
        """Validation (GDAL): verify that a valid raster checks out."""
        from palisades import validation
        from osgeo import gdal

        raster_filepath = os.path.join(self.workspace_dir, 'raster.tif')

        driver = gdal.GetDriverByName('GTiff')
        driver.Create(raster_filepath, 1, 1, 1, gdal.GDT_Float32)

        validation.check_raster(raster_filepath)

    def test_invalid_raster(self):
        """Validation (GDAL): verify that an invalid raster raises an error."""
        from palisades import validation

        raster_filepath = os.path.join(self.workspace_dir, 'bad_raster.tif')
        with open(raster_filepath, 'w') as bad_raster:
            bad_raster.write('this cannot possibly be a valid raster')

        with self.assertRaises(validation.ValidationError):
            validation.check_raster(raster_filepath)


class TestNumberValidation(unittest.TestCase):

    """Test fixture for numeric validation."""

    def test_string(self):
        """Validation (num): Check a string representation of a number."""
        from palisades import validation
        validation.check_number('123')

    def test_nonnumeric_string(self):
        """Validation (num): Verify failure for a nonnumeric string."""
        from palisades import validation
        with self.assertRaises(ValueError):
            validation.check_number('foo')

    def test_gteq(self):
        """Validation (num): Verify gteq comparison."""
        from palisades import validation
        validation.check_number(1, gteq=0)

    def test_gteq_fails(self):
        """Validation (num): Verify gteq failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, gteq=2)

    def test_gt(self):
        """Validation (num): Verify gt comparison."""
        from palisades import validation
        validation.check_number(1, greaterThan=0)

    def test_gt_fails(self):
        """Validation (num): Verify gt failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, greaterThan=2)

    def test_lteq(self):
        """Validation (num): Verify lteq comparison."""
        from palisades import validation
        validation.check_number(1, lteq=2)

    def test_lteq_fails(self):
        """Validation (num): Verify lteq failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, lteq=0)

    def test_lt(self):
        """Validation (num): Verify gt comparison."""
        from palisades import validation
        validation.check_number(1, lessThan=2)

    def test_lt_fails(self):
        """Validation (num): Verify lt failure."""
        from palisades import validation
        with self.assertRaises(validation.ValidationError):
            validation.check_number(1, lessThan=0)

    def test_matching_pattern(self):
        """Validation (num): Verify numeric regex can be user-defined."""
        from palisades import validation
        validation.check_number(0.555, allowedValues={'pattern': '0.5+'})

    def test_matching_pattern_scientific(self):
        """Validation (num): Verify default regex supports scientific notation."""
        from palisades import validation
        validation.check_number(0.3e10)

    def test_matching_pattern_negative_scientific(self):
        """Validation (num): Verify default regex supports negative sci. notation."""
        from palisades import validation
        validation.check_number(0.3e-10)

    def test_matching_pattern_decimal(self):
        """Validation (num): Verify default regex supports decimal notation."""
        from palisades import validation
        validation.check_number(0.3)

    def test_matching_pattern_int(self):
        """Validation (num): Verify default regex supports int notation."""
        from palisades import validation
        validation.check_number(12345)


class TestTableRestrictions(unittest.TestCase):

    """Test fixture for testing table restrictions."""

    def test_invalid_restriction_config(self):
        """Validation (table): verify vailure on bad restriction type."""
        from palisades import validation

        restrictions = [{'type': 'bad type!'}]
        with self.assertRaises(Exception):
            validation.check_table_restrictions({}, restrictions)

    def test_invalid_field_config(self):
        """Validation (table): verify failure on bad field configuration."""
        from palisades import validation

        restrictions = [123]
        with self.assertRaises(Exception):
            validation.check_table_restrictions({}, restrictions)

    def test_missing_required_fieldnames(self):
        """Validation (table): verify failure on required but missing fieldnames."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'number'},
                         'required': True,
                         'field': 'field_a'}]
        table_row = {'field_b': 'value'}

        with self.assertRaises(validation.ValidationError):
            validation.check_table_restrictions(table_row, restrictions)

    def test_matching_numeric_field_restrictions(self):
        """Validation (table): verify basic numeric field restriction."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'number'}, 'field': 'field_a'}]
        table_row = {'field_a': 1.234}

        validation.check_table_restrictions(table_row, restrictions)

    def test_matching_string_field_restrictions(self):
        """Validation (table): verify basic string field restriction."""
        from palisades import validation

        restrictions = [{'validateAs': {'type': 'string'}, 'field': 'field_a'}]
        table_row = {'field_a': 'hello!'}

        validation.check_table_restrictions(table_row, restrictions)

    def test_fieldname_pattern(self):
        """Validation (table): verify user-defined field pattern matching."""
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
        self.workspace_dir = tempfile.mkdtemp(suffix=UTF8_STRING)

    def tearDown(self):
        """Teardown function overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    def test_missing_file(self):
        """Validation (OGR): Vector can check that the file is missing."""
        from palisades import validation

        filepath = os.path.join(self.workspace_dir, 'missing_file.txt')
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filepath)

    def test_invalid_vector(self):
        """Validation (OGR): OGR cannot open an invalid vector."""
        from palisades import validation

        filepath = os.path.join(self.workspace_dir, 'new_file.txt')
        with open(filepath, 'w') as open_file:
            open_file.write('This should not be valid.')

        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filepath)

    def test_fields_exist(self):
        """Validation (OGR): check that expected fields exist."""
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
        """Validation (OGR): check that using basic restrictions can pass."""
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
        """Validation (OGR): check that using basic restrictions can fail."""
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
                # ESRI Shapefile layer names MUST be ASCII
                layername = str(os.path.splitext(os.path.basename(filepath))[0])
            layer = vector.CreateLayer(layername, srs=srs)
            layer = None

        vector = None

    def test_named_layer_missing(self):
        """Validation (OGR): fail when an expected layer can't be found."""
        from palisades import validation
        from osgeo import ogr

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename, layername=None)

        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=[{'name': 'foo'}])

    def test_inherited_layer(self):
        """Validation (OGR): pass when expected layername is inherited."""
        from palisades import validation
        from osgeo import ogr

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        validation.check_vector(
            filename, layers=[{'name': {'inheritFrom': 'file'}}])

    def test_no_spatial_reference(self):
        """Validation (OGR): fail when vector SRS not found but needed."""
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
        """Validation (OGR): pass when projected units match expected units."""
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
        """Validation (OGR): fail when units do not match expected units."""
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
        """Validation (OGR): verify vector is projected."""
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
        """Validation (OGR): fail when vector is projected but not supposed to be."""
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
        """Validation (OGR): verify vector is unprojected."""
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
        """Validation (OGR): fail when projection name does not match expected."""
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
        """Validation (OGR): fail when datum does not match."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'vector.shp')
        TestVectorValidation.create_simple_vector(filename)

        layer_config = [{
            'name': 'vector',
            'datum': 'D_Uranus_2000'  # like with EPSG 79975
        }]
        with self.assertRaises(validation.ValidationError):
            validation.check_vector(filename, layers=layer_config)


class TestCSVValidation(unittest.TestCase):

    """Test fixture for testing CSV files."""

    def setUp(self):
        """Setup function, overridden from ``unittest.TestCase.setUp``."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Teardown, overridden from ``unittest.TestCase.tearDown``."""
        shutil.rmtree(self.workspace_dir)

    @staticmethod
    def create_sample_csv(filepath):
        """Create a simple sample CSV at the given filepath.

        Parameters:
            filepath (string): The string path to where the file should be
                created on disk.

        Returns:
            ``None``
        """
        with open(filepath, 'w') as open_file:
            open_file.write(
                '"foo", "bar", "baz"\n'
                '1, 2, 3\n'
                '2, "b", "c"\n')

    def test_csv_detect_dialect(self):
        """Validation (CSV): csv dialect detection"""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'test.csv')
        TestCSVValidation.create_sample_csv(filename)
        validation.check_csv(filename)

    def test_csv_fields_exist(self):
        """Validation (CSV): verify we can validate field existence."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'test.csv')
        TestCSVValidation.create_sample_csv(filename)

        expected_fields = ['foo', 'bar', 'baz']

        validation.check_csv(filename, fieldsExist=expected_fields)

    def test_csv_restrictions(self):
        """Validation (CSV): verify we can run table restrictions via CSV."""
        from palisades import validation

        filename = os.path.join(self.workspace_dir, 'test.csv')
        TestCSVValidation.create_sample_csv(filename)

        restrictions = [{
            'field': 'foo',
            'validateAs': {
                'type': 'number',
                'lessThan': 3,
                'gteq': 1,
            }
        }]

        validation.check_csv(filename, restrictions=restrictions)
