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

## Advanced usage
Look for presence of users in the HaveIBeenPwned list (optionnal):  
```
python3 leakTheWeak.py --verbose <HASHES_FILE> <HAVEIBEENPWNED_LIST>
```
Look only for users not already cracked by john:
```
python3 leakTheWeak.py --john <JOHN_RESULT_FILE> <HASHES_FILE> <HAVEIBEENPWNED_LIST>
```
Append those users to the same john result file:
```
python3 leakTheWeak.py --john <JOHN_RESULT_FILE> -w <JOHN_RESULT_FILE> <HASHES_FILE> <HAVEIBEENPWNED_LIST>
```
