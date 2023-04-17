#!/usr/bin/python3

import hashlib
import click
import logging as log
import requests
import time
import re
import itertools
from gen_names_wordlist import *
from gen_dates_wordlist import *
from gen_numbers_wordlist import *
from gen_places_wordlist import *
from variations import *

log.basicConfig(format=' %(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

### dict

dictpath = "/usr/share/dict/words"

#########
# UTILS #
#########

def downloadWordlist(wordlist):
    log.info("[*] Requesting wordlist...")
    r = requests.get(wordlist)
    if not r.ok:
        log.error("[!] download failed")
    log.info("[+] wordlist downloaded")
    candidates = r.text.split("\n")
    return candidates

def cleanUsername(user):
    dom = ''
    if '@' in user:
        user, dom = user.split('@')
    elif '\\' in user:
        dom, user = user.split('\\')
    return user, dom

def readHashFile(hashfile):
    ntlm = {"cracked":{}, "safe":{}}
    with open(hashfile) as f:
        lines = f.readlines()
        for line in lines:
            try:
                l = line.split(':')
                h = l[3].lower()
                account = l[0].lower()
                if h not in ntlm["safe"]:
                    ntlm["safe"][h] = []
                ntlm["safe"][h].append(account)
            except Exception as e:
                log.warn(f"[!] line not well formated (will be ignored): '{line}'")
        log.info(f"[*] {len(lines)} lines parsed from {hashfile}. {len(ntlm['safe'])} unique passwords")
    return ntlm

def passwd2NTLM(passwd):
    return hashlib.new('md4', passwd.encode('utf-16le')).hexdigest()

def johnIt(ntlm, candidates, robustness, reason):
    cpt = 0
    with click.progressbar(candidates) as candidatesbar:
        for c in candidatesbar:
            hc = passwd2NTLM(c)
            if hc in ntlm["safe"]:
                ntlm["cracked"][hc] = {"password": c, "reason": reason, "robustness": robustness, 
                                       "accounts": list(ntlm["safe"][hc])}
                del(ntlm["safe"][hc])
                log.info(f"[+] Password found: '{c}' for {ntlm['cracked'][hc]['accounts']}")
                cpt += 1
    return ntlm, cpt

def johnItWithWordlist(ntlm, wordlist, robustness, reason):
    cpt = 0
    with open(wordlist) as f:
        for line in f:
            c = line[:-1]
            hc = passwd2NTLM(c)
            if hc in ntlm["safe"]:
                ntlm["cracked"][hc] = {"password": c, "reason": reason, "robustness": robustness,
                                       "accounts": list(ntlm["safe"][hc])}
                del(ntlm["safe"][hc])
                log.info(f"[+] Password found: '{c}' for {ntlm['cracked'][hc]['accounts']}")
                cpt += 1
    log.info(f"[*] {cpt} unique password compromised, {len(ntlm['safe'])} remaining")
    return ntlm

def update_ntlm(ntlm, res, robustness, reason):
    for h in res:
        ntlm["cracked"][h] = {"password": res[h], "reason": reason, "robustness": robustness,
                              "accounts": list(ntlm["safe"][h])}
        log.info(f"[+] Password found: '{res[h]}' for {' '.join(ntlm['cracked'][h]['accounts'])}")
        del(ntlm["safe"][h])
    log.info(f"[*] {len(res)} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm


##############
# STRATEGIES #
##############

def strat_empty(ntlm):
    log.info("[*] Testing empty passwords...")
    candidates = ['']
    ntlm, cpt = johnIt(ntlm, candidates, "seconds", "empty")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_login(ntlm):
    log.info("[*] Testing login as password...")
    candidates = ['']
    for accounts in ntlm['safe'].values():
        for account in accounts:
            clean, _ = cleanUsername(account)
            for i in range(1,len(clean)+1):
                candidates.append(clean[0:i])
                candidates.append(clean[0:i].upper())
                candidates.append(clean[0:i].capitalize())
    ntlm, cpt = johnIt(ntlm, candidates, "seconds", "login")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_company(ntlm):
    log.info("[*] Testing company name as password...")
    candidates = ['']
    for accounts in ntlm['safe'].values():
        for account in accounts:
            _, domain = cleanUsername(account)
            if domain != '':
                domain = domain.split('.')[0]
                candidates.append(domain)
                candidates.append(domain.upper())
                candidates.append(domain.capitalize())
    ntlm, cpt = johnIt(ntlm, candidates, "seconds", "company")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm


def strat_top10(ntlm):
    log.info("[*] Testing top 10 most common passwords...")
    candidates = ('1234', '123456', '12345678', 'password', 'Password', 'Passw0rd', 'test', '123123', 'abc123')
    ntlm, cpt = johnIt(ntlm, candidates, "seconds", "top10")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_top1000(ntlm):
    log.info("[*] Testing top 1000 most common passwords...")
    wordlist= "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000.txt"
    candidates = downloadWordlist(wordlist)
    ntlm, cpt = johnIt(ntlm, candidates, "minutes", "top1000")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_top1M(ntlm):
    log.info("[*] Testing top 1M most common passwords...")
    wordlist= "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt"
    candidates = downloadWordlist(wordlist)
    ntlm, cpt = johnIt(ntlm, candidates, "hours", "top1M")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_numbers(ntlm):
    log.info("[*] Testing numbers from 0 to 99999999...")
    res = cook_numbers(7, None, passwd2NTLM, ntlm['safe']) 
    return update_ntlm(ntlm, res, "hours", "digits only")

def strat_names(ntlm):
    log.info("[*] Testing names and birthdates...")
    res = cook_names("names.txt", None, passwd2NTLM, ntlm['safe']) 
    return update_ntlm(ntlm, res, "hours", "firstname")

def strat_places(ntlm):
    log.info("[*] Testing places...")
    res = cook_places("places.txt", None, passwd2NTLM, ntlm['safe']) 
    return update_ntlm(ntlm, res, "hours", "place")

def strat_dates(ntlm):
    log.info("[*] Testing dates...")
    res = cook_dates(None, passwd2NTLM, ntlm['safe']) 
    return update_ntlm(ntlm, res, "hours", "date")

def strat_words(ntlm):
    global dictpath
    log.info("[*] Testing words...")
    candidates = set()
    with open(dictpath) as f:
        for line in f:
            candidates.update( allCase(line[:-1]) )
    ntlm, cpt = johnIt(ntlm, candidates, "hours", "words")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    del(candidates)
    return ntlm


def crack(ntlm):
    ntlm = strat_empty(ntlm)
    ntlm = strat_company(ntlm)
    ntlm = strat_login(ntlm)
    ntlm = strat_top10(ntlm)
    ntlm = strat_top1000(ntlm)
    ntlm = strat_top1M(ntlm)
    ntlm = strat_numbers(ntlm)
    ntlm = strat_dates(ntlm)
    ntlm = strat_names(ntlm)
    ntlm = strat_places(ntlm)
    #ntlm = strat_words(ntlm)
    return ntlm

##########
# EXPORT #
##########

def export(ntlm, outfile):
    with open(outfile, "w") as f:
        for h, details in ntlm["cracked"].items():
            for account in details["accounts"]:
                f.write(f"{account}:{details['password']}:{details['robustness']}:{details['reason']}\n")
    log.info(f"[*] result exported in {outfile}")


########
# MAIN #
########

@click.command()
@click.argument('HASH_FILE')
def main(hash_file):
    outfile = "JOHN_RESULT.txt"
    ntlm = readHashFile(hash_file)
    ntlm = crack(ntlm)
    export(ntlm, outfile)
    


if __name__ == '__main__':
    main()

