#
# exam_netcdf.py
# Tools used to check content and size of NetCDF files
# TechForSpace
#


import os, os.path
from netCDF4 import Dataset
import pycurl

def exam_size(filein):
    """ Exams size of NetCDF file.
        Input: FTP address (string)
        Returns FILESIZE in bytes """

    c = pycurl.Curl()
    c.setopt(c.URL, filein)
    c.setopt(c.HEADER, 1)
    c.setopt(c.NOBODY, 1)
    c.perform()
    filesize = c.getinfo(c.CONTENT_LENGTH_DOWNLOAD)

    return filesize


def exam_cdf(filein, dllist=None, errorlog=None):
    """ Opens and exams NetCDF file. 
        Input:  filein: ftp address of file
                dllist: dictionary of downloaded ftp files and location,
                        where each key is a ftp address
        Returns header values:
            - Geospatial latitude:  max, min(, resolution)
            - Geospatial longitude: max, min(, resolution)
            - Geospatial resolution, but could be found for lat/long
            - Geospatial: max, min
            - ...
    """

    # Check if file has been downloaded
    file_downloaded = False
    if dllist :
        if filein in dllist.keys():
            file_downloaded = True
            dlfile = dllist[filein]

    if not file_downloaded :
        # Download file to a temp D/L directory 
        #pid = os.getpid()
        dlfolder0 = 'temp_dl/'
        #dlfolder1 = 'temp_dl/' + str(pid) + '/'
        dlfile   = dlfolder0 + filein.split('/')[-1]
        if not os.path.isdir(dlfolder0):
            os.mkdir(dlfolder0)
            #os.mkdir(dlfolder1)
        #else :
        #    if not os.path.isdir(dlfolder1):
        #        os.mkdir(dlfolder1)

        # One more check
        if not os.path.isfile(dlfile) :

            print 'Downloading', filein
            print exam_size(filein)/1024/1024, 'mb to download'
            with open(dlfile, 'wb') as d:
                c = pycurl.Curl()
                c.setopt(c.URL, filein)
                c.setopt(c.WRITEDATA, d)
                c.perform()
            print 'Download of', filein, 'completed'

        # Check if the file was downloaded
        if not (os.path.isfile(dlfile) and os.path.getsize(dlfile) > 0) :
            raise IOError('Downloaded file {} does not exist/is empty!' \
                    .format(dlfile))

        if dllist :
            # Append downloaded file to dictionary
            dllist[filein] = os.path.abspath(dlfile)


    # Investigate file
    df = Dataset(dlfile, 'r')

    outs = dict()

    # These keys will be saved to database,
    # in addition to those obtained from the filename
    args = ['geospatial_lat_min', 'geospatial_lat_max', 
            'geospatial_lon_min', 'geospatial_lat_max', 
            'geospatial_vertical_min', 'geospatial_vertical_max', 
            'geospatial_lat_units',
            'geospatial_lat_resolution', 'geospatial_lon_resolution', 
            'spatial_resolution', 'time_coverage_resolution', 
            'sensor', 'platform', 'keywords', 'project']
    for a in args:
        try :
            outs[a] = getattr(df, a)
        except AttributeError :
            outs[a] = ''


    return outs

