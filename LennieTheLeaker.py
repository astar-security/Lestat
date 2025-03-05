#!/usr/bin/python3

import requests
import argparse
import click
import re
import sys

HIBP_API = "https://api.pwnedpasswords.com/range/"

def importHIBP(output_file):
    """TODO : allow resume"""
    global HIBP_API
    print("[*] Downloading HIPB database ...")
    with open(output_file, "w") as f:
        with click.progressbar([hex(i)[2:].zfill(5).upper() for i in range(0x100000)]) as hashbar:
            for prefix in hashbar:
                try:
                    r = requests.get(HIBP_API + prefix + "?mode=ntlm")
                    leaked = r.text.split('\n')
                    for leak in leaked:
                        suffix,p = leak.split(':')
                        f.write(f"{p.strip()}:::{prefix+suffix}:::\n")
                except Exception as e:
                    print(f"[!] Error during database download: {e}")
    print(f"[+] Download completed, {output_file} file written")


def isNTLMHash(candidate):
    """Check if a string has the format of an NTLM hash."""
    ntlm_regex = r'^[0-9A-Fa-f]{32}$'
    return re.match(ntlm_regex, candidate)

def readJohnFile(john):
    exclude = {}
    print("[*] Importing already cracked hashes from John result file ...")
    try:
        with open(john) as j:
            for line in j:
                parts = line.split(':')
                if len(parts) == 8 and isNTLMHash(parts[4]):
                    h = parts[4].upper()
                    if h and h not in exclude:
                        exclude[h] = {"users":set(), "password":parts[1]}
    except Exception as e:
        print(f"[!] Error during parsing of John result file : \"{e}\"")
        exit(1)
    print(f"[+] {len(exclude)} imported hashes to exclude from the research")
    return exclude

def readHashFile(hashfile, john=''):
    exclude = {}
    if john:
        exclude = readJohnFile(john)
    ntlm = {}
    print("[*] Parsing hashes file ...")
    with open(hashfile) as f:
        for line in f:
            parts = line.strip().split(':')
            # case where input file has the form user:NTLM hash
            if len(parts) == 2 and isNTLMHash(parts[1]):
                h = parts[1].upper()
                u = parts[0].lower()
            # case where input file has the form of a secretsdump result
            elif len(parts) == 7 and isNTLMHash(parts[2]) and isNTLMHash(parts[3]):
                h = parts[3].upper()
                u = parts[0].lower()
            else:
                continue
            # if john file is provided
            if h in exclude:
                #print(f"[*] {line} ignored because already cracked : {exclude[h]['password']}")
                exclude[h]['users'].add(u)
            else:
                if h not in ntlm:
                    ntlm[h] = {"users": set(), "prevalence":0}
                ntlm[h]['users'].add(u)
    nb_users = sum([len(i['users']) for i in ntlm.values()])
    res = f"[+] Parsing completed. {nb_users} users detected with {len(ntlm)} unique NTLM hashes"
    if len(exclude) > 0:
        nb_users_excluded = sum([len(i['users']) for i in exclude.values()])
        res += f" - {nb_users_excluded} users ignored because already cracked"
    print(res)
    return ntlm, exclude

def isLeaked(hash, candidates):
    """Check if the hash is part of the compromised hashes suffixes sent by HIPB"""
    hash = hash.upper()
    for suffix in candidates:
        parts = suffix.strip().split(':')
        if hash[5:] == parts[0]:
            return int(parts[1])
    return 0

def searchLeaked(ntlm, verbose):
    global HIBP_API
    print("[*] Checking HaveIBeenPwned database for leaked passwords ...")
    cpt = {'hashes':0, 'users':0}
    with click.progressbar(ntlm) as hashbar:
        for h in hashbar:
            try:
                r = requests.get(HIBP_API + h[:5] + "?mode=ntlm")
                candidates = r.text.split('\n')
                ntlm[h]["prevalence"] = isLeaked(h, candidates)
                if ntlm[h]['prevalence'] > 0:
                    cpt['hashes'] += 1
                    cpt['users'] += len(ntlm[h]['users'])
                    if verbose:
                        print(f"[+] Hash leaked {ntlm[h]['prevalence']} time(s): {h} used by {ntlm[h]['users']}")
            except Exception as e:
                print(f"[!] Error during hash comparison with HIBP database : {e}")
    print(f"[+] Check completed : {cpt['hashes']} hashes leaked affecting {cpt['users']} users")
    return ntlm

def searchLeakedLocal(ntlm, verbose, lb):
    """Expect a HIBP file with 'int:::hash:::' lines where int the the occurrence"""
    print("[*] Checking local HaveIBeenPwned database for leaked passwords ...")
    cpt = {'hashes':0, 'users':0}
    try:
        with open(lb) as f:
            for line in f:
                    prevalence, h, _ = line.split(':::')
                    if h in ntlm :
                        cpt['hashes'] += 1
                        cpt['users'] += len(ntlm[h]['users'])
                        ntlm[h]['prevalence'] = int(prevalence)
                        if verbose:
                            print(f"[+] Hash leaked {ntlm[h]['prevalence']} time(s): {h} used by {ntlm[h]['users']}")
        print(f"[+] Check completed : {cpt['hashes']} hashes leaked affecting {cpt['users']} users")
        return ntlm
    except Exception as e:
        # if the database file doest not exist, propose to download HIBP db
        if type(e) == FileNotFoundError:
            i = input(f"[!] \"{lb}\" file does not exist. Would you like to download the HIBP database ? It takes a long time\n[y/n] : ")
            if i == 'y':
                importHIBP(lb)
                return searchLeakedLocal(ntlm, verbose, lb)
            else:
                print("[!] Aborting")
                exit(1)
        else:
            print(f"[!] Error during hash comparison with HIBP database : \"{e}\" with line: {line} ")
            exit(1)


def getRobustness(prevalence):
    if prevalence > 10000:
        return ("seconds", "Leaked > 10000 times")
    elif prevalence > 1000:
        return ("minutes", "Leaked > 1000 times")
    elif prevalence > 100:
        return ("hours", "Leaked > 100 times")
    else :
        return ("days", "Leaked > 1 time")

def export(ntlm, exclude, output=''):
    print(f"[*] Exporting result to {output if output else 'stdout'} ...")
    out = open(output, "w") if output else sys.stdout
    for h in ntlm:
        if ntlm[h]['prevalence'] > 0:
            for u in ntlm[h]['users']:
                rob = getRobustness(ntlm[h]['prevalence'])
                line = f"{u}:Leaked {ntlm[h]['prevalence']} times:{rob[0]}:{rob[1]}"
                print(line, file=out)
    for h in exclude:
        for u in exclude[h]['users']:
            line = f"{u}:{exclude[h]['password']}::"
            print(line, file=out)
    if output:
        out.close()
    print("[+] Export completed")


def main():
    parser = argparse.ArgumentParser(description='Lists accounts compromised through leaked databases', add_help=True)
    parser.add_argument('-w', '--write', action="store", dest="path", default='',
            help='A path to store the results. Default is stdout')
    parser.add_argument('HASH_FILE', action="store",
            help='A file with "user:NTLM hash" lines or the raw result of impacket-secretsdump.py')
    parser.add_argument('-j', '--john', action="store", dest="john_file", default='',
            help="If a 'john --show' result file is provided, only the accounts not cracked by john are analyzed")
    parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", default=False,
            help="display the cracked accounts in real time")
    parser.add_argument('-db', '--leakbase', action="store", dest="lb", default='',
            help="Local database of leaked hashes for offline usage. If the filename does not exist, will download the database")
    args = parser.parse_args()

    ntlm, exclude = readHashFile(args.HASH_FILE, args.john_file)
    if args.lb:
        ntlm = searchLeakedLocal(ntlm, args.verbose, args.lb)
    else:
        ntlm = searchLeaked(ntlm, args.verbose)
    export(ntlm, exclude, args.path)

if __name__ == '__main__':
    main()
