#!/usr/bin/python3

import hashlib
import click
import logging as log
import requests
import time
import re
import itertools

log.basicConfig(format=' %(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

########
# COOK #
########

### dict

dictpath = "/usr/share/dict/words"

### birthdates

birthdates = []
# 3112 3112! 1231 1231!
for m in [str(i).zfill(2) for i in range(1,13)]:
    for d in [str(i).zfill(2) for i in range(1,32)]:
        birthdates += [ d+m, d+m+'!', m+d, m+d+'!' ]

# 1988 1988! 88 88!
for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
    birthdates += ['', y, y + '!', y[2:], y[2:] + '!']

birthdates = set(birthdates)

### root

# useful for voyel substitution: david -> dvd, julia -> jl, roxane -> rxn
root = str.maketrans('','','aeiouy')

### case

def allCase(word):
    word = word.lower()
    # compute daniel, DANIEL, Daniel, dANIEL
    return [word, word.upper(), word.capitalize(), word[:1] + word[1:].upper()]


### dates

months_en = [ "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "spring", "summer", "autumn", "winter" ]
months_nl = [ "januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december", "lente", "zomer", "herfst", "winter" ]
months_fr = [ "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre", "printemps", "ete", "automne", "hivers" ]
months = months_en + months_fr + months_nl + ['']
years = []
for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
    # for 1988 add 1988, 1988!, 88, 88!
    years += ['', y, y + '!', y[2:], y[2:] + '!']
    if int(y) > 2009:
        # for 2017, add 2k17, 2K17, 2k17!, 2K17!
        years += ["2k" + y[2:], "2K" + y[2:], "2k" + y[2:] + '!', "2K" + y[2:] + '!']

years = set(years)

### l33t swap

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        'g':['9'],
        't':['7']
        }

### suffixes

common_special = [
        "!",
        "@",
        "$",
        "%",
        "&",
        "*",
        "?",
        ".",
        ""
        ]

common_words = [
        "pw",
        "pwd",
        "admin",
        "pass",
        "adm",
        ""
        ]

common_numeric = set([''])
# 2010 -> now
common_numeric.update( [str(i) for i in range(2010, int(time.strftime("%Y"))+1)] )
# 2k10 -> now
common_numeric.update( ["2k"+str(i)[-2:] for i in range(2010, int(time.strftime("%Y"))+1)] )
# 2K10 -> now
common_numeric.update( ["2K"+str(i)[-2:] for i in range(2010, int(time.strftime("%Y"))+1)] )
# 0 -> 9
common_numeric.update( [str(i) for i in range(10)] )
# 00 -> 99
common_numeric.update( [str(i).zfill(2) for i in range(100)] )
# common numbers
common_numeric.update( ['123', '1234'] )


def leet_variation(words):
    global leet_swap
    res = set()
    first_pass = []
    for word in words:
        res.add(word)
        if word.isalpha() and len(set(word)) > 1 and len(word) > 2:
            needles = [c for c in leet_swap.keys() if c in word.lower()]
            for i in range(len(needles)):
                nee1 = needles[i]
                for sub in leet_swap[nee1]:
                    first_pass.append(re.sub(nee1, sub, word, flags=re.I))
                res |= set(first_pass)
                for j in range(i+1,len(needles)):
                    nee2 = needles[j]
                    for word2 in first_pass:
                        for sub in leet_swap[nee2]:
                            res.add(re.sub(nee2, sub, word2, flags=re.I))
                first_pass = []
    return res


def case_variation(words):
    res = set()
    for word in words:
        res.update( [word, word.upper(), word.capitalize()] )
    return res

common_prefix = case_variation(leet_variation(common_words))
common_suffix = set([n + s for n in common_numeric for s in common_special])
common_complete = set(itertools.product(common_prefix, common_suffix))

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

def johnIt(ntlm, candidates, reason):
    cpt = 0
    with click.progressbar(candidates) as candidatesbar:
        for c in candidatesbar:
            hc = passwd2NTLM(c)
            if hc in ntlm["safe"]:
                ntlm["cracked"][hc] = {"password": c, "reason": reason, "accounts": list(ntlm["safe"][hc])}
                del(ntlm["safe"][hc])
                log.info(f"[+] Password found: '{c}' for {ntlm['cracked'][hc]['accounts']}")
                cpt += 1
    return ntlm, cpt

def johnItWithWordlist(ntlm, wordlist, reason):
    cpt = 0
    with open(wordlist) as f:
        for line in f:
            c = line[:-1]
            hc = passwd2NTLM(c)
            if hc in ntlm["safe"]:
                ntlm["cracked"][hc] = {"password": c, "reason": reason, "accounts": list(ntlm["safe"][hc])}
                del(ntlm["safe"][hc])
                log.info(f"[+] Password found: '{c}' for {ntlm['cracked'][hc]['accounts']}")
                cpt += 1
    log.info(f"[*] {cpt} unique password compromised, {len(ntlm['safe'])} remaining")
    return ntlm

##############
# STRATEGIES #
##############

def strat_top10(ntlm):
    log.info("[*] Testing top 10 most common passwords...")
    candidates = ('', '1234', '123456', '12345678', 'password', 'Password', 'Passw0rd', 'test', '123123', 'abc123')
    ntlm, cpt = johnIt(ntlm, candidates, "top10")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_top1000(ntlm):
    log.info("[*] Testing top 1000 most common passwords...")
    wordlist= "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000.txt"
    candidates = downloadWordlist(wordlist)
    ntlm, cpt = johnIt(ntlm, candidates, "top1000")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_top1M(ntlm):
    log.info("[*] Testing top 1M most common passwords...")
    wordlist= "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt"
    candidates = downloadWordlist(wordlist)
    ntlm, cpt = johnIt(ntlm, candidates, "top1M")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    return ntlm

def strat_names(ntlm):
    log.info("[*] Testing names and birthdates...")
    wordlist = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt"
    names = downloadWordlist(wordlist)
    candidates = set()
    for name in names:
        name = name.lower()
        # prefix for eg Nicolas: nicolas, nic, nico, nini, ncls
        prefix = [name, name[:3], name[:4], name[:2] + name[:2], name.translate(root)]
        for p in prefix:
            for s in birthdates:
                candidates.update(allCase(p+s))
    ntlm, cpt = johnIt(ntlm, candidates, "name")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    del(candidates)
    del(names)
    return ntlm

def strat_dates(ntlm):
    global months
    global years
    log.info("[*] Testing dates...")
    candidates = set()
    for month in months:
        # shortname like July -> jul
        prefix = [month, month[0:3]]
        for p in prefix:
            for s in years:
                candidates.update(allCase(p+s))
    ntlm, cpt = johnIt(ntlm, candidates, "date")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    del(candidates)
    return ntlm

def strat_words(ntlm):
    global dictpath
    log.info("[*] Testing words...")
    candidates = set()
    with open(dictpath) as f:
        for line in f:
            candidates.update( allCase(line[:-1]) )
    ntlm, cpt = johnIt(ntlm, candidates, "words")
    log.info(f"[*] {cpt} new passwords cracked, {len(ntlm['safe'])} remaining")
    del(candidates)
    return ntlm


def crack(ntlm):
    # 1st strategy
    ntlm = strat_top10(ntlm)
    # 2nd strategy    
    ntlm = strat_top1000(ntlm)
    # 3rd strategy    
    ntlm = strat_top1M(ntlm)
    # 4th strategy    
    ntlm = strat_dates(ntlm)
    # 5th strategy    
    #ntlm = strat_names(ntlm)
    # 6th strategy
    ntlm = strat_words(ntlm)
    return ntlm

##########
# EXPORT #
##########

def export(ntlm, outfile):
    with open(outfile, "w") as f:
        for h, details in ntlm["cracked"].items():
            for account in details["accounts"]:
                f.write(f"{account}:{details['password']}:{details['reason']}\n")
    log.info(f"[*] result exported in {outfile}")


########
# MAIN #
########

@click.command()
@click.argument('HASH_FILE')
def main(hash_file):
    outfile = "testyyy"
    ntlm = readHashFile(hash_file)
    ntlm = crack(ntlm)
    export(ntlm, outfile)
    


if __name__ == '__main__':
    main()
