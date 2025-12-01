from utils import *

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'guacamole_user',
    'password': 'password',
    'database': 'guacamole_db',
    'port': 3306
}

TOTP_ACCOUNT = 'kcm-totp@keepersecurity.com'

SQL = {
    'groups': """
SELECT 
    cg.connection_group_id, 
    parent_id, 
    connection_group_name,
    cga.attribute_value AS ksm_config
FROM 
    guacamole_connection_group cg
LEFT JOIN 
    guacamole_connection_group_attribute cga
ON 
    cg.connection_group_id = cga.connection_group_id
    AND cga.attribute_name = 'ksm-config'
""",
    'connections': """
SELECT
    c.connection_id,
    c.connection_name AS name,
    c.protocol,
    cp.parameter_name,
    cp.parameter_value,
    e.name AS entity_name,
    e.type AS entity_type,
    g.connection_group_id,
    g.parent_id,
    g.connection_group_name AS group_name,
    ca.attribute_name,
    ca.attribute_value
FROM
    guacamole_connection c
LEFT JOIN
    guacamole_connection_parameter cp ON c.connection_id = cp.connection_id
LEFT JOIN
    guacamole_connection_attribute ca ON c.connection_id = ca.connection_id
LEFT JOIN
    guacamole_connection_group g ON c.parent_id = g.connection_group_id
LEFT JOIN
    guacamole_connection_permission p ON c.connection_id = p.connection_id
LEFT JOIN
    guacamole_entity e ON p.entity_id = e.entity_id;
"""
}


class KCM_import:
    def __init__(self,DEBUG):
        self.mappings = validate_file_upload('json','./KCM/KCM_mappings.json')
        self.debug = DEBUG
        self.db_config = DB_CONFIG
        self.pam_config = ''
        self.folder_structure = 'ksm_based'
        self.separator = '/'
        self.dynamic_tokens = []
        self.logged_records = {}
        self.completed = False
        self.to_import = False
        
        display('# KCM Import','bold yellow')
        # Collect import method
        display('What database are you running on KCM?', 'cyan')
        list_items(['(1) MySQL','(2) PostgreSQL'])
        self.database = handle_prompt({'1':'MYSQL','2':'POSTGRES'})
        
        self.collect_db_config()
        
        connect = self.connect_to_db()
        if not connect:
            display('Unable to connect to database, ending program')
            return
            
        self.generate_data()
        
        from csv import DictWriter
        def export_to_csv(data,filename):
            headers = []
            for obj in data:
                for arg in obj:
                    if arg not in headers:
                        headers.append(arg)

            with open(f'{filename}.csv','w',newline='') as file:
                writer = DictWriter(file,headers)
                writer.writeheader()
                writer.writerows(data)
                    
        if self.logged_records:
            display('Exporting Dynamic Tokens and Logged Records as KCM_logs.csv...')
            export_to_csv(list(record for record in self.logged_records.values()),'KCM_logs.csv')
            display('Done','italic green')
        
        display('# Data collected and import-ready', 'green')
        display('What do you wish to do with the extracted data?', 'cyan')
        list_items(['(1) Export it for manual rework (e.g. setting pam_config)','(2) Import it right away'])
        action = handle_prompt({'1':'export','2':'import'})
        if action=='import':
            self.completed = True
            self.to_import = True
            return
        elif action=='export':      
            display('Exporting Users CSV as KCM_users.csv...')
            export_to_csv(self.user_records,'KCM_users')
            display('Done','italic green')
            
            display('Exporting Resources CSV as KCM_resources.csv...')
            export_to_csv(self.resource_records,'KCM_resources')
            display('Done','italic green')
            
            self.completed = True
            return
        

    def collect_db_config(self):
        display('How do you wish to provide your database details?', 'cyan')
        list_items([
            '(1) By docker-compose.yml file',
            '(2) I have hardcoded them in the Python script'
        ])
        if handle_prompt({'1':'file','2':'code'}) == 'file':
            display('## Please upload your docker-compose file', 'cyan')
            self.docker_compose = validate_file_upload('yaml')
            
            port={'MYSQL':3306,'POSTGRES':5432}
            custom_port = None
            
            debug('Analysing services',self.debug)
            guacamole_env = self.docker_compose['services']['guacamole']['environment']
            db_in_compose = True
            host = '127.0.0.1'
            if f'{self.database}_HOSTNAME' not in guacamole_env:
                debug('Alternate DB hostname detected',self.debug)
                host = guacamole_env[f'{self.database}_HOSTNAME']
                db_in_compose=False
            if db_in_compose and 'ports' in self.docker_compose['services'][guacamole_env[f'{self.database}_HOSTNAME']]:
                custom_port = int(self.docker_compose["services"][guacamole_env[f"{self.database}_HOSTNAME"]]["ports"][0].split(':')[0])
            try:
                self.db_config = {
                    'host': host,
                    'user': guacamole_env[f'{self.database}_USERNAME'],
                    'password': guacamole_env[f'{self.database}_PASSWORD'],
                    'database': guacamole_env[f'{self.database}_DATABASE'],
                    'port': custom_port or port[self.database]
                }
            except:
                display('Unable to parse environment variables into suitable DB details. Please check that your docker-compose file has all relevant Guacamole variables, or hardcode them in the script','italic red')
                self.collect_db_config()
 
    
    def connect_to_db(self):
        if self.database == 'MYSQL':
            try:
                from mysql.connector import connect
                debug('Attempting connection to database',self.debug)
                conn = connect(**self.db_config)
                cursor = conn.cursor(dictionary=True)
                
                display('Database connection successful. Extracting data...','italic green')
                
                debug('Extracting connection group data',self.debug)
                cursor.execute(SQL['groups'])
                self.group_data = cursor.fetchall()
                
                debug('Extracting connection data',self.debug)
                cursor.execute(SQL['connections'])
                self.connection_data = cursor.fetchall()
                
                display('Done','italic green')
                
                return True
                
            except mysql.connector.Error as e:
                display(f'MYSQL connector error: {e}','bold red')
                return False
                
        elif self.database == 'POSTGRES':
            try:
                from psycopg2 import connect
                from psycopg2.extras import RealDictCursor
                debug('Attempting connection to database',self.debug)
                conn = connect(**self.db_config)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                display('Database connection successful. Extracting data...','italic green')
                
                debug('Extracting connection group data',self.debug)
                cursor.execute(SQL['groups'])
                group_rows = cursor.fetchall()
                self.group_data = [dict(row) for row in group_rows]
                
                debug('Extracting connection data',self.debug)
                cursor.execute(SQL['connections'])
                connection_rows = cursor.fetchall()
                self.connection_data = [dict(row) for row in connection_rows]
                
                display('Done','italic green')
                
                return True
            except:    
                display(f'POSTGRESQL connector error: {e}','bold red')
                return False

    def generate_data(self):
        display('Do you want to apply a specific PAM Configuration name to all resources?','cyan')
        display('If not, you will have the option to export your resources to CSV before the full import','yellow')
        list_items(['(1) Yes','(2) No'])
        if handle_prompt({'1':True,'2':False}):
            self.pam_config = '$'+input('PAM Configuration name: ')
        display('By default, this import will keep the Connection Group nesting you have set in KCM, but any Group with a KSM config will be modelled as a root shared folder', 'yellow')
        display('What handling do you want to apply to Connection Groups?','cyan')
        list_items([
            '''(1) Mixed (recommended)  
ROOT/  
. .|_ Connection group A/  
. . . .|_ Connection group A1/  
Connection group B/ (with KSM config)  
. .|_ Connection group B1/  
            ''',
            '''(2) Keep exact nesting  
ROOT/  
. .|_ Connection group A/  
. . . .|_ Connection group A1/  
. .|_ Connection group B/ (with KSM config)  
. . . .|_ Connection group B1/  
            ''',
            '''(3) Flat  
ROOT/  
Connection group A/  
Connection group A1/  
Connection group B/  
Connection group B1/  
            '''
        ])
        self.folder_structure = handle_prompt({'1':'ksm_based','2':'nested','3':'flat'})
        
        display(f'Do you want to set a specific separator for Connection Group paths (default is "{self.separator}")?', 'cyan')
        list_items(['(1) Yes','(2) No'])
        if handle_prompt({'1':True,'2':False}):
            self.separator = input('New separator: ')
        
        self.group_paths = {}
    
        def resolve_path(group_id):
            if group_id is None:
                return "ROOT"
            if group_id in self.group_paths:
                return self.group_paths[group_id]
            # Find the group details
            group = next(g for g in self.group_data if g['connection_group_id'] == group_id)
            if self.folder_structure == 'ksm_based' and group['ksm_config']:
                self.group_paths[group_id] = group['connection_group_name']
                return group['connection_group_name']
            parent_path = resolve_path(group['parent_id'])
            full_path = f"{parent_path}{self.separator}{group['connection_group_name']}"
            self.group_paths[group_id] = full_path
            return full_path

        # Resolve paths for all groups
        for group in self.group_data:
            if self.folder_structure=='flat':
                self.group_paths[group['connection_group_id']] = group['connection_group_name']
            else:
                resolve_path(group['connection_group_id'])
        
        self.connections = {}
        self.users = {}
        for connection in self.connection_data:
            id = connection['connection_id']
            name = connection["name"]
            debug(f'Importing Connection {name}',self.debug)
            
            KCM_folder_path = self.group_paths.get(connection['connection_group_id'],'ROOT')
            folder_array = KCM_folder_path.split(self.separator)
            shared_folder = folder_array[0]
            folder_path = ''
                
            if id not in self.users:
                if len(folder_array)>1:
                    for folder in folder_array:
                        folder = f'Users - {folder}'
                    folder_path = self.separator.join(folder_array[1:])
                user = {
                    'shared_folder':f'Users - {shared_folder}',
                    'folder_path':folder_path,
                    'title': f'User - {name}',
                    'pam_config':self.pam_config,
                }
                self.users[id] = user
                
            if id not in self.connections:
                if len(folder_array)>1:
                    for folder in folder_array:
                        folder = f'Resources - {folder}'
                    folder_path = self.separator.join(folder_array[1:])
                    
                # Define record-type
                types = {
                    'http': 'pamRemoteBrowser',
                    'mysql': 'pamDatabase',
                    'postgresql': 'pamDatabase',
                    'sql-server': 'pamDatabase',
                }
                    
                resource = {
                    'shared_folder':f'Resources - {shared_folder}',
                    'folder_path':folder_path,
                    'title': f'Resource {name}',
                    'type':types.get(connection['protocol'],'pamMachine'),
                    'pam_config':self.pam_config,
                    '_connection.admin-user':f'$User - {name}',
                    'pamHostname':{'hostname':None,'port':None},
                    '_connection.protocol': connection['protocol']
                }                
                self.connections[id] = resource
            
            def handle_arg(id,name,arg,value):
                def handle_mapping(mapping,dir):
                    if mapping == 'ignore':
                        debug(f'Mapping {arg} ignored',self.debug)
                    elif mapping is None:
                        debug(f'Mapping {arg} recognized but not supported',self.debug)
                    elif '=' in mapping:
                        dir[id][mapping.split('=')[0]] = mapping.split('=')[1]
                    elif mapping=='log':
                        if name not in self.logged_records:
                            debug(f'Adding record {name} to logged records',self.debug)
                            self.logged_records[name] = {'name':name, arg:value}
                        else:
                            self.logged_records[name][arg] = value
                    else:
                        dir[id][mapping] = value
                    return dir
                
                if value.startswith('${KEEPER_') and id not in self.dynamic_tokens:
                    debug('Dynamic token detected',self.debug)
                    self.dynamic_tokens.append(id)
                    if name not in self.logged_records:
                        self.logged_records[name] = {'name':name, 'dynamic_token':True}
                    else:
                        self.logged_records[name]['dynamic_token'] = True
                elif value and arg.startswith('totp-'):
                    if 'oneTimeCode' not in user:
                        user['oneTimeCode'] = {
                            "totp-algorithm": '',
                            "totp-digits": "",
                            "totp-period": "",
                            "totp-secret": ""
                            }
                    user['oneTimeCode'][arg] = value
                elif value and arg == 'hostname':
                    resource['pamHostname']['hostname'] = value
                elif value and arg == 'port':
                    resource['pamHostname']['port'] = value
                elif value and arg in self.mappings['users']:
                    self.users = handle_mapping(self.mappings['users'][arg],self.users)
                elif arg in self.mappings['resources']:
                    self.connections = handle_mapping(self.mappings['resources'][arg],self.connections)
                else:
                    display(f'Error: Unknown parameter detected: {arg}. Add it to KCM_mappings.json to resolve this error','bold red')
 
            # Handle args
            if connection['parameter_name']:
                handle_arg(id,connection['name'],connection['parameter_name'],connection['parameter_value'])
            # Handle attributes
            if connection['attribute_name']:
                handle_arg(id,connection['name'],connection['attribute_name'],connection['attribute_value'])

        
        self.user_records = list(user for user in self.users.values())
        self.resource_records = list(conn for conn in self.connections.values())
        
        # Sanitize totp
        for user in self.user_records:
            if 'oneTimeCode' in user:
                alg = user['oneTimeCode']["totp-algorithm"]
                dig = user['oneTimeCode']["totp-digits"]
                period = user['oneTimeCode']["totp-period"]
                secret = user['oneTimeCode']["totp-secret"]
                user['oneTimeCode'] = f'tpauth://totp/{TOTP_ACCOUNT}?secret={secret}&issuer=&algorithm={alg}&digits={dig}&period={period}'
        
        # Sanitize pamHostname
        for resource in self.resource_records:
            host = resource['pamHostname']['hostname']
            port = resource['pamHostname']['port']
            if host is not None and port is not None:
                resource['pamHostname'] = ':'.join([host,port])
            else:
                resource.pop('pamHostname',None)
                
        if self.dynamic_tokens:
            display(f'{len(self.dynamic_tokens)} dynamic tokens detected')
        if self.logged_records:
            display(f'{len(self.logged_records)} records logged')
