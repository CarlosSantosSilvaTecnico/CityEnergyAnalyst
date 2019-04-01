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

    from cea.utilities.srtm.srtm import main as srtm
    import PIL
    geo_elevation_data = srtm.get_data(srtm1=True, srtm3=False)
    size = (1000, 1000)
    latitude_interval = (float(lat_min) - .05, float(lat_max) + .05)
    longitude_interval = (float(lon_min) - .05, float(lon_max) + .05)
    max_elevation = 3000
    min_elevation = 0
    image = geo_elevation_data.get_image(size, latitude_interval, longitude_interval, max_elevation, min_elevation)
    # the image s a standard PIL object, you can save or show it:
    image.show()


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
