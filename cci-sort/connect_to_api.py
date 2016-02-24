#
# connect_to_api.py
# First ver: 10/12/2015
#            30/01/2016: Added exam_size, exam_cdf
#            24/02/2016: Checks netCDF file, integrates with CCI-API
# MB Eide -- TechForSpace

import os, os.path
import json
import requests

from exam_netcdf import exam_size, exam_cdf

from config import *

#
# File structure:
#
# class Upload
#   - Connects to the CCI-API and gets IDs for experiment names
#     and uploads files for that experiment ID.
#   - Note especially post_files()
#     where the files of Experiment are attempted transferred to the
#     server, but the server can't accept all the fields for each file yet.
#


class Upload :
    def __init__(self, experiment, server_url=None):
        """ Uploads an experiment to the CCI-DB using
            the API
        """
        self.experiment = experiment
        self.server_url = server_url

        self.has_prepared_out = False

        print self.experiment.files[0].properties.keys()

        if self.server_url is None :
            raise IOError('server_url is not defined')

    def prepare_experiment(self):
        """ Iterates through the files and gathers:
            - Experiments
            - Products
            - Filenames
        """
        
        if not self.has_prepared_out:
            self.experiment.create_overview_list()
        
        self.has_prepared_out = True

    def get_experiment(self):
        """ Get full overview of experiments from server
        """
        if not self.has_prepared_out:
            self.prepare_experiment()

        # The experiments have been assigned IDs that
        # need to be resolved to experiment names

        resp = requests.get(self.server_url + 'experiments/')
        self.experiment.id_names_desc = json.loads(resp.content)

        self.ids_are_known = True

    def post_experiment(self):
        """ POST new experiment to server 
        """
        if not self.has_prepared_out:
            self.prepare_experiment()

        for exp, prod, desc in self.experiment.overview:
            print exp, prod, desc
            dt = json.dumps(\
                    {'name': exp,
                     'desc': desc})
            resp = requests.post(
                    self.server_url + 'experiments/',
                    data=dt,
                    headers={'Content-type':'application/json'})
            print resp

    def post_files(self):
        """ POST files to server.
            Server expects:
                - start_date
                - end_date
                - product_ids
                - experiment_ids
            Available: 
                - experiment
                - product
                - level
                - rate (update rate: hourly, daily, monthly, yearly)
                - date (for observation start)
                - size (file size)
                - path
                - webpath
                - filename
                - geospatial_lat_min
                - geospatial_lat_max
                - geospatial_lon_min
                - geospatial_lon_max
                - geospatial_vertical_min
                - geospatial_vertical_max
                - geospatial_lat_units
                - geospatial_resolution
                - geospatial_lat_resolution
                - geospatial_lon_resolution
                - spatial_resolution
                - time_coverage_resolution
                - sensor
                - platform
                - keywords
                - project
            obtained from NetCDF files and file paths.
        """

        if not self.has_prepared_out:
            self.prepare_experiment()
        if not self.ids_are_known:
            self.get_experiment()


        for f in self.experiment.files:
            # Get experiment and product and resolve these 
            # to the CCI-API given ids

            my_exp  = f.properties['experiment']
            my_prod = f.properties['product']

            for v in self.experiment.id_names_desc['experiments']:
                if v['name'] == my_exp:
                    my_id   = v['id']
                    break

            print my_id
                    
            dt =    {'experiment_ids': my_id,
                     'webpath': f.webpath }
            for key in f.properties.keys():
                dt[key] = f.properties[key]

            dt = json.dumps(dt)
            print dt

            resp = requests.post(
                    self.server_url + 'files/',
                    data=dt,
                    headers={'Content-type':'application/json'})
            print resp


        for exp, prod, desc in self.experiment.overview:
            print exp, prod, desc
            dt = json.dumps(\
                    {'name': exp,
                     'desc': desc})
            resp = requests.post(
                    self.server_url + 'experiments/',
                    data=dt,
                    headers={'Content-type':'application/json'})
            print resp
