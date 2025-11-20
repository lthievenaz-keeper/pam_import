# Modelling IAM AD rotations

There are two ways to model AD rotations with KeeperPAM:
- Using a PAM Directory resource to represent the AD - [documentation]([url](https://docs.keeper.io/en/keeperpam/privileged-access-manager/password-rotation/rotation-use-cases/local-network/active-directory))
- Using a PAM Configuration to represent the AD - [documentation]([url](https://docs.keeper.io/en/keeperpam/privileged-access-manager/password-rotation/rotation-use-cases/active-directory))

The PAM Configuration model can be achieved with the pam_import script, however needs to be handled in two steps:
1. Create the PAM objects required to set up the PAM configuration model:
  - PAM Gateway folder
  - PAM User record (AD admin)
  - KSM Application
  - PAM Gateway
  - PAM Configuration
2. Map the PAM Configuration as a Domain Controller
  - Set the gateway
  - Map the AD Admin user
  - Set the Domain Controller hostname and port (636)
3. Run the pam_import script

This is the expected format of the Users CSV file, where `AD_config` is the name of your Domain Controller PAM Configuration.
| shared_folder | folder_path       | title  | login  | password | pam_config   | distinguishedName | _rotation.on_demand |
| ------------- | ----------------- | ------ | ------ | -------- | ------------ | ----------------- | ------------------- |
| AD Users      |                   | AD01   | user01 |          | $AD_config   | {DN*}             | _            |
