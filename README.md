# Lestat
![](https://3.bp.blogspot.com/-PF5wQWEREK0/U_DS_eJM8nI/AAAAAAAAAVw/ack4TeHRyME/s1600/033.jpg)  
Check robustness of your (their) Active Directory accounts passwords

## What it does
You give it a file of `user:password` lines that you cracked.  
It will give you:
- the list of the domain groups of each craked account
- an indicator about whether a cracked account is admin or not
- the status of each cracked account: ACCOUNT_DISABLED or ACCOUNT_ENABLED
- the list of all the domain groups compromised through the cracked accounts (no false positive due to disabled users)
- a comprehensive set of stats about the passwords cracked (length distribution, charset, robustness evaluation, most frequent pattern, ...)

## Requirement
`ldapdomaindump` is required for domain users info compilation.  
`impacket` is required for remote hash extraction.

## Basic Usage
### Get the data

Use the automated script with a domain admin account to dump the required data:
```
python3 RobbTheRobber.py --user <USERNAME> --password <PASSWORD> --domain <DOMAIN>
# the --password can be omitted, then it will be prompted
# eg. python3 RobbTheRobber.py --user Administrator --domain astar.org
```
It will produce two files:
- DOMAIN_HASHES.txt
- USERS_INFO.txt

---
#### /!\ Workaround /!\

Some antivirus could block the remote execution needed to get these data (how to blame them). If it happens, you can get the required data manually.  

3 files are needed, first the domain users info in a grepable format. You must use `ldapdomaindump`:
```
ldapdomaindump -u <DOMAIN>\\<USER> -p <PASSWORD> --no-html --no-json ldap://<DC_IP>:389
```
Only the `domain_users.grep` file is needed (you can rename it `USERS_INFO.txt` to comply with the examples of this documentation).

Second, we need the `NTDS.dit` file of the Domain Controller with its `SYSTEM` key.  
If the AV prevent the automated script to run, connect with RDP to the DC and run:
```
cmd.exe /c ntdsutil "ac i ntds" "ifm" "create full c:\temp\robb" q q
```
Then, move these two files to your machine:
- C:\temp\robb\Active Directory\ntds.dit
- C:\temp\robb\registry\SYSTEM

Finally, parse the NTDS.dit file with `secretsdump`:
```
impacket-secretsdump -system SYSTEM -ntds ntds.dit LOCAL > DOMAIN_HASHES.txt
```
---

### Hack with your favorite tool

You can use the proposed `jonhTheRipper.py` script which perform attacks on common and predictable passwords:
```
python3 JohnTheRipper.py DOMAIN_HASHES.txt
```

For pure bruteforce enumeration, take 2 or 3 days [cracking](https://github.com/astar-security/Lestat/wiki/Crack_with_john) the `DOMAIN_HASHES.txt` file with you favorite tool (with or without [wordlists](https://github.com/astar-security/Lestat/wiki/GetWordlists)).  
Here are examples with `john-the-ripper`:
```
john --format=NT --wordlist=rockyou.txt DOMAIN_HASHES.txt
john --format=NT --fork=8 DOMAIN_HASHES.txt
```

When finished, get the result in the raw form of a login:password file (one per line):
```
john --format=NT --show DOMAIN_HASHES.txt> | cut -d: -f 1,2 > JOHN_RESULT.txt
```

### Loot:
Directly see if you cracked enabled admin accounts :
```
$ python3 LesterTheLooter.py --priv JOHN_RESULT.txt USERS_INFO.txt
[*] Importing john result from JOHN_RESULT.txt and domain info from USERS_INFO.txt
[!] Line ignored in JOHN_RESULT.txt file (not a valid user:password form): 
[!] Line ignored in JOHN_RESULT.txt file (not a valid user:password form): 124 password hashes cracked, 589 left
[*] Computing groups information
[*] Exporting data to users_compromised.csv and group_compromised.csv
[*] Privileged accounts compromised are listed below:
[+]	disabled     domain admins        n.sarko                  Cecilia<3
[+]	enabled      likely admin         f.maçon                  NOMondial2020!
[+]	enabled      enterprise admins    adm.boloré               Y4tch4life
[+]	enabled      domain admins        e.macron                 Macron2022!!!
[+]	enabled      enterprise admins    b.gates                  VaccineApple!
[+]	disabled     account operators    e.philippe               Prosac2k19
```
Three CSV files are produced: `lestat.csv`, `users_compromised.csv` and `group_compromised.csv`. They contain the full results.

_NOTE: the tool will ignore every line which does not have at least one ':' separator. If more than one ':' is detected, it will only retain the first and the second fields and ignore the rest. So, the direct result of `john --format=NT --show DOMAIn_HASHES.txt` will be correctly parsed (but you will see many warning)_

### Be proud
PNG charts can be generated from the `lestat.csv` file:  
```
python3 GregTheGrapher.py -w charts --transparent lestat.csv 
```

It is recommended to present the result in a Excel file. Import `users_compromised.csv` in one sheet, `group_compromised.csv` in a second one and use the pictures for a dedicated summary sheet:

![](https://camo.githubusercontent.com/aa8c35cdb071322f9c0e0d3c0dae9d5bef295cfabaa01115159e640badafffde/68747470733a2f2f626f6e6e792e61737461722e6f72672f6578616d706c655f6c65737461742e706e67)

For any question/support about this project, please visit: [www.astar.org](https://www.astar.org).
