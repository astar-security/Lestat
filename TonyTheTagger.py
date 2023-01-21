#!/usr/bin/python3

from difflib import SequenceMatcher as similar
import string
import requests
from wordlists.variations import *

# numbers are time to crack in an online bruteforce attack with OSINT: 0=seconds, 1=minutes, 2=hours, 3=days, 4=years
resistance = {
        "empty": 0,
        "login": 0,
        "company": 0,
        "top10": 0,
        "login derivation": 1,
        "company derivation": 1,
        "top1000": 1,
        "tiny": 1,
        "top1M": 2,
        "short": 2,
        "simple": 3,
        "common": 3
        }

#########
# UTILS #
#########

def attributeReason(cu, user, reason):
    global resistance
    #check if reason was previously set
    if reason == "check":
        r = cu[user]['reason']
        if r is not "undetermined":
            if r in resistance.keys():
                cu[user]['robustness'] = resistance[r]
            else:
                cu[user]['robustness'] = 3
    else:
        cu[user]['reason'] = reason
        cu[user]['robustness'] = resistance[reason]

def downloadWordlist(wordlist):
    print("[*] Requesting wordlist...")
    r = requests.get(wordlist)
    if not r.ok:
        print("[!] download failed")
    print("[+] wordlist downloaded")
    candidates = r.text.split("\n")
    return candidates

def unleet(name):
    leet = str.maketrans("01345789!@$€",
                         "oieastbgiase")
    return name.translate(leet)

def getCharsets(passwd):
    """give the composition of the password : l=lowercase u=uppercase n=numeric s=symbol"""
    cs = ''
    if any([i for i in passwd if i in string.ascii_lowercase]):
        cs += 'l'
    if any([i for i in passwd if i in string.ascii_uppercase]):
        cs += 'u'
    if any([i for i in passwd if i in string.digits]):
        cs += 'd'
    if any([i for i in passwd if i in string.punctuation]):
        cs += 'p'
    return cs

def bruteforceEffort(password):
    """return maximal number of attempts in pure exhaustive attack"""
    cs = getCharsets(password)
    effort = (('d' in cs) * len(string.digits) +
              ('l' in cs) * len(string.ascii_lowercase) +
              ('u' in cs) * len(string.ascii_uppercase) +
              ('p' in cs) * len(string.punctuation)) ** len(password)
    return effort

########
# COOK #
########

def populateRobustness(cu, domains):
    top1M = downloadWordlist("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt")

    # sanitize domain name
    separators = r'[\-\'\ \._&/]'
    domlist = set()
    for dom in domains:
        domlist.update(re.split(separators, dom.split('.')[0].lower()))

    for user, val in cu.items() :
        passw = val['password'].lower()
        d1 = similar(None, user, unleet(passw)).ratio()
        d2 = similar(None, user, getRoot(passw)).ratio()
        dom_distances = []
        for dom in domlist:
            dom_distances.append(similar(None, dom, unleet(passw)).ratio())
            dom_distances.append(similar(None, dom, getRoot(passw)).ratio())
        effort = bruteforceEffort(val['password'])

        # check if robustness was previously determined:
        attributeReason(cu, user, "check")

        # check empty
        if passw == '':
            attributeReason(cu, user, 'empty')
        # check login
        elif passw == user:
            attributeReason(cu, user, 'login')
        # check company
        elif passw in domlist:
            attributeReason(cu, user, 'company')
        # check top 10 most common
        elif passw in top1M[0:10]:
            attributeReason(cu, user, 'top10')
        # check top 1000 most common
        elif passw in top1M[0:1000]:
            attributeReason(cu, user, 'top1000')
        # check robustness against exhaustive attack
        elif effort/10000 < 60*60*2 :
            attributeReason(cu, user, 'tiny')
        # check login derivation
        elif d1 > 0.75 or d2 > 0.75:
            attributeReason(cu, user, 'login derivation')
        # check company derivation
        elif any([i for i in dom_distances if i > 0.75]):
            attributeReason(cu, user, 'company derivation')
        # check top 1 million most common
        elif passw in top1M:
            attributeReason(cu, user, 'top1M')
        # check robustness against exhaustive attack
        elif effort/10000 < 60*60*24*2 :
            attributeReason(cu, user, 'short')
        # check robustness against exhaustive attack
        elif effort/10000 < 60*60*24*365*2 :
            attributeReason(cu, user, 'simple')
        else:
            attributeReason(cu, user, 'common')            



