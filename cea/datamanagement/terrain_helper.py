"""
This script extracts terrain elevation from NASA - SRTM
https://www2.jpl.nasa.gov/srtm/
"""
from __future__ import division
from __future__ import print_function

import os

import elevation

import cea.config
import cea.inputlocator
from cea.datamanagement.streets_helper import calc_bounding_box

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def terrain_elevation_extractor(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    # local variables:
    list_of_bounding_box = config.streets_helper.bbox
    terrain_tiff_out_path = locator.get_terrain()

    # get the bounding box coordinates
    if list_of_bounding_box == []:
        # the list is empty, we then revert to get the bounding box for the district
        assert os.path.exists(
            locator.get_district_geometry()), 'Get district geometry file first or the coordinates of the area where to extract the terrain from in the next format: lon_min, lat_min, lon_max, lat_max: %s'
        print("generating streets from District Geometry")
        bounding_box_district_file = calc_bounding_box(locator.get_district_geometry())
        lon_min = bounding_box_district_file[0]
        lat_min = bounding_box_district_file[1]
        lon_max = bounding_box_district_file[2]
        lat_max = bounding_box_district_file[3]
    elif len(list_of_bounding_box) == 4:
        print("generating streets from your bounding box")
        # the list is not empty, the user has indicated a specific set of coordinates
        lon_min = list_of_bounding_box[0]
        lat_min = list_of_bounding_box[1]
        lon_max = list_of_bounding_box[2]
        lat_max = list_of_bounding_box[3]
    elif len(list_of_bounding_box) != 4:
        raise ValueError(
            "Please indicate the coordinates of the area where to extract the streets from in the next format: lon_min, lat_min, lon_max, lat_max")

    # # add a little bit more of space to avoid clipping
    bounds = (float(lon_min) - .05, float(lat_min) - .05, float(lon_max) + .05, float(lat_max) + .05)
    elevation.clip(bounds=bounds, output=terrain_tiff_out_path, product='SRTM1')
    elevation.clean()

    # import os
    # import json
    # import numpy as np
    #
    # SAMPLES = 3601  # Change this to 3601 for SRTM1
    # HGTDIR = 'hgt'  # All 'hgt' files will be kept here uncompressed
    #
    # def get_elevation(lon, lat):
    #     hgt_file = get_file_name(lon, lat)
    #     if hgt_file:
    #         return read_elevation_from_file(hgt_file, lon, lat)
    #     # Treat it as data void as in SRTM documentation
    #     # if file is absent
    #     return -32768
    #
    # def read_elevation_from_file(hgt_file, lon, lat):
    #     with open(hgt_file, 'rb') as hgt_data:
    #         # HGT is 16bit signed integer(i2) - big endian(>)
    #         elevations = np.fromfile(hgt_data, np.dtype('>i2'), SAMPLES * SAMPLES) \
    #             .reshape((SAMPLES, SAMPLES))
    #
    #         lat_row = int(round((lat - int(lat)) * (SAMPLES - 1), 0))
    #         lon_row = int(round((lon - int(lon)) * (SAMPLES - 1), 0))
    #
    #         return elevations[SAMPLES - 1 - lat_row, lon_row].astype(int)
    #
    # def get_file_name(lon, lat):
    #     """
    #     Returns filename such as N27E086.hgt, concatenated
    #     with HGTDIR where these 'hgt' files are kept
    #     """
    #
    #     if lat >= 0:
    #         ns = 'N'
    #     elif lat < 0:
    #         ns = 'S'
    #
    #     if lon >= 0:
    #         ew = 'E'
    #     elif lon < 0:
    #         ew = 'W'
    #
    #     hgt_file = "%(ns)s%(lat)02d%(ew)s%(lon)03d.hgt" % {'lat': abs(lat), 'lon': abs(lon), 'ns': ns, 'ew': ew}
    #     hgt_file_path = os.path.join(HGTDIR, hgt_file)
    #     if os.path.isfile(hgt_file_path):
    #         return hgt_file_path
    #     else:
    #         return None
    #
    # # Mt. Everest
    # print(get_elevation(86.925278, 27.988056))
    # # Kanchanjunga
    # print(get_elevation(88.146667, 27.7025))



def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    terrain_elevation_extractor(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
