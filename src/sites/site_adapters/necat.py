"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__created__ = "2016-02-01"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import logging
import redis

class Adapter(object):
    """
    Provides a connection to the Redis database used to communicate to Console
    """
    def __init__(self, settings):

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("ConsoleConnect::__init__")

        # Passed-in settings
        self.settings = settings

    def get_redis_connection(self):
        """
        Returns a connection to the Redis database
        """
        return redis.Redis(self.settings.SITE_REDIS_IP, self.settings.SITE_REDIS_PORT)

    #
    # Put methods
    #
    def put_distl_params(self, data):
        """
        Place requested data into Redis database
        """
        self.logger.debug("put_distl_params")

        # Open connection
        connection = self.get_redis_connection()

        # Construct data string
        data_string = "_".join((data["basename"].replace("_", "="),
                                str(data["distl_res"]),
                                str(data["distl_labelit_res"]),
                                str(data["distl_overloads"]),
                                str(data["distl_total_spots"]),
                                str(data["distl_good_bragg_spots"]),
                                str(data["distl_spots_in_res"]),
                                str(data["distl_max_signal_strength"]),
                                str(data["distl_mean_int_signal"]),
                                str(data["distl_min_signal_strength"])))

        # Put the data in redis
        pipe = connection.pipeline()
        pipe.set("DISTL_PARMS_SV", data_string).set("DP_REQUESTOR_SV", "").execute()
        del pipe
        self.logger.debug("%s Sent to Console in Distl", data_string)

    def put_crystal_params(self, data):
        """
        Place requested data into Redis database
        """
        self.logger.debug("put_crystal_params")

        # Open connection
        connection = self.get_redis_connection()

        # Construct data string
        data_string = "_".join((data["basename"].replace("_", "="),
                                str(data["labelit_a"]),
                                str(data["labelit_b"]),
                                str(data["labelit_c"]),
                                str(data["labelit_alpha"]),
                                str(data["labelit_beta"]),
                                str(data["labelit_gamma"]),
                                str(data["labelit_spacegroup"])))

        # Put the data in
        pipe = connection.pipeline()
        pipe.set("CRYSTAL_PARMS_SV", data_string).set("CP_REQUESTOR_SV", "").execute()
        del pipe
        self.logger.debug("%s Sent to Console in Crystal", data_string)

    def put_strategy_params(self, data):
        """
        Place requested data into Redis database
        """
        self.logger.debug("put_strategy_params")

        # Open connection
        connection = self.get_redis_connection()

        # Construct data string
        data_string = "_".join((str(data["phi_start"]),
                                str(data["delta_phi"]),
                                str(data["number_images"]),
                                str(data["exposure_time"]),
                                str(data["distance"]),
                                str(data["best_norm_atten"])))

        # Put the data in
        pipe = connection.pipeline()
        pipe.set("BEST_PARMS_SV", data_string).set("CP_REQUESTOR_SV", "").execute()
        del pipe

    def put_stac(self, timestamp="08/30/2010_14:13", omega=3.14, kappa=150.9, phi=26.5, width=90):
        """
        Sets the MK3 minikappa
            timestamp is format 08/26/2010_13:53
            omega
            kappa
            phi
            width (presumably of a collection wedge, but that"s not really what we are doing)
        """
        self.logger.debug("put_stac\n %s omega: %f kappa:%f phi:%f",
            (timestamp, omega, kappa, phi))

        # Open Redis connection
        connection = self.get_redis_connection()

        # Update the date of the setting
        connection.set("STAC_PRED_TS_SV", timestamp)

        # Update the setting
        connection.set("STAC_PRED_SV", "_".join((str(omega), str(kappa), str(phi), str(width))))

    def put_datacollection(self, timestamp="2010/08/30_14:13", omega_start=3.14, delta_omega=1.0, number_images=90, time=1.0, distance=450.0, transmission=7.0, kappa=150.9, phi=26.5):
        """
        Sends strategy information to console - both run information and minikappa settings
            timestamp is format YYYY/MM/DD_HH:MM
            omega_start
            delta_omega
            number_images
            time
            distance
            transmission
            kappa
            phi
        """
        if not kappa:
            kappa = 0.0
        if not phi:
            phi = 0.0

        self.logger.debug("""put_datacollection
        timestamp: %s
        omega_start: %f
        delta_omega: %f
        number_images: %d
        time: %f
        distance: %f
        transmission: %f
        kappa: %f
        phi:%f""", (timestamp, omega_start, delta_omega, number_images, time, distance, transmission, kappa, phi))

        # Open Redis connection
        connection = self.get_redis_connection()

        # Update the date of the setting
        connection.set("BEST_STRAT_TS_SV", timestamp)

        # Update the setting
        connection.set("BEST_STRAT_SV", "_".join((str(omega_start),
                                                  str(delta_omega),
                                                  str(number_images),
                                                  str(time),
                                                  str(distance),
                                                  str(transmission))))

    def put_image_stats(self, result_db, wedges_db):
        """Update Console Redis instance with statistics on an image"""

        self.logger.info("put_image_stats")

        # Open Redis connection
        connection = self.get_redis_connection()

        # Update the date of the setting
        if result_db["labelit_status" == "SUCCESS"]:
            connection.set("ST_CRYSPARAMS_SV", "_".join((result_db.fullname,
                                                         str(result_db.labelit_a),
                                                         str(result_db.labelit_b),
                                                         str(result_db.labelit_c),
                                                         str(result_db.labelit_alpha),
                                                         str(result_db.labelit_beta),
                                                         str(result_db.labelit_gamma))))
        # Update the setting
        wedge = ""
        if result_db["best_norm_status"]:
            # Get the right wedge
            for wedge in wedges_db:
                if wedge["strategy_type"] == "normal":
                    break

            connection.set("ST_STRATEGY_SV", "_".join((result_db.fullname,
                                                       str(wedge["phi_start"]),
                                                       str(wedge["delta_phi"]),
                                                       str(wedge["number_images"]))))

    #
    # Getters for the image info that sometimes goes missing
    #
    def get_image_data_adsc(self):
        """
        Returns a dict of beamline data for storage with the image
        """

        # Get connection to redis
        connection = self.get_redis_connection()

        pipe = connection.pipeline()
        #pipe.get("RING_CUR_SV")
        #pipe.get("RING_MODE_SV")
        pipe.get("ENERGY_SV")
        pipe.get("FLUX_SV")
        #pipe.get("MD2_AP_DIAM_SV")
        #pipe.get("PUCK_SV")
        #pipe.get("SAMP_SV")
        pipe.get("MD2_CENTERING_TABLE_XYZ_SV")
        #pipe.get("MD2_ALL_AXES_SV")
        beam_vals = pipe.execute()
        md2_pos = beam_vals[2].split()
        #md2_angles = beam_vals[8].split()

        return_dict = {"beamline"     : self.beamline,
                       #"ring_current" : float(beam_vals[0]),
                       #"ring_mode"    : beam_vals[1],
                       "energy"       : float(beam_vals[0]),
                       "flux"         : float(beam_vals[1]),
                       #"md2_aperture" : int(beam_vals[4].split()[0]),
                       #"puck"         : beam_vals[5],
                       #"sample"       : beam_vals[6],
                       #"phi"          : float(md2_angles[2]),
                       #"kappa"        : float(md2_angles[1]),
                       "md2_x"        : float(md2_pos[0]),
                       "md2_y"        : float(md2_pos[1]),
                       "md2_z"        : float(md2_pos[2])}

        # Return the data
        return return_dict

    def get_image_data(self):
        """
        Returns a dict of beamline data for storage with the image
        """

        self.logger.debug("get_image_data")

        # Get redis connection
        connection = self.get_redis_connection()
        self.logger.debug("get_image_data - Have redis connection")

        try:
            self.logger.debug("Getting Ring current")
            ring_current = float(connection.get("RING_CUR_SV"))
        except:
            ring_current = 0.0
            self.logger.debug("Ring current exception")

        try:
            self.logger.debug("Getting ring mode")
            ring_mode = str(connection.get("RING_MODE_SV"))
        except:
            ring_mode = ""
            self.logger.debug("Ring mode exception")

        try:
            energy = float(connection.get("ENERGY_SV"))
        except:
            energy = 0.0
            self.logger.debug("Energy exception")

        try:
            flux = float(connection.get("FLUX_SV"))
        except:
            flux = 0.0
            self.logger.debug("Flux exception")

        try:
            self.logger.debug("Getting Aperture")
            md2_aperture = int(connection.get("MD2_AP_DIAM_SV").split()[0])
        except:
            md2_aperture = 0
            self.logger.debug("Aperture exception")

        try:
            puck = str(connection.get("PUCK_SV"))
        except:
            puck = ""
            self.logger.debug("Puck exception")

        try:
            sample = int(connection.get("SAMP_SV"))
        except:
            sample = 0
            self.logger.debug("Sample exception")

        try:
            md2_angles = connection.get("MD2_ALL_AXES_SV").split()
        except:
            beam_vals = [0.0, 0.0, 0.0]
            self.logger.debug("Axes exception")

        try:
            phi = float(md2_angles[2])
        except:
            phi = 0.0
            self.logger.debug("Phi exception")

        try:
            kappa = float(md2_angles[1])
        except:
            kappa = 0.0
            self.logger.debug("Kappa exception")

        try:
            md2_pos = connection.get("MD2_CENTERING_TABLE_XYZ_SV").replace("_", " ").split()
        except:
            md2_pos = [0.0, 0.0, 0.0]
            self.logger.debug("MD2 Position exception")

	    # Scrub out problems with offest
        try:
            self.logger.debug("Getting vertical offset")
            vertical_offset = float(get("SEGMENT_OFFSET_SV"))
        except:
            vertical_offset = 0
            self.logger.debug("Vertical offset exception")

        self.logger.debug("get_image_data - making dict")

        return_dict = {"id"              : self.settings.ID,
                       "ring_current"    : ring_current,
                       "ring_mode"       : ring_mode,
                       "energy"          : energy,
                       "flux"            : flux,
                       "md2_aperture"    : md2_aperture,
                       "puck"            : puck,
                       "sample"          : sample,
                       "phi"             : phi,
                       "kappa"           : kappa,
                       "md2_x"           : float(md2_pos[0]),
                       "md2_y"           : float(md2_pos[1]),
                       "md2_z"           : float(md2_pos[2]),
                       "vertical_offset" : vertical_offset}

        self.logger.debug("%s", return_dict)

        # Return the data
        return return_dict

    def get_atten_thickness(self):
        """
        Returns attenuator thickness in microns as an int
        """

        self.logger.debug("get_atten_thickness")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            # Grab the data we want
            thickness = int(connection.get("ATTEN_SV"))

            # Return the value
            return thickness
        except:
            self.logger.exception("Error in get_atten_thickness")
            return -1

    def get_aperture_diameter(self):
        """
        Returns the aperture diameter
        """

        self.logger.debug("get_aperture_diameter")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            diameter = int(connection.get("MD2_AP_DIAM_SV"))

            #return the value
            return diameter
        except:
            self.logger.exception("Error in get_aperture_diameter")
            return -1

    def get_energy(self):
        """
        Returns the energy in eV as a float
        """
        self.logger.debug("get_energy")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            energy = float(connection.get("ENERGY_SV"))

            #return the value
            return energy
        except:
            self.logger.exception("Error in get_energy")
            return -1

    def get_flux(self):
        """
        Returns the flux in arbitrary units as a float
        """
        self.logger.debug("get_flux")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            flux = float(connection.get("FLUX_SV"))

            #return the value
            return flux
        except:
            self.logger.exception("Error in get_flux")
            return -1

    def get_puck(self):
        """
        Returns the puck A/B/C/D as a string
        """
        self.logger.debug("get_puck")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            puck = connection.get("PUCK_SV")

            #return the value
            return puck
        except:
            self.logger.exception("Error in get_puck")
            return -1

    def get_sample(self):
        return self.get_position()

    def get_position(self):
        """
        Returns the puck position as an int
        """

        self.logger.debug("get_position")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            sample = connection.get("SAMP_SV")

            #return the value
            return sample
        except:
            self.logger.exception("Error in get_position")
            return -1

    def get_ring_current(self):
        """
        Returns the ring mode
        """

        self.logger.debug("get_ring_current")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            current = float(connection.get("RING_CUR_SV"))

            #return the value
            return current
        except:
            self.logger.exception("Error in get_ring_current")
            return -1

    def get_ring_mode(self):
        """
        Returns the ring mode
        """

        self.logger.debug("get_ring_mode")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            mode = connection.get("RING_MODE_SV")

            #return the value
            return mode
        except:
            self.logger.exception("Error in get_ring_mode")
            return -1

    def get_collection_status(self):
        """
        Returns the ADSC status - IDLE COLLECTING ABORTED
        """

        self.logger.debug("get_collection_status")

        try:
            # Connect to redis database
            connection = self.get_redis_connection()
            #Grab the data we want
            status = connection.get("ADSC_SV")

            #return the value
            return status
        except:
            self.logger.exception("Error in get_collection_status")
            return -1
