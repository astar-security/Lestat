# Lestat
![](https://3.bp.blogspot.com/-PF5wQWEREK0/U_DS_eJM8nI/AAAAAAAAAVw/ack4TeHRyME/s1600/033.jpg)  
Check robustness of your (their) Active Directory accounts passwords

See the wiki for the complete guide : https://github.com/astar-security/Lestat/wiki  

## What it does
You give it a file of `user:password` lines that you cracked.  
It will give you:
- the list of the domain groups of each craked account
- an indicator about whether a cracked account is admin or not
- the status of each cracked account: ACCOUNT_DISABLED or ACCOUNT_ENABLED
- the list of all the domain groups compromised through the cracked accounts (no false positive due to disabled users)
- a comprehensive set of stats about the passwords cracked (length distribution, charset, robustness evaluation, most frequent pattern, ...)

## Requirement
Lestat should run out of the box.  

## Basic Usage
Take 2 or 3 days [cracking](https://github.com/astar-security/Lestat/wiki/Crack_with_john) with `john-the-ripper` (with or without [wordlists](https://github.com/astar-security/Lestat/wiki/GetWordlists)) over [the hashes file of your domain](https://github.com/astar-security/Lestat/wiki/GetTheHash).  
Then, get the raw result:
```
john --format=nt --show <HASHES_FILE> | cut -d: -f 1,2 > result_file
```
[Dump the users info](https://github.com/astar-security/Lestat/wiki/GetUsersInfo) from the domain to get the `domain_users.grep` file.  
Main way is:
```
ldapdomaindump -u <DOMAIN>\\<USER> -p <PASSWORD> ldap://<DC_IP>:389
```

### For pentesters:
```
$ python3 RobbTheRobber.py --priv result_file domain_users.grep
```

### For SysAdmin:
To get minimal stats :  
```
$ python3 RobbTheRobber.py --stats result_file domain_users.grep
```
To get comprehensive stats if you configured the wordlists (see [here](https://github.com/astar-security/Lestat/wiki/GetWordlists)):
```
python3 RobbTheRobber.py --wordlists <PATH_TO_WORDLISTS> --stats result_file domain_users.grep
```
