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
The CLI Import collects information about your project, KSM Application0, Gateway(s), and PAM Configuration(s), then requires two CSVs:
- A CSV for PAM user records.
- A CSV for PAM resource records.
Consult the _CSV Format_ chapter to find out more about CSV syntax.

After every step, the process will save your progress to a _import_autosave.json_ file. Consult the _JSON Format_ chapter to find out more about this template.  

Before the import into Keeper, you will be able to rerun any of the steps in this process.

### 2. Completed JSON File
If you've completed the _CLI Prompts and CSV Files_ already, or if you created your JSON template by other means, you can use this method to skip to the CLI process using the JSON template.

### 3. Partial JSON File
If you would like to resume from an autosave file, or have a partially completed JSON template, you can use this method to skip to specific steps in the CLI import.

## Capabilities

- Create KSM Application
- Create Gateways
- Generate Gateway One-Time-Tokens or Configuration Files
- Create PAM Configurations
- Link Pam Configurations to Gateways
- Create Nested shared folders and user folders 
- Add shared folders to KSM Application
- Create PAM User records
- Set rotation settings on PAM User records, linking to PAM Configurations or Resources in the project
- Create PAM resource records
- Set connection, rbi, and tunnel settings on PAM resources, linking to PAM Configurations and PAM User records in the project

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
| shared_folder | folder_path       | title  | login  | password | pam_config   | {kwargs*}| _rotation.{kwargs*} |
| ------------- | ----------------- | ------ | ------ | -------- | ------------ | -------- | ------------------- |
| Users         |                   | root   | user01 | pwd01    | $config_name | {value*} | {value*}            |
| Users2        | folder01/folder02 | nested | user02 | pwd02    | $config_name | {value*} | {value*}            |

- The default separator for the `folder_path` column is `/`, however this can be customized in the CLI import.
- Beyond the first 6 columns, `{kwargs*}` are Commander arguments for the `record-add` command. For instance:

| distinguishedName                                  | text.custom_field_name |
| -------------------------------------------------- | ---------------------- | 
| CN=Administrator,CN=Users,DC=keeper,DC=localdomain | custom_field_value     |

- `_rotation{kwargs*}` are Commander arguments for the `pam rotation edit` command. For instance:

| _rotation.resource | _rotation.on-demand |
| ------------------ | ------------------- |
| $resource_name     | _                   |

- Values prefixed with `$` refer to a record within the project
- For Commander flags that don't expect a value, use `_`
- All Commander arguments should use the long form (e.g. `_rotation.on-demand` and not `_rotation.od`)

Required columns for a PAM User with active local rotation:  
| shared_folder | folder_path       | title  | login  | password | pam_config   | _rotation.resource | _rotation.on-demand |
| ------------- | ----------------- | ------ | ------ | -------- | ------------ | ------------------ | ------------------- |
| Users         |                   | root   | user01 | pwd01    | $config_name | $resource_name     | _                   |
