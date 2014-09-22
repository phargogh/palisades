"""Test that critical pieces of functionality work as expected for the various
InVEST User Interface scripts (once the config files have been converted to
palisades format)"""

import unittest

from palisades import elements
from palisades.i18n import translation
import palisades.gui

class WindEnergyRegressionTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "height": 900,
            "id": "window",
            "label": {
                "en": "Wind Energy"
            },
            "localDocURI": "../documentation/wind_energy.html",
            "modelName": {
                "en": "wind_energy"
            },
            "targetScript": "invest_natcap.wind_energy.wind_energy",
            "width": 800,
            "elements": [
                {
                    "args_id": "workspace_dir",
                    "defaultValue": "../WindEnergy",
                    "helpText": {
                        "en": "Select a folder to be used as your workspace.  If the folder you select does not exist, it will be created for you.<br/><br/>This folder will contain the rasters produced by this model.  <b>If datasets already exist in this folder, they will be overwritten</b>."
                    },
                    "id": "workspace",
                    "label": {
                        "en": "Workspace"
                    },
                    "required": True,
                    "type": "folder",
                    "validateAs": {
                        "type": "folder"
                    }
                },
                {
                    "args_id": "wind_data_uri",
                    "defaultValue": "../WindEnergy/input/ECNA_EEZ_WEBPAR_Aug27_2012.bin",
                    "helpText": {
                        "en": "A binary file that represents the wind input data (Weibull parameters). Please see the User's Guide for a description of how this file was generated."
                    },
                    "id": "wind_data",
                    "label": {
                        "en": "Wind Data Points"
                    },
                    "required": True,
                    "type": "file"
                },
                {
                    "args_id": "aoi_uri",
                    "defaultValue": "../WindEnergy/input/New_England_US_Aoi.shp",
                    "helpText": {
                        "en": "An optional polygon shapefile that defines the area of interest. The AOI must be projected with linear units equal to meters. If the AOI is provided it will clip and project the outputs to that of the AOI. The Distance inputs are dependent on the AOI and will only be accessible if the AOI is selected. If the AOI is selected and the Distance parameters are selected, then the AOI should also cover a portion of the land polygon to calculate distances correctly. An AOI is required for valuation."
                    },
                    "id": "aoi",
                    "label": {
                        "en": "Area Of Interest (AOI)"
                    },
                    "returns": {
                        "ifEmpty": "pass"
                    },
                    "signals": [
                        "enables:land_polygon"
                    ],
                    "type": "file",
                    "validateAs": {
                        "type": "file"
                    }
                },
                {
                    "args_id": "bathymetry_uri",
                    "defaultValue": "../Base_Data/Marine/DEMs/global_dem/hdr.adf",
                    "helpText": {
                        "en": "A raster dataset for the elevation values in meters of the area of interest. The DEM should cover at least the entire span of the area of interest and if no AOI is provided then the default global DEM should be used."
                    },
                    "id": "bathymetry",
                    "label": {
                        "en": "Bathymetry (DEM)"
                    },
                    "required": True,
                    "type": "file",
                    "validateAs": {
                        "type": "file"
                    }
                },
                {
                    "args_id": "land_polygon_uri",
                    "defaultValue": "../Base_Data/Marine/Land/global_polygon.shp",
                    "helpText": {
                        "en": "A polygon shapefile that represents the land and coastline that is of interest. For this input to be selectable the AOI must be selected. The AOI should also cover a portion of this land polygon to properly calculate distances. This coastal polygon, and the area covered by the AOI, form the basis for distance calculations for wind farm electrical transmission. This input is required for masking by distance values and for valuation."
                    },
                    "id": "land_polygon",
                    "label": {
                        "en": "Land Polygon for Distance Calculation"
                    },
                    "returns": {
                        "ifEmpty": "pass"
                    },
                    "signals": [
                        "set_required:aoi",
                        "enables:min_distance",
                        "enables:max_distance"
                    ],
                    "type": "file",
                    "validateAs": {
                        "type": "file"
                    }
                },
                {
                    "args_id": "global_wind_parameters_uri",
                    "defaultValue": "../WindEnergy/input/global_wind_energy_parameters.csv",
                    "helpText": {
                        "en": "A CSV file that holds wind energy model parameters for both the biophysical and valuation modules. These parameters are defaulted to values that are supported and reviewed in the User's Guide. We recommend careful consideration before changing these values and to make a new CSV file so that the default one always remains."
                    },
                    "id": "global_wind_parameters",
                    "label": {
                        "en": "Global Wind Energy Parameters"
                    },
                    "required": True,
                    "type": "file",
                    "validateAs": {
                        "type": "file"
                    }
                },
                {
                    "args_id": "suffix",
                    "defaultValue": "",
                    "helpText": {
                        "en": "A String that will be added to the end of the output file paths."
                    },
                    "id": "results_suffix",
                    "label": {
                        "en": "Results Suffix (optional)"
                    },
                    "required": False,
                    "returns": {
                        "ifEmpty": "pass"
                    },
                    "type": "text"
                },
                {
                    "elements": [
                        {
                            "args_id": "turbine_parameters_uri",
                            "defaultValue": "",
                            "helpText": {
                                "en": "A CSV file that contains parameters corresponding to a specific turbine type. The InVEST package comes with two turbine model options, 3.6 MW and 5.0 MW. You may create a new turbine class (or modifying existing classes) by using the existing file format conventions and filling in your own parameters. It is recommended that you do not overwrite the existing default CSV files."
                            },
                            "id": "turbine_parameters",
                            "label": {
                                "en": "Turbine Type"
                            },
                            "required": True,
                            "type": "file",
                            "validateAs": {
                                "type": "file"
                            }
                        },
                        {
                            "args_id": "number_of_turbines",
                            "defaultValue": "",
                            "helpText": {
                                "en": "An integer value indicating the number of wind turbines per wind farm."
                            },
                            "id": "number_of_machines",
                            "label": {
                                "en": "Number Of Turbines"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "[0-9]+"
                        },
                        {
                            "args_id": "min_depth",
                            "defaultValue": "3",
                            "helpText": {
                                "en": "A floating point value in meters for the minimum depth of the offshore wind farm installation."
                            },
                            "id": "min_depth",
                            "label": {
                                "en": "Minimum Depth for Offshore Wind Farm Installation (m)"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        },
                        {
                            "args_id": "max_depth",
                            "defaultValue": "60",
                            "helpText": {
                                "en": "A floating point value in meters for the maximum depth of the offshore wind farm installation."
                            },
                            "id": "max_depth",
                            "label": {
                                "en": "Maximum Depth for Offshore Wind Farm Installation (m)"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        },
                        {
                            "args_id": "min_distance",
                            "defaultValue": "0",
                            "helpText": {
                                "en": "A floating point value in meters that represents the minimum distance from shore for offshore wind farm installation. Required for valuation."
                            },
                            "id": "min_distance",
                            "label": {
                                "en": "Minimum Distance for Offshore Wind Farm Installation (m)"
                            },
                            "returns": {
                                "ifEmpty": "pass"
                            },
                            "signals": [
                                "set_required:land_polygon"
                            ],
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        },
                        {
                            "args_id": "max_distance",
                            "defaultValue": "200000",
                            "helpText": {
                                "en": "A floating point value in meters that represents the maximum distance from shore for offshore wind farm installation. Required for valuation."
                            },
                            "id": "max_distance",
                            "label": {
                                "en": "Maximum Distance for Offshore Wind Farm Installation (m)"
                            },
                            "returns": {
                                "ifEmpty": "pass"
                            },
                            "signals": [
                                "set_required:land_polygon"
                            ],
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        }
                    ],
                    "id": "turbine_group",
                    "label": {
                        "en": "Turbine Properties"
                    },
                    "type": "container"
                },
                {
                    "args_id": "valuation_container",
                    "collapsible": True,
                    "defaultValue": False,
                    "elements": [
                        {
                            "args_id": "foundation_cost",
                            "defaultValue": "",
                            "helpText": {
                                "en": "A floating point number for the unit cost of the foundation type (in millions of dollars). The cost of a foundation will depend on the type selected, which itself depends on a variety of factors including depth and turbine choice. Please see the User's Guide for guidance on properly selecting this value."
                            },
                            "id": "foundation_cost",
                            "label": {
                                "en": "Cost of the Foundation Type (millions of dollars)"
                            },
                            "required": True,
                            "type": "text",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        },
                        {
                            "args_id": "discount_rate",
                            "defaultValue": "",
                            "helpText": {
                                "en": "The discount rate reflects preferences for immediate benefits over future benefits (e.g., would you rather receive $10 today or $10 five years from now?). Please consult the User's Guide for guidance on selecting this value."
                            },
                            "id": "discount_rate",
                            "label": {
                                "en": "Discount Rate"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        },
                        {
                            "args_id": "grid_points_uri",
                            "defaultValue": "",
                            "helpText": {
                                "en": "An optional CSV file with grid and land points to determine cable distances from. An example:<br/> <table border='1'> <tr> <th>ID</th> <th>TYPE</th> <th>LATI</th> <th>LONG</th> </tr> <tr> <td>1</td> <td>GRID</td> <td>42.957</td> <td>-70.786</td> </tr> <tr> <td>2</td> <td>LAND</td> <td>42.632</td> <td>-71.143</td> </tr> <tr> <td>3</td> <td>LAND</td> <td>41.839</td> <td>-70.394</td> </tr> </table> <br/><br/>Each point location is represented as a single row with columns being <b>ID</b>, <b>TYPE</b>, <b>LATI</b>, and <b>LONG</b>. The <b>LATI</b> and <b>LONG</b> columns indicate the coordinates for the point. The <b>TYPE</b> column relates to whether it is a land or grid point. The <b>ID</b> column is a simple unique integer. The shortest distance between respective points is used for calculations. Please see the User's Guide for more information. "
                            },
                            "id": "grid_points",
                            "label": {
                                "en": "Grid Connection Points"
                            },
                            "required": False,
                            "returns": {
                                "ifEmpty": "pass"
                            },
                            "type": "file",
                            "validateAs": {
                                "type": "file"
                            }
                        },
                        {
                            "args_id": "avg_grid_distance",
                            "defaultValue": "4",
                            "helpText": {
                                "en": "<b>Always required, but NOT used in the model if Grid Points provided</b><br/><br/>A number in kilometres that is only used if grid points are NOT used in valuation. When running valuation using the land polygon to compute distances, the model uses an average distance to the onshore grid from coastal cable landing points instead of specific grid connection points. See the User's Guide for a description of the approach and the method used to calculate the default value."
                            },
                            "id": "avg_grid_dist",
                            "label": {
                                "en": "Average Shore to Grid Distance (km)"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            }
                        },
                        {
                            "args_id": "price_table",
                            "defaultValue": True,
                            "helpText": {
                                "en": "When checked the model will use the social cost of wind energy table provided in the input below. If not checked the price per year will be determined using the price of energy input and the annual rate of change."
                            },
                            "id": "price_table",
                            "label": {
                                "en": "Use Price Table"
                            },
                            "signals": [
                                "enables:wind_schedule",
                                "disables:wind_price",
                                "disables:rate_change"
                            ],
                            "type": "checkbox"
                        },
                        {
                            "args_id": "wind_schedule",
                            "defaultValue": "",
                            "helpText": {
                                "en": "A CSV file that has the price of wind energy per kilowatt hour for each year of the wind farms life. The CSV file should have the following two columns:<br/><br/><b>Year:</b> a set of integers indicating each year for the lifespan of the wind farm. They can be in date form such as : 2010, 2011, 2012... OR simple time step integers such as : 0, 1, 2... <br/><br/><b>Price:</b> a set of floats indicating the price of wind energy per kilowatt hour for a particular year or time step in the wind farms life.<br/><br/>An example:<br/> <table border='1'> <tr><th>Year</th> <th>Price</th></tr><tr><td>0</td><td>.244</td></tr><tr><td>1</td><td>.255</td></tr><tr><td>2</td><td>.270</td></tr><tr><td>3</td><td>.275</td></tr><tr><td>4</td><td>.283</td></tr><tr><td>5</td><td>.290</td></tr></table><br/><br/><b>NOTE:</b> The number of years or time steps listed must match the <b>time</b> parameter in the <b>Global Wind Energy Parameters</b> input file above. In the above example we have 6 years for the lifetime of the farm, year 0 being a construction year and year 5 being the last year."
                            },
                            "id": "wind_schedule",
                            "label": {
                                "en": "Wind Energy Price Table"
                            },
                            "required": True,
                            "type": "file"
                        },
                        {
                            "args_id": "wind_price",
                            "dataType": "float",
                            "defaultValue": "",
                            "helpText": {
                                "en": "The price of energy per kilowatt hour. This is the price that will be used for year or time step 0 and will then be adjusted based on the rate of change percentage from the input below. Please consult the User's Guide for determining this value."
                            },
                            "id": "wind_price",
                            "label": {
                                "en": "Price of Energy per Kilowatt Hour ($/kWh)"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "^[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "^[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            },
                            "width": 70
                        },
                        {
                            "args_id": "rate_change",
                            "dataType": "float",
                            "defaultValue": "0",
                            "helpText": {
                                "en": "The annual rate of change in the price of wind energy. This should be expressed as a decimal percentage. I.e. 0.1 for a 10% annual price change."
                            },
                            "id": "rate_change",
                            "label": {
                                "en": "Annual Rate of Change in Price of Wind Energy"
                            },
                            "required": True,
                            "type": "text",
                            "validText": "[-+]?[0-9]*\\.?[0-9]+$",
                            "validateAs": {
                                "allowedValues": {
                                    "pattern": "[-+]?[0-9]*\\.?[0-9]+$"
                                },
                                "type": "number"
                            },
                            "width": 70
                        }
                    ],
                    "id": "valuation_container",
                    "label": {
                        "en": "Valuation"
                    },
                    "signals": [
                        "set_required:aoi",
                        "set_required:land_polygon",
                        "set_required:min_distance",
                        "set_required:max_distance"
                    ],
                    "type": "container"
                }
            ],
        }
        self.translated_config = translation.translate_config(self.config, 'en')
        self.form = elements.Form(self.translated_config)
        self.gui = palisades.gui.get_application()
        self.gui.add_window(self.form)
        self.form.emit_signals()

    def test_setup(self):
        pass

    def test_aoi_enables_land_polygon(self):
        # The AOI element should be enabled.
        aoi_element = self.form.find_element('aoi')
        aoi_gui = self.gui.find_input('aoi')
        self.assertTrue(aoi_element.is_enabled())
        self.assertTrue(aoi_gui._text_field.is_enabled())  # proxy for input

        # AOI element enables the land_polygon input.  Should be disabled until
        # triggered by the AOI.  Therefore, should start disabled.
        land_poly_element = self.form.find_element('land_polygon')
        land_poly_gui = self.gui.find_input('land_polygon')
        self.assertFalse(land_poly_element.is_enabled())
        self.assertFalse(land_poly_gui._text_field.is_enabled())

