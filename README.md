# cci-sort
Methods for accessing CCI data

## create_index.py
See `__name__ == '__main__':` for how the code runs, there are two steps:

1. Check if data dictionary already exists
    - If saved list of NC files exist in a Python dictionary where the *key is the name of the dataset*, it loads it to the memory
    - If it does not exist, the program will connect to the CCI FTP server and search it (based on parameters in the beginning of file) to find NC files in the subfolders
        - The results will be saved to a new JSON file: `CCI.json`.
        - The results are a list of filenames found for that folder
        - The JSON file is a dictionary with one key: **the folder name of the root folder chosen to iterate from** with the file list as value
2. Categorises the long list of file name strings (from the `CCI.json` file)
    - Creates or connects to an SQLite database with filename defined in `CCI_DB_PATH`
    - Checks for parameters in the function `find_info(list of strings, SQLite database connection)`
        - Determines level, instrument, etc, based on Rémi's table
    - Saves the categorised data to the SQLite database
    - NB! It saves but does not check for duplicates yet

You can have a look at the sample database dumps (file ending "`.sqlite`") by uploading the file to [http://sqliteviewer.flowsoft7.com/](http://sqliteviewer.flowsoft7.com/). 

You can also reconstruct the SQLite database by renaming one of the `.json` files to `CCI.json`, then the Python script will add the JSON data to the `CCI.sqlite` database.
