# Lestat
![](https://3.bp.blogspot.com/-PF5wQWEREK0/U_DS_eJM8nI/AAAAAAAAAVw/ack4TeHRyME/s1600/033.jpg)  
Check robustness of your (their) Active Directory accounts passwords

See the wiki for the complete guide : https://github.com/astar-security/Lestat/wiki  

## What it does
You give it the john-the-ripper file result of the accounts you cracked.  
It will give you:
- the list of the domain groups of each craked account
- an indicator about whether a cracked account is admin or not
- the status of each cracked account: ACCOUNT_DISABLED or ACCOUNT_ENABLED
- the list of all the domain groups compromised through the cracked accounts (no false positive due to disabled users)
- a comprehensive set of stats about the passwords cracked (length distribution, charset, robustness evaluation, most frequent pattern, ...)

## Requirement
Lestat should run out of the box.  

## Basic Usage
For pentesters:
```
$ python3 /RobbTheRobber.py --priv result_john domain_users.grep
```

For SysAdmin:
```
$ python3 /RobbTheRobber.py --stats <OUTPUT_FILENAME> result_john domain_users.grep
```
