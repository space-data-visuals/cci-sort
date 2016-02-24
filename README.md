# cci-sort
Methods for accessing CCI data


## README

- See run.py for basic usage
- Note that it is expecting a CCI-API server to be running as configured in config.py

## File structures:

### connect_to_api.py

 class Upload
   - Connects to the CCI-API and gets IDs for experiment names
     and uploads files for that experiment ID.
   - Note especially post_files()
     where the files of Experiment are attempted transferred to the
     server, but the server can't accept all the fields for each file yet.


### find_files.py

 class Experiment
   - For an experiment, holding associated files stored as
     Child_file objects in a list, Experiment.files

 class Child_file
   - Each file found on the server becomes a Child_file object
     where the properties are stored as a dictionary
     in Child_file.properties

 class Explore
   - Function that accesses the CCI FTP server and enumerates it from a
     given folder, see CCI_FTP and CCI_HOME in config.py


### exam_netcdf.py

 function exam_size
   - Downloads header from FTP to get NetCDF file size in bytes 
 function exam_cdf
   - Downloads full NetCDF file to read out header values
     such as latitudes, resolution, level, instruments and platform




