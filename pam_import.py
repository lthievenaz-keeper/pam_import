from utils import *

AUTOSAVE = True
DEBUG = True

class Project:
    def __init__(self):  
        self.separator = '/'
        
        display('# Welcome to the PAM Import','bold yellow')
        # Collect import method
        display('Which method would you like to use to import your content?', 'cyan')
        list_items([
            '(1) CLI Prompts and CSV files',
            '(2) I have a completed JSON file',
            '(3) I have a partial JSON file',
            '(4) Import connections from KCM on-prem (coming soon)'
        ])
        self.import_method = handle_prompt({'1':'cli','2':'json','3':'cli_rerun'})
            
        match self.import_method:
            case 'cli':
                self.cli_import()
            case 'json':
                display('## Please upload your completed JSON file', 'cyan')
                self.json = validate_file_upload('json')
            case 'cli_rerun':
                display('## Please upload your partial JSON file', 'cyan')
                self.json = validate_file_upload('json')
                self.rerun(False)
            #case 'kcm':
             #   from kcm_import import KCM_import
             #   self.json = KCM_import(self.json,DEBUG)
        
        self.execute_import()
            
            
    def autosave(self):
        if AUTOSAVE:
            with open('import_autosave.json','w') as file:
                dump(self.json,file,indent=2)
            display('Progress saved','italic green')
        else:
            display('Autosave feature disabled','italic red')
          
          
    def cli_import(self):
        display('Are you creating a new project?', 'cyan')
        display('This will define the parent folder where all PAM records are created.')
        list_items(['(1) Yes','(2) No'])
        new_project = False
        if handle_prompt({'1':True,'2':False}):
            new_project = True
            display('Enter the name for your new project:')
        else:
            display('Enter the name of your existing project folder:')
        project_name = input('Input: ')
        if not project_name:
            project_name = 'Project'
        self.json = {
            "name": project_name,
            "new_build":new_project,
            "application": {},
            "gateways": [],
            "pam_config_folder":f"{project_name} PAM configs (do not delete)",
            "pam_configs": [],
            "user_folders":{},
            "resource_folders":{}
        }
        
        self.setup_KSM_app()
        
        self.setup_gateways()
        
        self.setup_configs()
        
        self.collect_users()
        
        self.collect_resources()
        
        # Summarize project and enable redo
        self.rerun()
                
        
    def setup_KSM_app(self):
        display('# KSM application', None)
        display('Are you creating a new KSM application?', 'cyan')
        list_items(['(1) Yes','(2) No'])
        self.new_app = handle_prompt({'1':True,'2':False})
        if self.new_app:
            self.json['application']['new_build'] = True
            self.json['application']['name'] = input('Application name:')
        else:
            self.json['application']['new_build'] = False
            self.json['application']['name'] = input('Application name or UID: ')
        self.autosave()
    
    
    def setup_gateways(self):
        display('# Gateways')
        gateway_collection_complete = False
        while not (gateway_collection_complete):
            if not self.json['gateways']:
                display('Are you creating a new PAM gateway for this application?', 'cyan')
            else:
                display('Do you wish to create or add another gateway for this application?', 'cyan')
                list_items(['(1) Yes','(2) No'])
                if not handle_prompt({'1':True,'2':False}):
                    gateway_collection_complete = True
                else:
                    display('Are you creating a new gateway for this application?', 'cyan')
            if not gateway_collection_complete:
                list_items(['(1) Yes','(2) No, I want to use an existing gateway'])
                new_gateway = handle_prompt({'1':True,'2':False})
                if not new_gateway:
                    gateway_name = input('Gateway name or UID: ')
                    self.json['gateways'].append({'name':gateway_name,'new_build':False}) 
                else:
                    if self.json['gateways']:
                        display('Caution: Ensure gateway names are unique','italic red')
                    gateway_name = input('Gateway name: ')
                    display('What initialization do you need for this gateway?', 'cyan')
                    list_items([
                        '(1) One Time Token',
                        '(2) Configuration File (b64)',
                        '(3) Configuration File (JSON)',
                        '(4) Configuration File (k8s)',
                    ])
                    gateway_init = handle_prompt({
                        '1':None,
                        '2':'b64',
                        '3':'json',
                        '4':'k8s',
                    })
                    self.json['gateways'].append({'name':gateway_name,'new_build':True,'init_method':gateway_init}) 
        self.autosave()
    
    
    def setup_configs(self):
        display('# PAM Configurations')
        config_collection_complete = False
        while not (config_collection_complete):
            if not self.json['pam_configs']:
               display('Are you creating a new PAM configuration?', 'cyan')
            else:
                display('Do you wish to create another PAM configuration for this application?', 'cyan')
                list_items(['(1) Yes','(2) No'])
                if not handle_prompt({'1':True,'2':False}):
                    config_collection_complete = True
                else:
                    display('Are you creating a new PAM configuration?', 'cyan')
            if not config_collection_complete:
                list_items(['(1) Yes','(2) No'])
                new_config = handle_prompt({'1':True,'2':False})
                if not new_config:
                    config_name = input('PAM configuration name or UID: ')
                    self.json['pam_configs'].append({'name':config_name,'new_build':False}) 
                else:
                    if self.json['pam_configs']:
                        display('Caution: Ensure PAM configuration names are unique','italic red')
                    config_name = input('PAM configuration name: ')
                    config_gateway = None
                    gateway_list= []
                    gateway_inputs = {}
                    for i,gateway in enumerate(self.json['gateways']):
                        gateway_list.append(f'({str(i+1)}) {gateway["name"]}')
                        gateway_inputs[str(i+1)] = gateway["name"]
                    display('Which gateway should be connected to this PAM configuration?', 'cyan')
                    list_items(gateway_list)
                    chosen_gateway = handle_prompt(gateway_inputs)
                    self.json['pam_configs'].append({'name':config_name,'new_build':True,'gateway':chosen_gateway})
        self.autosave()
    
    
    
    def collect_users(self):
        display('# PAM Users')
        display('The User CSV should look like this:')
        display('''
| shared_folder | folder_path       | title  | login  | password | pam_config   | {kwargs*}| _rotation.{kwargs*} |
| ------------- | ----------------- | ------ | ------ | -------- | ------------ | -------- | ------------------- |
| Users         |                   | root   | user01 | pwd01    | $config_name | {value*} | {value*}            |
| Users2        | folder01/folder02 | nested | user02 | pwd02    | $config_name | {value*} | {value*}            |
        ''','green')
        display('{kwargs*} are Commander arguments for the record-add command. For instance:')
        display('''
| distinguishedName                                  | text.custom_field_name |
| -------------------------------------------------- | ---------------------- | 
| CN=Administrator,CN=Users,DC=keeper,DC=localdomain | custom_field_value     |
        ''','green')
        display('_rotation{kwargs*} are Commander arguments for the pam rotation edit command. For instance:')
        display('''
| _rotation.resource | _rotation.on-demand |
| ------------------ | ------------------- |
| $resource_name     | _                   |
        ''','green')
        display('Caution: Use the long format for all arguments','italic red')
        display(f'Do you want to set a specific separator for folder_path (default is "{self.separator}")?', 'cyan')
        list_items(['(1) Yes','(2) No'])
        if handle_prompt({'1':True,'2':False}):
            self.separator = input('New separator: ')
        display('## Please enter your Users CSV file', 'cyan')
        
        user_data = validate_file_upload('csv')
        
        self.generate_folders(user_data,'user_folders')
        self.generate_content(user_data,'user_folders')
        self.autosave()
        
    
    def collect_resources(self):
        display('# PAM Resources')
        display('The Resource CSV should look like this:')
        display('''
| shared_folder | folder_path       | title | type         | pam_config   | {kwargs*} | _connection.{kwargs*}  | _rbi.{kwargs*} | _tunnel.{kwargs*} |
| ------------- | ----------------- | ----- | ------------ | ------------ | --------- | ---------------------- | -------------- | ----------------- |
| Resources     |                   | AD01  | pamDirectory | $config_name | {value*}  | {value*}               | {value*}       | {value*}          |
| Resources2    | folder01/folder02 | SRV01 | pamMachine   | $config_name | {value*}  | {value*}               | {value*}       | {value*}          |
        ''','green')
        display('Caution: Ensure shared folder names are unique from the ones in your user data','italic red')
        display('{kwargs*} are Commander arguments for the record-add command. For instance:')
        display('''
| pamHostname   | operatingSystem |
| ------------- | --------------- | 
| 10.10.0.15:22 | linux           |
        ''','green')
        display('_connection{kwargs*}, _rbi{kwargs*} and _tunnel{kwargs*} are Commander arguments for the pam connection, rbi and tunnel edit commands. For instance:')
        display('''
| _connection.protocol | _connection.admin-user |
| -------------------- | ---------------------- | 
| rdp                  | $PAMuser_name          |
        ''','green')
        display('Caution: Use the long format for all arguments','italic red')
        display(f'Do you want to set a specific separator for folder_path (default is "{self.separator}")?', 'cyan')
        list_items(['(1) Yes','(2) No'])
        if handle_prompt({'1':True,'2':False}):
            self.separator = input('New separator: ')
        display('## Please enter your Resources CSV file', 'cyan')
        
        resource_data = validate_file_upload('csv')

        self.generate_folders(resource_data,'resource_folders')
        self.generate_content(resource_data,'resource_folders')
        self.autosave()
    
    
    def generate_folders(self,csv_data,root):
        shared_folders = {}
        user_folders = []
        
        for index, row in enumerate(csv_data):
            if not row['shared_folder']:
                display(f'Error on row {str(index+1)}: No assigned shared folder','bold red')
            elif row['shared_folder'] not in shared_folders:
                # Create shared folder dicts
                shared_folders[row['shared_folder']] = {}
            if row['folder_path'] and row['folder_path'].split(self.separator) not in user_folders:
                array = [row['shared_folder']] + row['folder_path'].split(self.separator)
                user_folders.append(array)
                
        # Extract user folders into nested dict
        dict = {}
        for folder_tree in user_folders:
            for i,folder in enumerate(folder_tree):
                # shared_folder depth
                if i==0:
                    current = dict
                    if folder not in current:
                        current[folder] = {}
                    current = current[folder]
                # user_folder depths
                elif folder not in current:
                    current[folder] = {'content':{}}
                    current = current[folder]['content']
                elif folder in current and i > 0:
                    current = current[folder]['content']
            
        self.json[root] = dict
    
    
    def generate_content(self,csv_data,root):
        for record in csv_data:
            if root=='user_folders':
                record['type'] = 'pamUser'
            shared_folder = record['shared_folder']
            record.pop('shared_folder',None)
            if not record['folder_path']:
                self.json[root][shared_folder][record['title']] = record
            else:
                record['folder_path'] = record['folder_path'].split(self.separator)
                location = self.get_folder_location(root,shared_folder,record['folder_path'])
                location[record['title']] = record
        
    
    def get_folder_location(self,root,shared_folder,folder_array):
        location = self.json[root][shared_folder]
        for i,folder in enumerate(folder_array):
            if i>0:
                location = location['content']
            location = location[folder]
        return location
        
        
    def rerun(self,new_build=True):
        complete = False
        if new_build:
            display('Do you need to run any of the following steps again?')
        else:
            display('Select a step to complete:')
        list_items([
        '(1) App setup',
        '(2) Gateways setup',
        '(3) PAM configurations setup',
        '(4) PAM Users collection',
        '(5) PAM Resources collection',
        '(6) None'
        ])
        do_over = handle_prompt({
            '1':'app',
            '2':'gateway',
            '3':'config',
            '4':'user',
            '5':'resource',
            '6':'none'
        })
        match do_over:
            case 'app':
                self.json['application'] = {}
                self.setup_KSM_app()
            case 'gateway':
                self.json['gateways'] = []
                self.setup_gateways()
            case 'config':
                self.json['pam_configs'] = []
                self.setup_configs()
            case 'user':
                self.json['user_folders'] = {}
                self.collect_users()
            case 'resource':
                self.json['resource_folders'] = {}
                self.collect_resources()
            case 'none':
                complete = True
        if not complete:
            self.rerun(new_build)
        
        
    
    def execute_import(self):
        self.errors = 0
        self.folder_uids = {}
        self.records = {}
        self.rotation_records = []
        self.connection_records = []
        self.rbi_records = []
        self.tunnel_records = []
        display('# Commander Sign In')
        from keepercommander.params import KeeperParams
        from keepercommander.commands.ksm import KSMCommand
        from keepercommander.commands.folder import FolderMakeCommand,get_folder_path,get_contained_record_uids
        from keepercommander.commands.pam.gateway_helper import create_gateway
        from keepercommander.commands.pam.config_helper import pam_configurations_get_all
        from keepercommander import api, cli
        # classes
        params = KeeperParams()
        KSM = KSMCommand()
        MKDIR = FolderMakeCommand()
        
        params.user = input('User email: ')
        api.login(params)
        api.sync_down(params)
        
        display('Commander login successful','italic green')
        
        
        def run_command(command):
            if command.startswith('record-add'):
                debug('Adding record',DEBUG)
            else:
                debug(f'Running command: {command}',DEBUG)
            try:
                cli.do_command(params,command)
                api.sync_down(params)
            except Exception as e:
                self.errors +=1
                display(f'Commander error: {e}','bold red')
        
        
        def list_records(folder,root):
            records = []
            for obj in folder:
                if 'content' in folder[obj]:
                    debug(f'Creating user folder {obj}',DEBUG)
                    uid = MKDIR.execute(
                        params,
                        folder=get_folder_path(params,self.folder_uids[root])+obj,
                        user_folder=True
                    )
                    api.sync_down(params)
                    self.folder_uids[obj] = uid
                    records += list_records(folder[obj]['content'],obj)  
                    
                    for val in folder[obj]:
                        if val != 'content':
                            records.append(folder[obj][val])                 
                else:
                    records.append(folder[obj])
            return records
        
        
        def get_uid(record,folder_uid):

            records = get_contained_record_uids(params,folder_uid)[folder_uid]
            for uid in records:
                if api.get_record(params,uid).title == record['title']:
                    debug(f'UID: {uid}',DEBUG)
                    return uid
                    
                    
        def create_record(record,root):
            debug(f'Preparing record-add for {record["title"]}',DEBUG)
            # Get folder
            folder = self.folder_uids[root]
            if isinstance(record['folder_path'],list):
                folder = self.folder_uids[record['folder_path'][-1]]
            debug(f'Parent folder UID: {folder}',DEBUG)
            
            # Check args and concat command
            command = f'record-add -rt {record["type"]} -t "{record["title"]}" --folder={folder} '
            debug('Scanning record arguments',DEBUG)
            rotation,connection,rbi,tunnel = False,False,False,False
            for arg in record:
                if arg[0] != '_' and record[arg] and arg not in ['folder_path','type','title','pam_config','uid']:
                    command += f'{arg}="{record[arg]}" '
                elif record[arg] and arg=='pam_config':
                    for config in self.json['pam_configs']:
                        if record[arg][1:] == config['name']:
                            record['pam_config'] = config['uid']
                if record[arg] and arg.startswith('_rotation.'):
                    rotation = True
                elif record[arg] and arg.startswith('_connection.'):
                    connection = True
                elif record[arg] and arg.startswith('_rbi.'):
                    rbi = True
                if record[arg] and arg.startswith('_tunnel.'):
                    tunnel = True
            if rotation:
                self.rotation_records.append(record)
            elif connection:
                self.connection_records.append(record)
            elif rbi:
                self.rbi_records.append(record)
            if tunnel:
                self.tunnel_records.append(record)
                
            # Create the record
            run_command(command)
            api.sync_down(params)
            uid = get_uid(record,folder)
            return uid
              

        def update_record(record,action):
            if not record['pam_config']:
                display(f'Error: Could not find PAM configuration for record {record["title"]}','bold red')
                return
            base_commands = {
                'rotation': f'pam rotation edit -r {record["uid"]} -c {record["pam_config"]} -f ',
                'connection': f'pam connection edit {record["uid"]} -cn on -c {record["pam_config"]} ',
                'rbi': f'pam rbi edit -r {record["uid"]} -c {record["pam_config"]} ',
                'tunnel': f'pam tunnel edit {record["uid"]} -c {record["pam_config"]} '
            }
            result_command = base_commands[action]
            
            for arg in record:
                if arg.startswith(f'_{action}.'):
                    argument = arg.split('.')[1]
                    # Convert object name to uid
                    if record[arg] and record[arg][0] == '$':
                        result_command += f'--{argument} {self.records[record[arg][1:]]["uid"]} '
                    # Handle args with no value
                    elif record[arg] == '_':
                        result_command += f'--{argument} '
                    elif record[arg]:
                        result_command += f'--{argument} {record[arg]} '
            
            # Check if command has changed
            if result_command != base_commands[action]:
                run_command(result_command)
                
                
        def wipe_project():
            display('Do you wish to delete all created objects?', 'red')
            list_items(['(1) Yes','(2) No'])
            if handle_prompt({'1':True,'2':False}):
                display('Deleting project data...','red')
                try:
                    config_objs = pam_configurations_get_all(params)
                    for config in self.json['pam_configs']:
                        for config_obj in config_objs:
                            if loads(config_obj['data_unencrypted'].decode('utf-8'))['title'] == config['name']:
                                run_command(f'pam config remove {config_obj["record_uid"]}')
                except:
                    pass
                try:
                     run_command(f'sm app remove "{app_name}" -f')
                except:
                    pass
                try:
                     run_command(f'rmdir "{self.json["name"]}" -f')
                except:
                    pass
            display('Data deleted','red')
            
            
        display('# Import','bold yellow')
        
        display('Creating vault folders...','yellow')
        user_folder_uids = []
        shared_folder_uids = []

        try:
            if self.json['new_build']:
                debug(f'Creating master folder {self.json["name"]}',DEBUG)
                run_command(f'mkdir -uf "{self.json["name"]}"')
            
            
            if self.json['new_build']:
                debug('Creating PAM config container folder',DEBUG)
                shared_folder_uids.append(MKDIR.execute(
                    params,
                    folder=f'{self.json["name"]}/{self.json["pam_config_folder"]}',
                    shared_folder=True
                ))
            for folder in self.json['user_folders']:
                debug(f'Creating shared folder {folder}',DEBUG)
                uid = MKDIR.execute(
                    params,
                    folder=f'{self.json["name"]}/{folder}',
                    shared_folder=True
                )
                user_folder_uids.append(uid)
                self.folder_uids[folder] = uid
            for folder in self.json['resource_folders']:
                debug(f'Creating shared folder {folder}',DEBUG)
                uid = MKDIR.execute(
                    params,
                    folder=f'{self.json["name"]}/{folder}',
                    shared_folder=True
                )
                shared_folder_uids.append(uid)
                self.folder_uids[folder] = uid
            api.sync_down(params)
            display('Done','italic green')
            
            app_name = self.json['application']['name']
            if self.json['application']['new_build']:
                display('Creating the KSM app...','yellow')
                app_json = KSM.add_new_v5_app(params, app_name, force_to_add=False, format_type='json')
                try:
                    app_name = loads(app_json)['app_uid']
                    self.json['application']['uid'] = app_name
                    api.sync_down(params)
                    display('Done','italic green')
                except Exception as e:
                    display(f'Error creating the app: {e}','bold red')
            self.autosave()
            
            debug('Adding user folders to app',DEBUG)
            KSM.add_app_share(params, user_folder_uids,app_name, is_editable=True)
            debug('Adding resource folders to app',DEBUG)
            KSM.add_app_share(params, shared_folder_uids,app_name, is_editable=False)
                
            for gateway in self.json['gateways']:
                if gateway['new_build']:
                    display(f'Creating gateway {gateway["name"]}...','yellow')
                    try:
                        gateway['token'] = create_gateway(params, gateway['name'], app_name, gateway['init_method'])
                        api.sync_down(params)
                        display('Done','italic green')
                    except Exception as e:
                        raise Exception(f'Error creating the gateway: {e}')
            self.autosave()
        
            
            for config in self.json['pam_configs']:
                if config['new_build']:
                    display(f'Creating config {config["name"]}...','yellow')
                    run_command(f'pam config new -t "{config["name"]}" -env local -sf "{self.json["pam_config_folder"]}" -g "{config["gateway"]}" -c on -u on -r on -rbi on -cr on -tr on')
                for config_obj in pam_configurations_get_all(params):
                    if config_obj['record_uid'] == config['name'] or loads(config_obj['data_unencrypted'].decode('utf-8'))['title'] == config['name']:
                        debug(f'UID: {config_obj["record_uid"]}',DEBUG)
                        config['uid'] = config_obj['record_uid']
                        self.records[config['name']] = {"uid":config_obj['record_uid']}
                if not config['uid']:
                    raise Exception(f'Unable to find the config UID for: {config["name"]}')
                else:
                    display('Done','italic green') 
            self.autosave()
                
            self.rotation_commands = []
            self.connection_commands = []
            self.rbi_commands = []
            self.tunnel_commands = []
            display('Creating PAM User Records...','yellow')
            for folder in self.json['user_folders']:
                for record in list_records(self.json['user_folders'][folder],folder):
                    if record:
                        record['uid'] = create_record(record,folder)
                        self.records[record['title']] = record
            display('Done','italic green')
            self.autosave()
            
            
            display('Creating PAM Resource Records...','yellow')
            for folder in self.json['resource_folders']:
                for record in list_records(self.json['resource_folders'][folder],folder):
                    if record:
                        record['uid'] = create_record(record,folder)
                        self.records[record['title']] = record
            display('Done','italic green')
            self.autosave()
            
            if self.connection_records:
                display('Handling Connection Records...','yellow')
                for record in self.connection_records:
                    update_record(record,'connection')
            if self.rotation_records:
                display('Handling Rotation Records...','yellow')
                for record in self.rotation_records:
                    update_record(record,'rotation')
            if self.rbi_records:
                display('Handling RBI Records...','yellow')
                for record in self.rbi_records:
                    update_record(record,'rbi')
            if self.tunnel_records:
                display('Handling Tunnel Records...','yellow')
                for record in self.tunnel_records:
                    update_record(record,'tunnel')
        except Exception as e:
            display(f'Critical error: {e}','bold red')
            self.errors +=1
            wipe_project()
        
        
        def complete_import():
            display('# Your import has completed','bold green')
            gateway_info = []
            for gateway in self.json['gateways']:
                if gateway['new_build'] and gateway['token']:
                    gateway_info.append(f'{gateway["name"]}: {gateway["token"]}')
            if gateway_info:
                display('## Gateway initialization information:','green')
                list_items(gateway_info,'green')
            display('## Please make sure you dispose of any CSV / JSON file containing sensitive data','italic red')
        
        
        if self.errors:
            display(f'{str(self.errors)} errors detected. Do you wish to delete all created objects and start over?', 'red')
            list_items(['(1) Yes','(2) No'])
            if handle_prompt({'1':True,'2':False}):
                wipe_project()
                Project()    
            else:            
                complete_import()
        else:
            complete_import()
            
            
Project()


