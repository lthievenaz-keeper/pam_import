# AD Rotation Models

With KeeperPAM, there are two ways to model AD rotations:
- (old) With a PAM Directory record representing the AD - [documentation]([url](https://docs.keeper.io/en/keeperpam/privileged-access-manager/password-rotation/rotation-use-cases/local-network/active-directory))
- (new) With a PAM Configuration representing the AD - [documentation]([url](https://docs.keeper.io/en/keeperpam/privileged-access-manager/password-rotation/rotation-use-cases/active-directory))

It is possible to handle AD rotations with the second model with the pam_import script, however this requires running it after setting up the PAM Configuration:
1. Create a KeeperPAM setup including:
  - A Gateway folder
  - A KSM Application
  - A PAM Gateway
  - A PAM Configuraton
2. Create a PAM User record representing the AD Admin with username, password and distinguished name fields
3. Update the PAM Configuration to be a Domain Controller type, with the above AD Admin as credential and the Domain Controller's hostname and port (636).

4. Run the pam_import script, selecting your existing KSM app, Gateway and PAM Configuration.

Find below the CSV format for AD users with IAM rotations set up to the PAM Configuration (here named `AD_config`):
| shared_folder | folder_path | title  | login  | password | pam_config   | distinguishedName | _rotation.iam-aad-config | _rotation.on-demand |
| ------------- | ----------- | ------ | ------ | -------- | ------------ | ----------------- | ------------------------ | ------------------- |
| AD Users      |             | AD01   | user01 |          | $AD_config   | {DN*}             | $AD_confi                | _                   |
