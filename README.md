# pam_import
Python script to import complex nested models from CSV to KeeperPAM.  

⚠️ - CSVs and JSON files handled by this script will include sensitive user information in plain text. Make sure to dispose of these files accordingly.

Output of example CSVs:  
<img width="315" height="1200" alt="Vault screenshot" src="https://github.com/user-attachments/assets/1a5beb76-c6cb-4c64-99c3-a84d241d1963" />


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
The CLI Import collects information about your project, KSM Application, Gateway(s), and PAM Configuration(s), then requires two CSVs:
- A CSV for PAM user records.
- A CSV for PAM resource records.
Consult the _CSV Format_ chapter to find out more about CSV syntax.

After every step, the process will save your progress to a _import_autosave.json_ file. Consult the _JSON Format_ chapter to find out more about this template.  

Before the import into Keeper, you will be able to rerun any of the steps in this process.

### 2. Completed JSON File
If you've completed the _CLI Prompts and CSV Files_ already, or if you created your JSON template by other means, you can use this method to skip to the CLI process using the JSON template.

### 3. Partial JSON File
If you would like to resume from an autosave file, or have a partially completed JSON template, you can use this method to skip to specific steps in the CLI import.

___
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

- Run the import again, setting existing KSM Application / Gateways / PAM Configurations so resources can be added to _existing_ models.

## Limitations  

- Object titles should be unique. This includes:
  - Project name*
  - Application name*
  - Gateway names*
  - PAM Configuration names*
  - Shared Folder names
  - User Folder names
  - Record titles

For items marked with *, the names must be unique across the Keeper Vault. Other items must simply be unique per project
- The import generates a PAM Configuration with all features enabled (that can be enabled with Commander). This can be edited after the import is complete
- A bespoke shared folder is created to be the Application folder for all PAM Configurations. This can be edited after the import is complete
- The import shares the user shared folders to your KSM app with can-edit permissions. This can be edited after the import is complete
- Record creation and configuration inherit limitations from Commander arguments

## Debugging

To toggle the display of Debug statements during the import, change the `DEBUG` constant at the beginning of the Python file.

___
## CSV Format

### 1. Users CSV

| shared_folder | folder_path       | title  | login  | password | pam_config   | {kwargs*}| _rotation.{kwargs*} |
| ------------- | ----------------- | ------ | ------ | -------- | ------------ | -------- | ------------------- |
| Users         |                   | root   | user01 | pwd01    | $config_name | {value*} | {value*}            |
| Users2        | folder01/folder02 | nested | user02 | pwd02    | $config_name | {value*} | {value*}            |

- The default separator for the `folder_path` column is `/`, however this can be customized in the CLI import
- Beyond the first 6 columns, `{kwargs*}` are Commander arguments for the `record-add` command. For instance:

| distinguishedName                                  | text.custom_field_name |
| -------------------------------------------------- | ---------------------- | 
| CN=Administrator,CN=Users,DC=keeper,DC=localdomain | custom_field_value     |

- `_rotation{kwargs*}` are Commander arguments for the `pam rotation edit` command. For instance:

| _rotation.resource | _rotation.on-demand |
| ------------------ | ------------------- |
| $resource_name     | _                   |

- Values prefixed with `$` refer to the title of a record within the project (or the PAM Configuration)
- For Commander flags that don't expect a value, use `_`
- All Commander arguments should use the long form (e.g. `_rotation.on-demand` and not `_rotation.od`)

Required columns for a PAM User with active local rotation:

| shared_folder | folder_path       | title  | login  | password | pam_config   | _rotation.resource | _rotation.on-demand |
| ------------- | ----------------- | ------ | ------ | -------- | ------------ | ------------------ | ------------------- |
| Users         |                   | root   | user01 | pwd01    | $config_name | $resource_name     | _                   |

(You do not need to set `configuration` or `config` as a flag - it is set automatically from the `pam_config` column)

___
### 2. Resources CSV

| shared_folder | folder_path       | title | type         | pam_config   | {kwargs*} | _connection.{kwargs*}  | _rbi.{kwargs*} | _tunnel.{kwargs*} |
| ------------- | ----------------- | ----- | ------------ | ------------ | --------- | ---------------------- | -------------- | ----------------- |
| Resources     |                   | AD01  | pamDirectory | $config_name | {value*}  | {value*}               | {value*}       | {value*}          |
| Resources2    | folder01/folder02 | SRV01 | pamMachine   | $config_name | {value*}  | {value*}               | {value*}       | {value*}          |

- The default separator for the `folder_path` column is `/`, however this can be customized in the CLI import
- Beyond the first 4 columns, `{kwargs*}` are Commander arguments for the `record-add` command. For instance:

| pamHostname   | operatingSystem |
| ------------- | --------------- | 
| 10.10.0.15:22 | linux           |

- `_connection{kwargs*}`, `_rbi{kwargs*}` and `_tunnel{kwargs*}` are Commander arguments for the `pam connection`, `rbi` and `tunnel edit` commands. For instance:

| _connection.protocol | _connection.admin-user |
| -------------------- | ---------------------- | 
| rdp                  | $PAMuser_name          |

- Values prefixed with `$` refer to the title of a record within the project (or the PAM Configuration)
- For Commander flags that don't expect a value, use `_`
- All Commander arguments should use the long form (e.g. `_connection.protocol` and not `_connection.p`)

Required columns for a RDP PAM Machine:

| shared_folder | folder_path       | title | type         | pam_config   | pamHostname   | _connection.admin-user  | _connection.protocol |
| ------------- | ----------------- | ----- | ------------ | ------------ | ------------- | ----------------------- | -------------------- |
| Resources     |                   | srv1  | pamMachine   | $config_name | 10.0.0.5:3389 | $PAMuser_name           | rdp                  |

(You do not need to set `configuration` or `config` as a flag - it is set automatically from the `pam_config` column)

___
## JSON Format

The internal Keeper import process runs from this JSON template, which handles nesting with nested dictionaries:

```
{
  "name": "new_project",
  "new_build": true,
  "application": {
    "new_build": true,
    "name": "new_app"
  },
  "gateways": [
    {
      "name": "new_gateway",
      "new_build": true,
      "init_method": null
    }
  ],
  "pam_config_folder": "new_project PAM configs (do not delete)",
  "pam_configs": [
    {
      "name": "new_config",
      "new_build": true,
      "gateway": "new_gateway"
    }
  ],
  "user_folders": {
    "AD": {
      "EU users": {
        "content": {
          "Dev users": {
            "content": {
              "Infra users": {
                "content": {},
                "AD_admin": {
                  "folder_path": [
                    "EU users",
                    "Dev users",
                    "Infra users"
                  ],
                  "title": "AD_admin",
                  "login": "Administrator",
                  "password": "some_strong_password",
                  "pam_config": "$new_config",
                  "_rotation.resource": "$AD",
                  "_rotation.on-demand": "_",
                  "type": "pamUser"
                }
              }
            }
          },
          "Staff users": {
            "content": {
              "HR": {
                "content": {},
                "AD01": {
                  "folder_path": [
                    "EU users",
                    "Staff users",
                    "HR"
                  ],
                  "title": "AD01",
                  "login": "demouser",
                  "password": "some_strong_password",
                  "pam_config": null,
                  "_rotation.resource": null,
                  "_rotation.on-demand": null,
                  "type": "pamUser"
                }
              }
            }
          }
        }
      }
    },
    "LOCAL": {
      "EU users": {
        "content": {},
        "dev1": {
          "folder_path": [
            "EU users"
          ],
          "title": "dev1",
          "login": "user123456",
          "password": "some_strong_password",
          "pam_config": null,
          "_rotation.resource": null,
          "_rotation.on-demand": null,
          "type": "pamUser"
        }
      },
      "dev2": {
        "folder_path": "",
        "title": "dev2",
        "login": "user456789",
        "password": "some_strong_password",
        "pam_config": null,
        "_rotation.resource": null,
        "_rotation.on-demand": null,
        "type": "pamUser"
      }
    }
  },
  "resource_folders": {
    "resources": {
      "EU": {
        "content": {
          "Dev": {
            "content": {
              "Infra": {
                "content": {},
                "AD": {
                  "folder_path": [
                    "EU",
                    "Dev",
                    "Infra"
                  ],
                  "title": "AD",
                  "type": "pamMachine",
                  "pam_config": "$new_config",
                  "pamHostname": "1.1.1.1:3389",
                  "rbiUrl": "",
                  "_connection.admin-user": "$AD_admin",
                  "_connection.protocol": "rdp",
                  "_tunnel.enable-tunneling": "_",
                  "_rbi.remote-browser-isolation": null
                }
              },
              "DevOps": {
                "content": {},
                "srv2": {
                  "folder_path": [
                    "EU",
                    "Dev",
                    "DevOps"
                  ],
                  "title": "srv2",
                  "type": "pamDatabase",
                  "pam_config": "$new_config",
                  "pamHostname": "1.1.1.1:22",
                  "rbiUrl": "",
                  "_connection.admin-user": "$dev1",
                  "_connection.protocol": "ssh",
                  "_tunnel.enable-tunneling": null,
                  "_rbi.remote-browser-isolation": null
                }
              }
            }
          }
        },
        "srv1": {
          "folder_path": [
            "EU"
          ],
          "title": "srv1",
          "type": "pamMachine",
          "pam_config": "$new_config",
          "pamHostname": "1.1.1.1:22",
          "rbiUrl": "",
          "_connection.admin-user": "$dev1",
          "_connection.protocol": "ssh",
          "_tunnel.enable-tunneling": null,
          "_rbi.remote-browser-isolation": null
        }
      },
      "net": {
        "folder_path": "",
        "title": "net",
        "type": "pamRemoteBrowser",
        "pam_config": "$new_config",
        "pamHostname": "",
        "rbiUrl": "https://test.com",
        "_connection.admin-user": "",
        "_connection.protocol": "",
        "_tunnel.enable-tunneling": "",
        "_rbi.remote-browser-isolation": "on"
      }
    }
  }
}
```
