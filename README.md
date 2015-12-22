# cci-sort
Methods for accessing CCI data

## create_index.py
See `__name__ == '__main__':` for how the code runs, there are two steps:

1. Check if data dictionary already exists
    - If saved list of NC files exist in a Python dictionary where the *key is the name of the dataset*
    - If it does not exist, the program will connect to the CCI FTP server and search it (based on parameters in the beginning of file) to find NC files
2. Categorises the long list of file name strings
    - Creates or connects to an SQLite database with filename defined in `CCI_DB_PATH`
    - Checks for parameters in the function `find_info(list of strings, SQLite database connection)`
    - Saves the categorised data to the SQLite database
    - NB! Does not check for duplicates yet

You can have a look at the sample database dumps (file ending "`.sqlite`") by uploading the file to [http://sqliteviewer.flowsoft7.com/](http://sqliteviewer.flowsoft7.com/). 

You can also reconstruct the SQLite database by renaming one of the `.json` files to `CCI.json`, then the Python script will add the JSON data to the `CCI.sqlite` database.
