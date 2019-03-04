"""
Building model utility function definitions
"""
import sqlite3
import csv
import os
import glob
import pandas as pd
import pvlib
# Using CoolProp for calculating humid air properties: http://www.coolprop.org/fluid_properties/HumidAir.html
from CoolProp.HumidAirProp import HAPropsSI as humid_air_properties

def create_database(sqlite_path, sql_path, csv_path):
    """
    Create SQLITE database from SQL (schema) file and CSV files
    """
    # Remove old SQLITE database file, if any
    if os.path.isfile(sqlite_path):
        os.remove(sqlite_path)

    # Create SQLITE database (schema) from SQL file
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.executescript(open(sql_path, "r").read())
    conn.commit()

    # Import CSV files into SQLITE database
    conn.text_factory = str  # allows utf-8 data to be stored
    cursor = conn.cursor()
    for file in glob.glob(os.path.join(csv_path, "*.csv")):
        table_name = os.path.splitext(os.path.basename(file))[0]

        with open(file, "r") as file:
            first_row = True
            for row in csv.reader(file):
                if first_row:
                    cursor.execute("delete from {}".format(table_name))
                    insert_sql_query = \
                        "insert into {} VALUES ({})".format(table_name, ", ".join(["?" for column in row]))

                    first_row = False
                else:
                    cursor.execute(insert_sql_query, row)
            conn.commit()
    cursor.close()
    conn.close()


def calculate_irradiation_surfaces(conn, weather_type='singapore_nus', irradiation_model='dirint'):
    """
    - Calculates irradiation for surfaces oriented towards east, south, west & north
    - Operates on the database: Updates according columns in weather_timeseries
    - Takes irradition_horizontal as measured global horizontal irradiation (ghi)
    - Based on pvlib-python toolbox: https://github.com/pvlib/pvlib-python
    """
    # Load weather data
    weather_types = pd.read_sql(
        """
        select * from weather_types 
        where weather_type='{}'
        """.format(weather_type),
        conn
    )
    weather_timeseries = pd.read_sql(
        """
        select * from weather_timeseries 
        where weather_type='{}'
        """.format(weather_type),
        conn
    )
    weather_timeseries.index = pd.to_datetime(weather_timeseries['time'])

    # Set time zone (for solarposition calculation)
    weather_timeseries.index = weather_timeseries.index.tz_localize(weather_types['time_zone'][0])

    # Calculate solarposition (zenith, azimuth)
    solarposition = pvlib.solarposition.get_solarposition(
        time=weather_timeseries.index,
        latitude=weather_types['latitude'][0],
        longitude=weather_types['longitude'][0]
    )

    # Calculate direct normal irradiation (dni) from global horizontal irr. (ghi)
    if irradiation_model == 'disc':
        # ... via DISC model
        irradiation_dni_dhi = pvlib.irradiance.disc(
            ghi=weather_timeseries['irradiation_horizontal'],
            zenith=solarposition['zenith'],
            datetime_or_doy=weather_timeseries.index
        )
    elif irradiation_model == 'erbs':
        # ... via ERBS model
        irradiation_dni_dhi = pvlib.irradiance.erbs(
            ghi=weather_timeseries['irradiation_horizontal'],
            zenith=solarposition['zenith'],
            doy=weather_timeseries.index
        )
    elif irradiation_model == 'dirint':
        # ... via DIRINT model
        irradiation_dni_dhi = pd.DataFrame(pvlib.irradiance.dirint(
            ghi=weather_timeseries['irradiation_horizontal'],
            zenith=solarposition['zenith'],
            times=weather_timeseries.index,
            temp_dew=humid_air_properties(
                'D',
                'T', weather_timeseries['ambient_air_temperature'].values + 273.15,
                'W', weather_timeseries['ambient_air_humidity_ratio'].values,
                'P', 101325
            ) - 273.15  # Use CoolProps toolbox to calculate dew point temperature
        ), index=weather_timeseries.index, columns=['dni'])
        irradiation_dni_dhi.loc[irradiation_dni_dhi['dni'].isna(), 'dni'] = 0  # NaN means no irradiation

    # Calculate diffuse horizontal irradiation (dhi)
    irradiation_dni_dhi['dhi'] = (
            weather_timeseries['irradiation_horizontal']
            - irradiation_dni_dhi['dni']
            * pvlib.tools.cosd(solarposition['zenith'])
    )

    # Define surface orientations
    surface_orientations = pd.DataFrame(
        data=[0, 90, 180, 270],
        index=['north', 'east', 'south', 'west'],
        columns=['surface_azimuth']
    )

    # Calculate irradiation onto each surface
    for index, row in surface_orientations.iterrows():
        irradiation_surface = pvlib.irradiance.total_irrad(
            surface_tilt=90,
            surface_azimuth=row['surface_azimuth'],
            apparent_zenith=solarposition['apparent_zenith'],
            azimuth=solarposition['azimuth'],
            dni=irradiation_dni_dhi['dni'],
            ghi=weather_timeseries['irradiation_horizontal'],
            dhi=irradiation_dni_dhi['dhi'],
            surface_type='urban',
            model='isotropic'
        )
        weather_timeseries.loc[:, 'irradiation_' + index] = irradiation_surface['poa_global']

    # Update weather_timeseries in database
    conn.cursor().execute(
        """
        delete from weather_timeseries 
        where weather_type='{}'
        """.format(weather_type),
    )
    weather_timeseries.to_sql('weather_timeseries', conn, if_exists='append', index=False)

def calculate_sky_temperature(conn, weather_type='singapore_nus'):
    """
    - Calculates sky temperatures from ambient air temperature for tropical weather
    - ambient air temperature is decreased by 11K to get the sky temperature
    """
    # Load weather data
    weather_types = pd.read_sql(
        """
        select * from weather_types 
        where weather_type='{}'
        """.format(weather_type),
        conn
    )
    weather_timeseries = pd.read_sql(
        """
        select * from weather_timeseries 
        where weather_type='{}'
        """.format(weather_type),
        conn
    )
    weather_timeseries.index = pd.to_datetime(weather_timeseries['time'])

    # Get temperature difference between sky and ambient
    temperature_difference = weather_types['temperature_difference_sky_ambient'][0]

    # Calculate sky temperature
    weather_timeseries.loc[:, 'sky_temperature'] = \
        weather_timeseries.loc[:, 'ambient_air_temperature'] - temperature_difference

    # Update weather_timeseries in database
    conn.cursor().execute(
        """
        delete from weather_timeseries 
        where weather_type='{}'
        """.format(weather_type),
    )

    weather_timeseries.to_sql('weather_timeseries', conn, if_exists='append', index=False)
