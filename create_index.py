#
# create_index.py
# First ver: 10/12/2015
# MB Eide -- TechForSpace
#
# Connects to ESA Climate Change Initiative public data FTP server
# and creates a dictionary for each dataset holding:
#   - Name
#   - Dates
#   - Data objects for each subfolder
# that can be easily searched and accessed
#

import os.path
import json
import sqlite3
import re

CCI_LS_PATH = 'CCI.json'
CCI_DB_PATH = 'CCI.sqlite'
CCI_USER    = 'anonymous'
CCI_PASS    = 'guest'
CCI_FTP     = 'anon-ftp.ceda.ac.uk'
#CCI_HOME    = '/neodc/esacci/'
#CCI_HOME    = '/neodc/esacci/aerosol/data/AATSR_SU/L3_DAILY/v4.2/2002/'
CCI_HOME    = '/neodc/esacci/fire/data/burned_area/grid/v3.1/2006/'
CCI_DTYPE   = 'nc'
CCI_DB_NAME = 'cci_db'

def find_all_datafiles(host, ftype):
    """ Iterates every underlying directory until it finds data.
        Returns:
            - Full path to data file,
            - Instrument/product
            - Sampling rate (DAILY, 8DAY, MONTHLY, ANNUALLY)
            - Level
            - Date
        FIRST TRY: ASSUME ALL THIS CAN BE RECOVERED FROM FILENAME """

    dir_level = 0               # Root level, exits when returning 
    has_visited = []            # list of folders that are visited
    has_visited_all = False     # when dir_level = 0, we are done
    cntr = 0                    # counting how many levels we've visited
    files = []                  # list of data files found

    while not has_visited_all :
        # Get list of files/directories in current directory
        indx    = host.listdir('.')
        #files   = []
        more_to_see_here = False    # Switched if entering a new folder

        print indx

        # For every item in directory
        for item in indx :
            print 'Current item:', item

            if host.path.isfile(item) :
                if item.split(".")[-1] == ftype \
                and item not in files :
                    # Is correct data type
                    # and is not in list of files already
                    files.append(host.path.abspath(item))
                    print 'appended', item

            elif host.path.isdir(item) \
            and host.path.abspath(item) not in has_visited :
                # The item in the directory is another directory,
                # and it has not been visited before
                print host.path.abspath(item), 'not in has_visited'
                has_visited.append(host.path.abspath(item))
                host.chdir(item)
                cntr      += 1
                dir_level += 1
                print dir_level
                
                # Tell loop that we have entered a new folder
                more_to_see_here = True
                print 'Sending break...'
                break

        if not more_to_see_here :
            # The loop has run out of folders and files in this directory
            print 'Loop has run out of folders!'
            if dir_level != 0 :
                # Could be dealing with data in root folder
                # otherwise we move up one directory
                dir_level -= 1
                print 'Going up one directory...'
                host.chdir(host.pardir)
                print 'Changed to dir:', host.path.abspath(host.getcwd())
                more_to_see_here = True
            print dir_level

        if dir_level == 0 and not more_to_see_here :
            has_visited_all = True


    # Returns list of path to all data files 
    # that were in the subfolders of the directory host was in
    print 'Has visited all?', has_visited_all
    print 'Reached return, end of function...'
    return files

def find_info(list_of_files, sqlite_db_connection, experiment_list=None,
              product_list=None, sensor_list=None):
    """ Connects to SQLite database and reads through list of files,
        categorising each item in the file list by assigning:
            - Experiment (from list)
            - Date and time
            - Level
            - ?
            - Filename/ftp path
        Checks database if the data already exist, and adds if not there """

    c = sqlite_db_connection.cursor()
    entries_to_add = []
    exp_l = experiment_list \
            or [\
            'aerosol',
            'cloud',
            'fire',
            'ghg',
            'glaciers',
            'ice_sheets_greenland',
            'land_cover',
            'ocean_colour',
            'ozone',
            'sea_ice',
            'sea_level',
            'soil_moisture',
            'sst' ]

    prod_l = product_list \
            or [\
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

    sensor_l = sensor_list or \
            ['AVHRR', 'MODIS', 'AATSR', 'MERISAATSR',
             'MERIS',
             'TANSO', 'GOSAT',
             'SCIAMACHY', 'ENVISAT']

    d_level = ['L1', 'L2', 'L3', 'L4']
    d_rate  = ['DAILY', 'MONTHLY', 'YEARLY', 'daily', 'monthly', 'yearly']
    neglect = ['ESACCI', 'neodc', 'data']   # append "noise" here

    #date    = re.compile("((19|20)(\d{2}))(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])")
    date    = re.compile("((19|20)(\d{2}))(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])((\d{2})(\d{2})(\d{2}))?")

    for f in list_of_files:
        print 'hei', f
        # check each entry, categorising it and saving it to database
        f_exp = ''  # Dataset
        f_prd = ''  # Product
        f_lvl = ''  # Level
        f_sns = ''  # Sensor
        f_rte = ''  # rate
        f_dte = ''  # date/time
        f_pth = ''  # path

        if f.startswith('/neodc/esacci/'):
            # The string makes sense, shorten it

            # Path
            f_pth = 'ftp://{0}{1}'.format(CCI_FTP, f)
            print f_pth

            # Shorten
            f = f[14:]

            # Check dataset 
            f_p = f.split("/")
            if f_p[0] in exp_l:
                # Experiment in experiment list
                f_exp = f_p[0]
            else :
                print "Not in experiment list, discarding"
                continue

            # Cross-check with the rest
            # Product
            for pr in prod_l :
                if pr in f :
                    f_prd = pr

            for lvl in d_level :
                if lvl in f :
                    f_lvl = lvl

            for sns in sensor_l :
                if sns in f :
                    f_sns = sns

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

            entries_to_add.append((f_exp, f_prd, f_lvl, f_sns, f_rte, f_dte, f_pth))

        else :
            # Something is not right
            print "Path to NetCDF file makes no sense, printing it:"
            print f

    print 'Execute many, adds to database'
    print len(entries_to_add)

    c.executemany('INSERT INTO {0} VALUES (?,?,?,?,?,?,?)'.format(\
            CCI_DB_NAME), 
            entries_to_add)

    sqlite_db_connection.commit()
    

def connect_sqlite_db(sqlite_db_file):
    """ Returns connection to SQLite database file,
        creates database file if it does not exist. """

    if os.path.exists(sqlite_db_file) :
        conn = sqlite3.connect(sqlite_db_file)
    else :
        # Create it
        conn = sqlite3.connect(sqlite_db_file)

        # Create required fields
        
        print "Creating DB fields"
        c = conn.cursor()
        c.execute('CREATE TABLE {2} ({3} {0}, {4} {0}, {5} {0}, {6} {0}, {7} {0}, {8} {0}, {9} {0})'.format( \
                  'TEXT', 'INTEGER',
                  'cci_db', 
                  'dataset', 'product', 'level', 'sensor', 'rate', 'datetime', 'path'))

        conn.commit()

    return conn


def test_functions():
    """ Test functions """
    print "CONNECT_SQLITE_DB"
    sq_c = connect_sqlite_db("test_db.sql")
    c = sq_c.cursor()
    test_entry = [('aerosol', 'AATSR_SU', 'L2', '', 'DAILY', '2002-10-12 12:22:35', '/cci/p')]
    c.executemany('INSERT INTO cci_db VALUES (?,?,?,?,?,?,?)', test_entry)
    sq_c.commit()

    print "FIND_INFO"
    if os.path.exists(CCI_LS_PATH):
        print 'CCI dictionary exists, loads into memory'
        with open(CCI_LS_PATH, 'r') as cci_db_file:
            cci_db = json.load(cci_db_file)
            print 'CCI dictionary loaded as "cci_db"'
        find_info(cci_db['11']['all_files'], sq_c)
    else :
        find_info(["aerosol/data/AATSR_SU/L3_DAILY/v4.2/2002/11/20021126-ESACCI-L3C_AEROSOL-ALL-AATSR_ENVISAT-SU_DAILY-v4.2.nc", "/neodc/esacci/aerosol/data/AATSR_SU/L3_DAILY/v4.2/2002/11/20021126-ESACCI-L3C_AEROSOL-ALL-AATSR_ENVISAT-SU_DAILY-v4.2.nc"], sq_c)

    


    


if __name__ == '__main__':

    # Step 1:   Check if data dictionary already exists,
    #           else get overview of data from CCI server
    if os.path.exists(CCI_LS_PATH):
        print 'CCI dictionary exists, loads into memory'
        with open(CCI_LS_PATH, 'r') as cci_db_file:
            cci_db = json.load(cci_db_file)
            print 'CCI dictionary loaded as "cci_db"'
    else :
        print 'CCI dictionary not found, will scan FTP server'
        import ftputil

        # Init empty dict
        cci_db = {}
        
        # Connect to host:
        with ftputil.FTPHost(CCI_FTP, CCI_USER, CCI_PASS) as host :
            host.chdir(CCI_HOME)

            # Iterate through each folder on server and
            # create list of data files available for each 
            # data set. 
            cci_dataset = host.path.basename(host.getcwd())
            print 'Connected to host. Current folder:', cci_dataset
            dfiles = find_all_datafiles(host, CCI_DTYPE)
            cci_db[cci_dataset] = dfiles

        print 'Done saving list of CCI data into dict cci_db'
        print 'Saving to file:', CCI_LS_PATH
        with open(CCI_LS_PATH, 'w') as cci_db_file :
            json.dump(cci_db, cci_db_file)
            print 'Saved.'

    ## Step 2:
    ## Analyse and categorise the data
    ## Appends or establishes a SQLite database

    print "CONNECT_SQLITE_DB"
    cci_sql = connect_sqlite_db(CCI_DB_PATH)
    c       = cci_sql.cursor()

    print "FIND_INFO", 'Categorises data from dictionary'
    print "Iterates through each key"
    for key in cci_db:
        print 'Current key:', key
        find_info(cci_db[key], cci_sql)






