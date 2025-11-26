# kcm_import WIP

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
pip install psycopg2
```

## Usage

open the ports on docker-compose

## Capabilities


## Limitations

-sftp


## Debugging

The kcm_import script inherits the debug behavior from the pam_import script.
