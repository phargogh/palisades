# -*- coding: utf-8 -*-
"""This file contains test cases for classes contained within the module
invest_natcap.iui.palisades.validation."""

import unittest
import os
import platform
import shutil
import tempfile

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


class GDALCheckerTester(CheckerTester):
    """Test the class iui_validate.GDALChecker"""
    def setUp(self):
        self.validate_as = {'type': 'GDAL',
                            'value': os.path.join(VALIDATION_DATA, 'lulc_samp_cur')}
        self.checker = validation.GDALChecker()

    def test_opens(self):
        """Assert that GDALChecker can open a file."""
        self.assertNoError()

    def test_not_exists(self):
        """Assert that GDALChecker fails if given a bad URI"""
        self.validate_as['value'] += 'aaa'
        self.assertError()

class UnicodeGDALCheckerTester(GDALCheckerTester):
    def setUp(self):
        self.unicode_dir = u'folder_тамквюам'
        self.validate_as = {
            'type': 'GDAL',
            'value': os.path.join(self.unicode_dir, 'lulc_samp_cur'),
        }
        self.checker = validation.GDALChecker()

        # copy the whole validation data dir to the new folder for this suite
        # of tests.
        if os.path.exists(self.unicode_dir):
            shutil.rmtree(self.unicode_dir)
        shutil.copytree(unicode(VALIDATION_DATA, 'utf-8'), self.unicode_dir)

    def tearDown(self):
        shutil.rmtree(self.unicode_dir)

class OGRCheckerTester(CheckerTester):
    """Test the class palisades.validation.OGRChecker"""
    def setUp(self):
        self.validate_as = {'type':'OGR',
                            'value': os.path.join(VALIDATION_DATA, 'AOI_WCVI')}
        self.checker = validation.OGRChecker()

    def test_file_layers(self):
        """Assert tha OGRChecker can validate layer restrictions."""
        layer = {'name': {'inheritFrom': 'file'}}
        self.validate_as['layers'] = [layer]

        incremental_additions = [('name', {'inheritFrom': 'file'}),
                                 ('type', 'polygons'),
                                 ('projection', 'Transverse_Mercator'),
                                 ('datum', 'WGS_1984')]

        for key, value in incremental_additions:
            self.validate_as['layers'][0][key] = value
            self.assertNoError()

    def test_fields_exist(self):
        """Assert that OGRChecker can validate that fields exist."""
        updates = {'layers': [{'name': 'harv_samp_cur'}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur'),
                   'fieldsExist': [
                       {'field': {'pattern': 'start_date',
                                  'flag': 'ignoreCase'}},
                       {'field': {'pattern': 'Cut_cur',
                                  'flag': 'ignoreCase'}},
                       {'field': {'pattern': 'BCEF_cur',
                                  'flag': 'ignoreCase'}}]
                  }
        self.validate_as.update(updates)
        self.assertNoError()

        self.validate_as['fieldsExist'].append('nonexistent_field')
        self.assertError()

        self.validate_as['fieldsExist'] = ['StArT_dAtE', 'Cut_cur']
        self.assertNoError()


    def test_projection(self):
        """Assert that OGRChecker can validate projection units."""
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'units': 'meters'}}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur')}
        self.validate_as.update(updates)
        self.assertNoError()

        # Verify that if the JSON definition requires a projection that we don't
        # recognize in validation's known_units dictionary.
        updates = {'layers': [{'name': 'mn',
                               'projection': {'units': 'SOMETHING!'}}],
                   'value': os.path.join(VALIDATION_DATA, 'mn')}
        self.validate_as.update(updates)
        self.assertError()

    def test_is_projected(self):
        """Assert that OGRChecker can validate the projection."""
        # Check that the layer is projected.
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'exists': True}}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur')}
        self.validate_as.update(updates)
        self.assertNoError()

        # Check that the layer is projected (should fail)
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'exists': False}}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur.shp')}
        self.validate_as.update(updates)
        self.assertError()

        # Check that the layer is projected
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'name': 'Transverse_Mercator'}}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur')}
        self.validate_as.update(updates)
        self.assertNoError()

        # Check that the layer is projected (should fail)
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'name': 'nonexistent_prj'}}],
                               'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur')}
        self.validate_as.update(updates)
        self.assertError()

        # Check that the layer is projected
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'name': 'Transverse_Mercator'},
                               'datum': 'North_American_Datum_1983'}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur')}
        self.validate_as.update(updates)
        self.assertNoError()

        # Check that the layer is projected (should fail)
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'name': 'Transverse_Mercator'},
                               'datum': 'some_other_datum'}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur')}
        self.validate_as.update(updates)
        self.assertError()

    def test_projection_meters(self):
        """Assert that OGRChecker can validate projection units (meters)."""
        # This should validate that the projection's linear units are in
        # Meters.
        updates = {'layers': [{'name': 'meter_proj',
                               'projection': {'units': 'meters'}}],
                   'value': os.path.join(VALIDATION_DATA, 'meter_proj')}
        self.validate_as.update(updates)
        self.assertNoError()

        # This should validate that the projection's linear units are in
        # Meters (spelled as 'metre').
        updates = {'layers': [{'name': 'Florida_SC_UTM17N',
                               'projection': {'units': 'meters'}}],
                   'value': os.path.join(VALIDATION_DATA,
                       'Florida_SC_UTM17N')}
        self.validate_as.update(updates)
        self.assertNoError()

    def test_projection_latlong(self):
        """Assert that OGRChecker can validate projection units (latlong)."""
        # This should return an error.
        updates = {'layers': [{'name': 'harv_samp_cur',
                               'projection': {'units': 'latLong'}}],
                   'value': os.path.join(VALIDATION_DATA, 'harv_samp_cur.shp')}
        self.validate_as.update(updates)
        self.assertError()

    def test_projection_us_feet(self):
        """Assert that OGRChecker can validate projection units (US Feet)."""
        # This should validate that the projection's linear units are in
        # Degrees.
        updates = {'layers': [{'name': 'mn',
                               'projection': {'units': 'US Feet'}}],
                   'value': os.path.join(VALIDATION_DATA, 'mn')}
        self.validate_as.update(updates)
        self.assertNoError()

class UnicodeOGRCheckerTester(OGRCheckerTester):
    def setUp(self):
        self.unicode_dir = u'folder_тамквюам'
        self.validate_as = {'type':'OGR',
                            'value': os.path.join(self.unicode_dir, 'AOI_WCVI')}
        self.checker = validation.OGRChecker()

        # copy the whole validation data dir to the new folder for this suite
        # of tests.
        if os.path.exists(self.unicode_dir):
            shutil.rmtree(self.unicode_dir)
        shutil.copytree(unicode(VALIDATION_DATA, 'utf-8'), self.unicode_dir)

    def tearDown(self):
        shutil.rmtree(self.unicode_dir)


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
