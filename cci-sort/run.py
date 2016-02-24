#
# run.py
# First ver: 10/12/2015
#            30/01/2016: Added exam_size, exam_cdf
#            24/02/2016: Checks netCDF file, integrates with CCI-API
# MB Eide -- TechForSpace
#

import os, os.path
import cPickle as pickle

from config import *

from search_remote import Experiment, Child_file, Explore
from connect_to_api import Upload
from exam_netcdf import exam_size, exam_cdf

#
# File structures:
#
#
# connect_to_api.py
#
# class Upload
#   - Connects to the CCI-API and gets IDs for experiment names
#     and uploads files for that experiment ID.
#   - Note especially post_files()
#     where the files of Experiment are attempted transferred to the
#     server, but the server can't accept all the fields for each file yet.
#
#
# find_files.py
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
#
# exam_netcdf.py
#
# function exam_size
#   - Downloads header from FTP to get NetCDF file size in bytes 
# function exam_cdf
#   - Downloads full NetCDF file to read out header values
#     such as latitudes, resolution, level, instruments and platform
#


if __name__ == '__main__':

    # Dumps pickled Experiment to file holding list of files
    tmp_dump = 'dump_exp.pickle'

    if not os.path.isfile(tmp_dump):

        # Set up new experiment to hold list of files
        exp = Experiment('test experiment')

        # Iterate through FTP server
        ex1 = Explore(exp)
        ex1.connect_server()
        ex1.add_files()

        with open(tmp_dump, 'w') as f:
            pickle.dump(exp, f)
    else :
        with open(tmp_dump, 'r') as f:
            exp = pickle.load(f)
        

    # Upload to the CCI-API database
    ul  = Upload(exp, server_url=CCI_API_URL)
    ul.post_experiment()
    ul.get_experiment()
    ul.post_files()

    # Tests on the experiment class
    exp.create_experiment_list()
    exp.create_product_list()
    exp.create_overview_list()
    print exp.is_in_files('20061207-ESACCI-L4_FIRE-BA-MERIS-fv03.1.nc')



