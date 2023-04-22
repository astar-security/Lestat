# Lestat

![](https://3.bp.blogspot.com/-PF5wQWEREK0/U_DS_eJM8nI/AAAAAAAAAVw/ack4TeHRyME/s1600/033.jpg)  
Lestat is a framework for performing password robustness analysis.  
It is dedicated to be used by two main populations :
- Pentesters who want to quickly identify valuable accounts from the ones they compromised
- Pentesters who want to easily restitute some stats about password quality of the company
- Sysadmins who want to test the robustness of the employees' passwords

## What it does

Mainly, Lestat does analysis about a list of already cracked accounts :

- Distinguishing disabled accounts
- Distinguishing highly privileged accounts
- Providing a reflective view : "user compromised --> groups associated" and "group --> members compromised"
- Providing a comprehensive set of stats and charts about the passwords cracked (length distribution, charset, robustness evaluation, most frequent pattern, ...)

Also, Lestat provides facilities to perform :

- Domain's users information exfiltration
- Domain's users hashes exfiltration
- Wordlists generation for dictionnary attacks
- Domain's users passwords cracking

But it is not the main goal.

## Requirement

```
#For domain users info compilation.  
pip install ldapdomaindump
# For remote hash extraction.
pip install impacket
# For wordlist generation
pip install click
```

## Basic Usage

Lestat needs two inputs :

- The `domain_users.grep` file from ldapdomaindump
- A file containing all the cracked accounts with `user:password` lines

### Get those inputs

Lestat provides an automated script to obtains those inputs.  
Feed it with a domain admin account to dump the required data:
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
Connect with RDP to the DC and run:
```
cmd.exe /c ntdsutil "ac i ntds" "ifm" "create full c:\temp\robb" q q
```
Then, get these two files to your machine:
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

For pure bruteforce enumeration, take 2 or 3 days [cracking](https://github.com/astar-security/Lestat/wiki/Crack_with_john) the `DOMAIN_HASHES.txt` file with you favorite tool.    
Here are examples with `john-the-ripper`:
```
john --format=NT --wordlist=rockyou.txt DOMAIN_HASHES.txt
john --format=NT --fork=8 DOMAIN_HASHES.txt
```

You can also use the wordlists provided by lestat in the wordlists directory :

```
python3 gen_names_wordlist.py
python3 gen_dates_wordlist.py
python3 gen_places_wordlist.py
...
```

When finished, get the result in the raw form of a login:password file (one per line):
```
john --format=NT --show DOMAIN_HASHES.txt> | cut -d: -f 1,2 > JOHN_RESULT.txt
```

### Loot:
Directly see if you cracked enabled admin accounts :
```
$ python3 LesterTheLooter.py --priv JOHN_RESULT.txt USERS_INFO.txt
[*] Importing domain info from USERS_INFO.txt
[*] Importing john result from JOHN_RESULT.txt
[*] Assigning robustness
[*] Requesting wordlist...
[+] Wordlist downloaded
[*] Computing groups information
[*] Computing stats
[*] Privileged accounts compromised are listed below:
        STATUS    USERNAME        PASSWORD          SENSITIVE         #GROUPS  DESCRIPTION
[+]	enabled   n.sarko         Cecilia<3         domain admins     6        to disable
[+]	enabled   f.maçon         NOMondial2020!    likely admin      21987       
[+]	enabled   adm.boloré      Y4tch4life        enterprise admins 17       
[+]	enabled   e.macron        Macron2027!!!!    domain admins     10       
[+]	enabled   b.gates         VaccineApple!     enterprise admins 8        
[+]	enabled   e.philippe      Prosac2k19        account operators 3             
[*] Exporting to XLSX format in lestat.xlsx
[*] Making the charts for all accounts...
[*] Making the charts for active accounts...
[+] Export successful. All finished !
```
All the data are exported to a unique XLSX file.  
But you can also obtain three CSV files (`lestat.csv`, `users_compromised.csv` and `group_compromised.csv`) with the `--csv` option. 

_NOTE: the tool will ignore every line which does not have at least one ':' separator. If more than one ':' is detected, it will only retain the first and the second fields and ignore the rest. So, the direct result of `john --format=NT --show DOMAIn_HASHES.txt` will be correctly parsed (but you will see many warning)_

### Restitute

Produce a easy to read Excel file with all the information compiled :

```
$ python3 LesterTheLooter.py JOHN_RESULT.txt USERS_INFO.txt
```

### Be proud
PNG charts are generated on the fly by LesterTheLooter and incoporated in the XLSX file.

![](https://camo.githubusercontent.com/aa8c35cdb071322f9c0e0d3c0dae9d5bef295cfabaa01115159e640badafffde/68747470733a2f2f626f6e6e792e61737461722e6f72672f6578616d706c655f6c65737461742e706e67)

You can also use the `GregTheGrapher.py` script in a standalone mode to generate charts from a `lestat.csv` file:  
```
python3 GregTheGrapher.py -w charts --transparent lestat.csv 
```

For any question/support about this project, please visit: [www.astar.org](https://www.astar.org).
