#
# search_remote.py
# First ver: 10/12/2015
#            30/01/2016: Added exam_size, exam_cdf
#            24/02/2016: Checks netCDF file, integrates with CCI-API
# MB Eide -- TechForSpace

import os, os.path
import json
import re
import ftputil
import requests
import cPickle as pickle

from exam_netcdf import exam_size, exam_cdf

from config import *

#
# File structure:
#
# class Experiment
#   - For an experiment, holding associated files stored as
#     Child_file objects in a list, Experiment.files
#
# class Child_file
#   - Each file found on the server becomes a Child_file object
#     where the properties are stored as a dictionary
#     in Child_file.properties
#
# class Explore
#   - Function that accesses the CCI FTP server and enumerates it from a
#     given folder, see CCI_FTP and CCI_HOME in config.py
#



class Experiment :
    def __init__(self, name) :
        """ Collection of files for a CCI experiment.
            Note that the CCI_* paths define the experiment location
            and not the name passed to the class
        """
        self.name  = name
        self.files = []

        self.has_experiments_list = False
        self.has_product_list    = False
        self.has_fname_list      = False
        self.has_overview_list   = False

    def is_in_files(self, fname):
        """ Checks if file fname is amongst added files
        """

        if not self.has_fname_list :
            self.filenames = set()
            for f in self.files :
                self.filenames.add(f.fname)

            self.has_fname_list = True

        return (fname in self.filenames)


    def create_experiment_list(self):
        """ Iterate throuch each file and see if there
            are different experiments present
        """

        if not self.has_experiments_list :
            self.experiments = set()
            for f in self.files :
                self.experiments.add(f.properties['experiment'])

            self.has_experiments_list = True

        print self.experiments

    def create_product_list(self):
        """ Iterate throuch each file and see if there
            are different products present
        """

        if not self.has_product_list :
            self.products = set()
            for f in self.files :
                self.products.add(f.properties['product'])

            self.has_product_list = True

        print self.products

    def create_overview_list(self):
        """ Iterate through each file and 
            generate tuples of experiment, product and description
        """
        if not self.has_overview_list:
            self.overview = set()
            for f in self.files :
                self.overview.add((f.properties['experiment'],
                                   f.properties['product'],
                                   f.properties['project']))

            self.has_overview_list = True

        print self.overview



class Child_file :
    def __init__(self, path,
                 main_file=None, FTP_PATH=None):
        """ Child file in an experiment 
        """

        self.CCI_FTP = FTP_PATH or CCI_FTP
        self.path = path
        self.webpath = 'ftp://{0}{1}'.format(CCI_FTP, self.path)
        self.fname   = self.path.split('/')[-1]

        self.properties = dict()

        if main_file is not None :
            # Add properties from this file
            self.properties = main_file.properties
        else :
            # Add properties based on file contents
            print 'Examining ', self.webpath
            details = exam_cdf(self.webpath)
            self.properties.update(details)

        # adjust file properties such as date, etc from file name
        self.find_filename_info()

    def find_filename_info(self):
        """ Classifies information based on information held in path
        """
        # Experiments
        exp_l = ['aerosol', 'cloud', 'fire', 'ghg', 'glaciers',
                'ice_sheets_greenland', 'land_cover', 'ocean_colour',
                'ozone', 'sea_ice', 'sea_level', 'soil_moisture', 'sst' ]
        # Products
        prod_l = [\
                'AATSR_SU',     # aerosol
                'ATSR2_SU',
                'MS_UVAI',
                'L3C',          # cloud
                'L3U',
                'burned_area/grid',
                'burned_area/pixel',
                'XCH4_GOS_FP',
                'XCH4_GOS_PR',
                'XCH4_SCI',
                'XCO2_EMMA',
                'XCO2_GOS',
                'XCO2_SCI',
                'geographic',   # ocean_colour
                'sinusoidal',
                'TC_L3_MRG',    # ozone
                'MSLA',         # sea_level
                'ACTIVE',       # soil_moisture
                'PASSIVE',
                'COMBINED',
                'gmpe'          # sst
                ]

        ## Sensors
        #sensor_l = ['AVHRR', 'MODIS', 'AATSR', 'MERISAATSR',
        #         'MERIS',
        #         'TANSO', 'GOSAT',
        #         'SCIAMACHY', 'ENVISAT']

        d_level = ['L1', 'L2', 'L3', 'L4']
        d_rate  = ['DAILY', 'MONTHLY', 'YEARLY',
                   'daily', 'monthly', 'yearly']
        neglect = ['ESACCI', 'neodc', 'data']   # append "noise" here

        date    = re.compile("((19|20)(\d{2}))(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])((\d{2})(\d{2})(\d{2}))?")

        f = self.path[:]
        # check each entry
        f_exp = ''  # Dataset
        f_prd = ''  # Product
        f_lvl = ''  # Level
        #f_sns = ''  # Sensor
        f_rte = ''  # rate
        f_dte = ''  # date/time
        f_pth = ''  # path

        if f.startswith('/neodc/esacci/'):
            # The string makes sense, shorten it

            # Shorten
            f = f[14:]

            # Check dataset 
            f_p = f.split("/")
            if f_p[0] in exp_l:
                # Experiment in experiment list
                f_exp = f_p[0]
            else :
                print "Not in experiment list, discarding"

            # Cross-check with the rest
            # Product
            for pr in prod_l :
                if pr in f :
                    f_prd = pr

            for lvl in d_level :
                if lvl in f :
                    f_lvl = lvl

            #for sns in sensor_l :
            #    if sns in f :
            #        f_sns = sns

            for rate in d_rate :
                if rate in f :
                    f_rte = rate

            # Find date
            dte,    = date.findall(f)
            dte_yr  = dte[0] or '1900'
            dte_mn  = dte[3] or '01'
            dte_dy  = dte[4] or '01'
            dte_hr  = dte[6] or '00'
            dte_mi  = dte[7] or '00'
            dte_sc  = dte[8] or '00'

            f_dte   = '{0}-{1}-{2} {3}:{4}:{5}'.format(
                    dte_yr, dte_mn, dte_dy, dte_hr, dte_mi, dte_sc )

            f_siz   = exam_size(self.webpath)

            # Save to file properties
            outs  = [ f_exp,  f_prd,  f_lvl,  f_rte,
                      f_dte,  f_siz,  f_pth ]

            props = ['experiment', 'product', 'level', 'rate',
                     'date', 'size']

            for out, prop in zip(outs, props):
                self.properties[prop] = out

        else :
            # Something is not right
            print "Path to NetCDF file makes no sense, printing it:"
            print f



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





class Explore :  
    def __init__(self, experiment, ftype=None):
        """ Iterates through each file in the folders for a given 
            Experiment.
            Note that the CCI_* paths define the experiment location
            and not the name passed to Experiment
        """
        
        self.experiment = experiment        # experiment of class Experiment

        self.has_visited_all = False
        self.first_file      = True
        self.more_to_see_here = False       # True when entering folder
        self.current_level = 0
        self.visited_folders = set()
        self.visited_files  = set()
        self.ftype          = ftype or CCI_DTYPE


    def connect_server(self, url=None, user=None, passw=None, homedir=None):
        """ Connects to FTP server
            and changes to working directory specified by homedir 
        """

        url     = url or CCI_FTP
        user    = user or CCI_USER
        passw   = passw or CCI_PASS
        homedir = homedir or CCI_HOME

        self.host = ftputil.FTPHost(url, user, passw)
        self.host.chdir(homedir)
        print self.host.listdir('.')


    def new_file(self, webpath, shortpath, has_mother_file=None):
        """ Add this file to the experiment """
        self.experiment.files.append(\
                Child_file(webpath, has_mother_file))
        self.visited_files.add(shortpath)


    def add_files(self):
        """ Traverse CCI folders and add files to experiment """

        while not self.has_visited_all :
            # Loops as long as there are unexplored files/dirs

            items = self.index_folder()

            for item in items:
                print item

                if self.check_if_file(item) :
                    # The item is a file
                    abs_path = self.host.path.abspath(item)

                    if self.first_file :
                        # First file in folder is downloaded and
                        # will be used to give common properties
                        # to the other files in the folder
                        the_mother_file = \
                                Child_file(abs_path)

                        self.first_file = False

                    # add file in folder with index idx
                    self.new_file(abs_path, item, the_mother_file)

                elif self.check_if_folder_and_not_visited(item) :
                    # An unexplored folder
                    self.go_down(item)

                    # Break item loop so that the new folder is explored
                    break

                else :
                    # All items in items have been checked
                    self.more_to_see_here = False

            if not self.more_to_see_here :
                # The loop has run out of folders and files in this dir
                print 'Loop has run out of folders!'

                if self.current_level != 0 :
                    # Return to parent dir to see if more files exist
                    self.go_up()

                print self.current_level

            if self.current_level == 0 and not self.more_to_see_here :
                # Has returned to top level and no folders remain
                self.has_visited_all = True


    def index_folder(self):
        """ Retrieves list of objects in FTP folder
        """
        indx    = self.host.listdir('.')
        return indx

    def go_down(self, item):
        """ Enters item on FTP server
        """
        print "Going down", item
        self.current_level += 1
        self.more_to_see_here = True
        self.first_file = True

        self.visited_folders.add(self.host.path.abspath(item))

        self.host.chdir(item)

    def go_up(self):
        """ Returns to parent directory on FTP server
        """
        print "Going up"
        self.current_level -= 1
        self.first_file = True
        self.more_to_see_here = True 

        self.host.chdir(self.host.pardir)

    def check_if_file(self, item):
        """ Checks if item is a file
            and that it has not been checked before
        """
        if self.host.path.isfile(item) :
            if item.split(".")[-1] == self.ftype \
            and item not in self.visited_files :
                return True
            else :
                return False

    def check_if_folder_and_not_visited(self, item):
        """ Checks if item is a directory
            and that it has not been checked before
        """
        if self.host.path.isdir(item) \
        and self.host.path.abspath(item) not in self.visited_folders:
            # The item in the directory is another directory,
            # and it has not been visited before
            print self.host.path.abspath(item), 'not in has_visited'
            return True
        else :
            return False
