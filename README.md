# cci-sort
Methods for accessing CCI data


## README
This program traverses the CCI FTP server from a given starting folder. Each discovered NetCDF file is stored to a class Experiment as a Child_file class object holding properties read out from the first NetCDF file in the same directory, and the file path.

After having traversed the FTP server, it connects to the CCI-API server and looks for matching experiment names and derives the ID number from that. This ID number is used to upload file descriptions to the correct experiment in the online CCI-API database.

- See run.py for basic usage
- Configuration settings for CCI FTP server and CCI-API server are given in config.py
- The program is expecting a CCI-API server to be running, but can index the remote host without it
- The selected CCI folder in config.py (fire) has a reasonable amount of data sets to test the script. However, the NetCDF files are lacking the interesting details that are abundant in the other experiments' files. 
- After indexing the files, it will have downloaded the first NetCDF file into a local folder, temp_dl. Later runs will use these files to read out information. 
- After indexing, the program will also dump the Experiment class instance which holds the files.
- The CCI-API cannot accept the amount of fields this script now finds. Now, each discovered file will be pushed to the CCI-API as each file must be classified according to the CCI-API's ID system (currently only experiment IDs, as some products are null, even in the NetCDF files).

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




