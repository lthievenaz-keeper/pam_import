# pam_import
Python script to import complex nested models from CSV to KeeperPAM

## Installation
- Required modules:
```
pip install keepercommander
```
- Optional modules:
```
pip install rich
```
Rich is used for CLI styling, it can be skipped, however ensure the import statements at the head of the file are removed.
## Usage
Run the script:
```
python pam_import.py
```
### 1. CLI Prompts and CSV Files
The CLI Import collects information about your project, app, gateway(s), and PAM config(s), then requires two CSVs:
- A CSV for PAM user records.
- A CSV for PAM resource records.
Consult the _CSV Format_ chapter to find out more about CSV syntax.

After every step, the process will save your progress to a _import_autosave.json_ file. Consult the _JSON Format_ chapter to find out more about this template.  

Before the import into Keeper, you will be able to rerun any of the steps in this process.

### 2. Completed JSON File
If you've completed the _CLI Prompts and CSV Files_ already, or if you created your JSON template by other means, you can use this method to skip to the CLI process using the JSON template.

### 3. Partial JSON File
If you would like to resume from an autosave file, or have a partially completed JSON template, you can use this method to skip to specific steps in the CLI import.

## Limitations  

- Object titles should be unique. This includes:
  - Project name*
  - Application name*
  - Gateway names*
  - PAM Configuration names*
  - Shared Folder names
  - User Folder names
  - Record titles

For items marked with *, the names must be unique across the Keeper Vault. Other items must simply be unique per project.
- The import generates a PAM configuration with all features enabled (that can be enabled with Commander). This can be edited after the import is complete.
- The import shares the user shared folders to your KSM app with can-edit permissions. This can be edited after the import is complete.

## CSV Format
### 1. Users CSV
| shared_folder | folder_path       | title  | login  | password |{kwargs*}| _rotation.{kwargs*} |
| ------------- | ----------------- | ------ | ------ | -------- | ------- | ------------------- |
| Users         |                   | root   | user01 | pwd01    |{value*} | {value*}            |
| Users2        | folder01/folder02 | nested | user02 | pwd02    |{value*} | {value*}            |
