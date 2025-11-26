# kcm_import

## Requirements

All module requirements are conditional:  
- To read database connection arguments from your `docker-compose.yml` file, import `pyYAML`:
```
pip install pyYAML
```
- To extract data from a MySQL / Guacamole-mysql database, import `mysql-connector`:
```
pip install mysql-connector
```
- To extract data from a PostgreSQL / Guacamole-postgresql database, import `psycopg2`:
```
pip install psycopg2-binary
```

## Usage

Run the parent pam_import script and select option `4. Import connections from KCM on-prem`:
```
python pam_import.py
```

### Connecting to the Database

#### Automatic Connection
With `pyYAML` installed, the script can read the `docker-compose.yml` file provided and determine the database connection parameters (whether the database is hosted in the container or externally).  
If you are using the default `docker-compose.yml` template, make sure to add open ports in the `db` service so the script can connect:
```
ports:
   // for MySQL
   - "3306:3306"
   // for PostgreSQL
   - "5432:5432"
```

#### Manual Connection

Alternatively, you can hardset the `DB_CONFIG` variable at the head of the `kcm_import.py` file with your connection parameters.

### PAM Configuration Catch-all

The pam_import requires a `pam_config` value for resources (and users if rotation parameters are set). While the kcm_import can export it's CSVs so you can add these parameters before importing them, it also allows you to set a blanket `pam_config` name for all users and resources.

### Folder Structure

The kcm_import process will split the KCM structure into two - one for users and the other for resources. This structure can be modelled in three ways:  
- Mixed  
The nesting of Connection Groups is preserved with user folders, however Connection Group with a KSM Configuration will be modelled as root shared folders.
```
ROOT/  
. .|_ Connection group A/  
. . . .|_ Connection group A1/  
Connection group B/ (with KSM config)  
. .|_ Connection group B1/
```

- Nested  
The exact nesting of Connection Groups is preserved, irrespective of KSM Configuration. Only one shared folder (ROOT) is created.
```
ROOT/  
. .|_ Connection group A/  
. . . .|_ Connection group A1/  
. .|_ Connection group B/ (with KSM config)  
. . . .|_ Connection group B1/
```

- Flat  
Nesting is ignored, all Connection Groups are modelled as root shared folders.
``` 
ROOT/  
Connection group A/  
Connection group A1/  
Connection group B/  
Connection group B1/
```

## Capabilities

- Connect to database automatically from `docker-compose.yml` or manually
- Extract Connections and Connection Groups from KCM
- Generate one of three different nesting structures for the Connection Groups in KCM
- Export data to ready-to-import CSVs for users and resources, as well as a CSV for any record that require additional work (Dynamic Tokens and SFTP)
- If no work is needed, import data right away with all records under a unique PAM Configuration

## Limitations

- The kcm_import script can detect Connection Groups that have a KSM Configuration, but cannot unmask this configuration. This means that it is not possible to pull the values from Dynamic or Static Tokens.
- The kcm_import script does not support adding SFTP parameters on resources such as RDP connections.
Records with Dynamic Tokens or SFTP parameters will be compiled into a `KCM_logs.csv` file, which can be worked on afterwards.

## Debugging

The kcm_import script inherits the debug behavior from the pam_import script.

## Mappings

The pam_import process uses Commander argument syntax.
Parameters extracted from KCM are not a match for these arguments, and must be converted. This is the role of the `KCM_mappings.json` file.
- Mappings set as `ignore` in the file are parameters that aren't relevant to KeeperPAM
- Mappings set as `null` are parameters which don't have a correspondence in Commander
- Mappings set as `log` are parameters which cannot be implemented with the kcm_import, but can be added manually - a `KCM_logs.csv` file is created after the import to outline them.
  By default, this includes Dynamic Tokens and SFTP parameters, but you can set any mapping value to `log` if you wish to include records detected with this parameter in the file.
- Any missing mapping will result in a warning on the CLI to highlight it.
