# lestat
Check robustness of your (their) Active Directory accounts passwords

## Get domain hashes
From a privileged cmd.exe on the Domain Controller, run:  
```
C:\>ntdsutil
ntdsutil: activate instance ntds
ntdsutil: ifm
ifm: create full c:\robb
ifm: quit
ntdsutil: quit
```
Then, donwload these two files on your Linux machine:
```
smbclient -U <USERNAME>%<PASSWORD> \\\\<DC_IP>\\C$ -c 'get "robb\Active Directory\ntds.dit"'
smbclient -U <USERNAME>%<PASSWORD> \\\\<DC_IP>\\C$ -c 'get "robb\registry\SYSTEM"'
```
Extract the hashes with impacket:
```
impacket-secretsdump -system <PATH_TO_SYSTEM_FILE> -ntds <PATH_TO_ntds.dit_FILE> LOCAL > hashes.txt
```
## Get users info from the domain
Use `ldapdomaindump`:
```
ldapdomaindump -u <DOMAIN>\\<USER> -p <PASSWORD> ldap://<DC_IP>:389
```
We will use the `domain_users.grep` file

## Crack
Use john the ripper at your convenience:
```
john --format=NT --fork=<AS_YOU_WANT> hashes.txt
```
