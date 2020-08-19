#!/usr/bin/python3

import string
import argparse
from collections import Counter

#########
# Const #
#########

PRIVILEGED_GROUPS = [
        "admins du domaine",
        "administrateurs du schéma",
        "administrateurs de l’entreprise",
        "administrateurs",
        "propriétaires créateurs de la stratégie de groupe",
        "account operators",
        "administrators",
        "backup operators",
        "certificate operators",
        "domain administrators",
        "enterprise administrators",
        "print operators",
        "replicator",
        "schema administrators",
        "server operators"
        ]

#########
# Utils #
#########


def beautifyName(person):
    """remove domain prefix like mydomain\\user"""
    person = person.lower()
    if '\\' in person:
        person = person.split('\\')[1]
    return person

def isPriv(elem, groups=None):
    """check clues about an element (user or group) being privileged"""
    suspected_admin = "adm" in elem
    # if elem is a user and groups a list
    if groups:
        for i in groups:
            if i in PRIVILEGED_GROUPS:
                return i
            if "adm" in i:
                suspected_admin = True
        if suspected_admin:
           return "likely admin"
        else:
            return None
    # if elem is a group and groups is empty
    else:
        if elem in PRIVILEGED_GROUPS:
            return elem
        elif suspected_admin:
            return "likely"
        else:
            return None

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

def getRoot(word):
    """obtain root of a password or username"""
    remove = str.maketrans('', '', string.digits+string.punctuation)
    return word.lower().translate(remove)

def getThatRobust(compromised, level):
    """ask for the list of users with a specific level of robustness/reason"""
    criteria = "robustness" if level in range(4) else "reason"
    total = 0
    for acc, info in compromised.items():
        if info[criteria] == level:
            print(acc, info['password'], sep='\t')
            total += 1
    print("total:",total)


########
# Init #
########


def initInfo(pass_file, user_file):
    """verify john file's content and domain users info file's format"""
    """get the user:pass from john"""
    """check if the leakTheWeak module was used on the john file"""
    compromised = {}
    with open(user_file,"r") as f:
        users = f.read().lower().splitlines()
    with open(pass_file, "r") as f:
        john = f.read().splitlines()
    # check user file content
    if users[0] != 'cn\tname\tsamaccountname\tmemberof\tprimarygroupid\twhencreated\twhenchanged\tlastlogon\tuseraccountcontrol\tpwdlastset\tobjectsid\tdescription':
        print("[!] Bad user file")
        exit(1)
    for line in users:
        if len(line.split('\t')) != 12:
            print(f"[!] Bad line in user file: {line}")
            exit(1)
    # check john file content
    for line in john:
        person = line.split(':')
        lpers = len(person)
        if lpers < 2:
            print(f"[!] Line ignored in {pass_file} file (not a valid user:password form): {line}")
            continue
        if lpers > 2:
            print(f"[!] Line used but seems to contain more than only a user:password form: {line}")
        # trick to avoid further stats over leaked hashes were password is not known
        init_reason = "leaked" if person[1]=="<LeakTheWeak>" else "undetermined"
        compromised[beautifyName(person[0])] = {"password":person[1], "groups":[], "status":[], "lastchange":"", "lastlogon":"", "robustness":3, "reason":init_reason, "priv":None}
    return users, compromised

def populateUsers(compromised, users):
    """complete info about users compromised by join using the domain users info file"""
    for i in users:
        p=i.split('\t')
        if p[2] in compromised:
                compromised[p[2]]["groups"] = p[3].split(', ')
                compromised[p[2]]["lastchange"] = p[9]
                compromised[p[2]]["lastlogon"] = p[7]
                # primary group :
                compromised[p[2]]["groups"].append(p[4])
                compromised[p[2]]["status"] = p[8].split(', ')
    # check privilege
    for acc, info in compromised.items():
        if len(info["groups"]) == 0:
            print(f"[!] {acc} not consolidated from domain users info")
        else:
            info["priv"] = isPriv(acc, info['groups'])

##############
# Robustness #
##############

def testLen(compromised, pool, trigger, rob, reason):
    """find empty passwords"""
    res = {}
    cpt = 0
    for passwd, accounts in pool.items():
        if len(passwd) <= trigger:
            for acc in accounts:
                compromised[acc]['robustness'] = rob
                compromised[acc]['reason'] = reason
                cpt += 1
        else:
            res[passwd] = accounts
    print(f"[*] {cpt} passwords found as {reason}")
    return res

def testLoginBased(compromised, pool, rob):
    """test passwords which are substring of the login or the opposite"""
    res = {}
    cpt = 0
    for passwd, accounts in pool.items():
        pl = passwd.lower()
        rest = []
        for acc in accounts:
            if pl in acc or acc in pl:
                compromised[acc]['robustness'] = rob
                compromised[acc]['reason'] = "login based"
                cpt += 1
            else:
                rest.append(acc)
        if rest:
            res[passwd] = rest
    print(f"[*] {cpt} passwords found login based")
    return res

def testIsSubstring(compromised, wordlist, pool, rob, reason):
    """test passwords which are substring of a wordlist"""
    res = {}
    cpt = 0
    f=open(wordlist)
    wl = f.read().lower()
    f.close()
    for passwd, accounts in pool.items():
        if passwd.lower() in wl:
            for acc in accounts:
                compromised[acc]['robustness'] = rob
                compromised[acc]['reason'] = reason
                cpt += 1
        else:
            res[passwd] = accounts
    print(f"[*] {cpt} passwords found as {reason}")
    return res

def testLoginExtrapolation(compromised, pool, rob):
    """test if the root of the password is included in the root of the login and the opposite"""
    res = {}
    cpt = 0
    for p in pool:
        root_p = getRoot(p)
        if len(root_p) > 2:
            rest = []
            for acc in pool[p]:
                root_n = getRoot(acc)
                if len(root_n) > 2 and (root_p in root_n or root_n in root_p):
                    compromised[acc]['robustness'] = rob
                    compromised[acc]['reason'] = "login extrapolation"
                    cpt += 1
                else:
                    rest.append(acc)
            if rest:
                res[p] = rest
        else:
            res[p] = pool[p]
    print(f"[*] {cpt} passwords found as login extrapolation")
    return res

def testWordlist(compromised, wordlist, pool, rob, reason):
    """test if a line of a wordlist match a password"""
    cpt = 0
    f=open(wordlist)
    for line in f:
        if line[:-1] in pool:
            for acc in pool[line[:-1]]:
                compromised[acc]['robustness'] = rob
                compromised[acc]['reason'] = reason
                cpt += 1
            del(pool[line[:-1]])
    f.close()
    print(f"[*] {cpt} passwords found in wordlist : {wordlist}")
    return pool

def testCharset(compromised, pool, trigger, rob, reason):
    """test how many charsets are used in the password"""
    res = {}
    cpt = 0
    for p in pool:
        if len(p) <= trigger[0] and len(getCharsets(p)) <= trigger[1] :
            for acc in pool[p]:
                compromised[acc]['robustness'] = rob
                compromised[acc]['reason'] = reason
                cpt += 1
        else:
            res[p] = pool[p]
    print(f"[*] {cpt} passwords found as {reason}")
    return res

def computeRobustness(compromised, wordlists):
    """use the previous tests over a pool of passwords to tag"""
    pool = {}
    for acc in compromised:
        if compromised[acc]['reason'] == "leaked":
            continue
        p = compromised[acc]['password']
        if p not in pool:
            pool[p] = [acc]
        else:
            pool[p].append(acc)
    # seconds
    ## empty
    pool = testLen(compromised, pool, 0, 0, "empty")
    ## login based
    pool = testLoginBased(compromised, pool, 0)
    ## top 10 common
    pool = testIsSubstring(compromised, wordlists['wl_0_top10'], pool, 0, "top 10 common")
    ## company name
    pool = testIsSubstring(compromised, wordlists['wl_0_company'], pool, 0, "company name")
    # minutes
    ## top 1000 common
    pool = testWordlist(compromised, wordlists['wl_1_top1000'], pool, 1, "top 1000 common")
    ### login extrapolation
    pool = testLoginExtrapolation(compromised, pool, 1)
    ### company context
    pool = testWordlist(compromised, wordlists['wl_1_company_context'], pool, 1, "company context related")
    ### 4 char long or less
    pool = testLen(compromised, pool, 4, 1, "4 char or less")
    # hours
    ## top 1 million common
    pool = testWordlist(compromised, wordlists['wl_2_top1M'], pool, 2, "top 1M common")
    ## 6 char or less
    pool = testLen(compromised, pool, 6, 2, "6 char or less")
    ## only 2 charsets
    pool = testCharset(compromised, pool, (10,2), 2, "2 charsets or less")
    # days
    ## all common
    pool = testWordlist(compromised, wordlists['wl_3_all'], pool, 3, "present in attack wordlist")
    ## local common
    pool = testWordlist(compromised, wordlists['wl_3_locale'], pool, 3, "present in locale attack wordlist")


##########
# Groups #
##########

def populateGroups(compromised):
    """from the view 'user -> groups compromised' to the view 'group -> users compromised'"""
    compromised_groups = {}
    for p in compromised:
        for g in compromised[p]["groups"]:
            if g == '':
                continue
            if g not in compromised_groups:
                priv = isPriv(g)
                compromised_groups[g] = {"enabled":[], "disabled":[], "robustness":3, "priv":priv}
            if "account_disabled" in compromised[p]["status"]:
                compromised_groups[g]["disabled"].append(p)
            else:
                compromised_groups[g]["enabled"].append(p)
                if compromised[p]["robustness"] < compromised_groups[g]["robustness"]:
                    compromised_groups[g]["robustness"] = compromised[p]["robustness"]
    return compromised_groups


##########
# Export #
##########

def exportUsers(compromised, output, priv):
    """write consolidated info about users into CSV format with ; separator"""
    f= open(output, "w")
    f.write("name;password;status;lastlogon;lastchange;num groups;groups;sensitive;robustness;reason\n")
    if priv:
        print("[*] Privileged accounts compromised are listed below:")
    for acc, info in compromised.items():
        psw = info['password']
        stat = 'disabled' if 'account_disabled' in info['status'] else 'enabled'
        logn = info['lastlogon']
        lchg = info['lastchange']
        numg = len(info['groups'])
        grp = ', '.join(info['groups'])
        crit = info['priv'] if info['priv'] else "unknown"
        robu = ["seconds", "minutes", "hours", "days"][info['robustness']]
        reas = info['reason']
        f.write(f"{acc};{psw};{stat};{logn};{lchg};{numg};{grp};{crit};{robu};{reas}\n")
        if priv and crit != 'unknown':
            print(f"[*]\t{stat}\t{acc}\t{psw}\t{crit}")
    f.close()

def exportGroups(compromised_groups, output):
    """write consolidated info about groups into CSV format with ; separator"""
    f= open(output, "w")
    f.write("name;num;sensitive;robustness;enabled members compromised;disabled members compromised\n")
    for gr, info in compromised_groups.items():
        memb = len(info['disabled']) + len(info['enabled'])
        crit = info['priv'] if info['priv'] else "unknown"
        robu = ["seconds", "minutes", "hours", "days"][info['robustness']]
        emem = ', '.join(info['enabled'])
        dmem = ', '.join(info['disabled'])
        f.write(f"{gr};{memb};{crit};{robu};{emem};{dmem}\n")
    f.close()


#########
# Stats #
#########


def getPass(compromised):
    """just create a dict with two lists: one for all the acounts, another for the active accounts only"""
    passwords = {"all":[], "active":[]}
    for c in compromised:
        if compromised[c]['reason'] == 'leaked':
            continue
        passwords["all"].append(compromised[c]['password'])
        if 'account_disabled' not in compromised[c]['status']:
            passwords["active"].append(compromised[c]['password'])
    return passwords

def statSynthesis(users, compromised):
    """produce data for synthesis stats"""
    total = len(users)-1
    unsafe = 0
    active_unsafe = 0
    for i in compromised:
        if compromised[i]['reason'] == 'leaked':
            unsafe += 1
            if 'account_disabled' not in compromised[i]['status']:
                active_unsafe += 1
    cracked = len(compromised) - unsafe
    safe = total - cracked - unsafe
    active_total = 0
    for i in users:
        if 'account_disabled' not in i.split('\t')[8]:
            active_total += 1
    active_cracked = 0 - active_unsafe
    for i in compromised:
        if 'account_disabled' not in compromised[i]['status']:
            active_cracked += 1
    active_safe = active_total - active_cracked - active_unsafe
    return (total, cracked, safe, active_total, active_cracked, active_safe, unsafe, active_unsafe)

def statUniq(passwords):
    """produce data about unicity stats"""
    empty_a = passwords["active"].count('')
    non_empty_a = len(passwords["active"]) - empty_a
    uniq_a = len(set(passwords["active"]))
    empty = passwords["all"].count('')
    non_empty = len(passwords["all"]) - empty
    uniq = len(set(passwords["all"]))
    return (empty, non_empty, uniq, empty_a, non_empty_a, uniq_a)

def statSensitive(compromised):
    """produce data about the privilege of the users"""
    crit = {"all": {"likely":{}, "admin": {}}, "active": {"likely":{}, "admin": {}}}
    for u in compromised:
        if compromised[u]['priv'] :
            if 'likely' in compromised[u]['priv']:
                crit['all']['likely'][u] = (compromised[u]['robustness'], compromised[u]['reason'])
                if 'account_disabled' not in compromised[u]["status"]:
                    crit['active']['likely'][u] = (compromised[u]['robustness'], compromised[u]['reason'])
            else:
                crit['all']['admin'][u] = (compromised[u]['robustness'], compromised[u]['reason'])
                if 'account_disabled' not in compromised[u]["status"]:
                    crit['active']['admin'][u] = (compromised[u]['robustness'], compromised[u]['reason'])
    return crit

def statLength(passwords):
    """produce data for length stats"""
    lengths = {"all":[0]*16, "active":[0]*16}
    for p in passwords["all"]:
        l = len(p)
        if l >= 15:
            lengths["all"][15] += 1
        else:
            lengths["all"][l] += 1
    for p in passwords["active"]:
        l = len(p)
        if l >= 15:
            lengths["active"][15] += 1
        else:
            lengths["active"][l] += 1
    return lengths

def statCharset(passwords):
    """produce data for charset stats"""
    cs = {'':0,
        'l':0, 'u':0, 'd':0, 'p':0,
        'lu':0, 'ld':0, 'lp':0, 'ud':0, 'up':0, 'dp':0,
        'lud':0, 'lup':0, 'ldp':0, 'udp':0,
        'ludp':0}
    charsets = {"all": dict(cs), "active": dict(cs)}
    for p in passwords["active"]:
        c = getCharsets(p)
        charsets['active'][c] +=1
    for p in passwords["all"]:
        c = getCharsets(p)
        charsets['all'][c] +=1
    return charsets

def statFreq(passwords):
    """produce data for most frequent passwords stats"""
    occ = {"all": None, "active": None}
    occ["all"] = Counter(passwords["all"])
    occ["active"] = Counter(passwords["active"])
    return occ

def statPattern(passwords):
    """produce data for most frequent patterns stats"""
    patterns = {"all": {}, "active": {}}
    digit_isolation = str.maketrans('', '', string.ascii_letters+string.punctuation)
    for field in patterns.keys():
        for p in passwords[field]:
            r = getRoot(p)
            d = p.translate(digit_isolation)
            if len(r) > 3 :
                if r not in patterns[field]:
                    patterns[field][r] = 0
                patterns[field][r] += 1
            if len(d) > 1 :
                if d not in patterns[field]:
                    patterns[field][d] = 0
                patterns[field][d] += 1
    return patterns

def statRobustness(compromised, status):
    """produce data for robustness stats"""
    rob = {0:{"empty":0, "login based":0, "top 10 common":0, "company name":0},
            1:{"top 1000 common":0, "login extrapolation":0, "company context related":0, "4 char or less":0},
            2:{"top 1M common":0, "6 char or less":0, "2 charsets or less":0},
            3:{"present in attack wordlist":0, "present in locale attack wordlist":0, "leaked":0, "undetermined":0}}
    for acc in compromised:
        if status == 'all' or 'account_disabled' not in compromised[acc]["status"]:
            rob[compromised[acc]["robustness"]][compromised[acc]["reason"]] += 1
    return rob

def produceStats(output, users, compromised):
    """ write the stats to a file"""
    f = open(output,"w")
    f.write("total accounts;"\
           "compromised accounts;"\
           "unsafe accounts;"\
           "safe accounts;"\
           "total accounts (active);"\
           "compromised accounts (active);"\
           "unsafe active accounts (active);"\
           "safe active accounts (active);"\
           "unique passwords compromised;"\
           "unique passwords compromised (active);"\
           "likely sensitive users compromised;"\
           "firm sensitive users compromised;"\
           "likely sensitive users compromised (active);"\
           "firm sensitive users compromised (active);"\
           "password length 0;"\
           "password length 1;"\
           "password length 2;"\
           "password length 3;"\
           "password length 4;"\
           "password length 5;"\
           "password length 6;"\
           "password length 7;"\
           "password length 8;"\
           "password length 9;"\
           "password length 10;"\
           "password length 11;"\
           "password length 12;"\
           "password length 13;"\
           "password length 14;"\
           "password length 15 or more;"\
           "password length 0 (active);"\
           "password length 1 (active);"\
           "password length 2 (active);"\
           "password length 3 (active);"\
           "password length 4 (active);"\
           "password length 5 (active);"\
           "password length 6 (active);"\
           "password length 7 (active);"\
           "password length 8 (active);"\
           "password length 9 (active);"\
           "password length 10 (active);"\
           "password length 11 (active);"\
           "password length 12 (active);"\
           "password length 13 (active);"\
           "password length 14 (active);"\
           "password length 15 or more (active);"\
           "passwords with 1 charset;"\
           "passwords with 2 charsets;"\
           "passwords with 3 charsets;"\
           "passwords all the charsets;"\
           "passwords with 1 charset (active);"\
           "passwords with 2 charsets (active);"\
           "passwords with 3 charsets (active);"\
           "passwords all the charsets (active);"\
           "empty passwords;"\
           "lowercase passwords;"\
           "uppercase passwords;"\
           "digit passwords;"\
           "punctuation passwords;"\
           "lower-upper passwords;"\
           "lower-digit passwords;"\
           "lower-punct passwords;"\
           "upper-digit passwords;"\
           "upper-punct passwords;"\
           "digit-punct passwords;"\
           "lower-upper-digit passwords;"\
           "lower-upper-punct passwords;"\
           "lower-digit-punct passwords;"\
           "upper-digit-punct passwords;"\
           "lower-upper-digit-punct passwords;"\
           "empty passwords (active);"\
           "lowercase passwords (active);"\
           "uppercase passwords (active);"\
           "digit passwords (active);"\
           "punctuation passwords (active);"\
           "lower-upper passwords (active);"\
           "lower-digit passwords (active);"\
           "lower-punct passwords (active);"\
           "upper-digit passwords (active);"\
           "upper-punct passwords (active);"\
           "digit-punct passwords (active);"\
           "lower-upper-digit passwords (active);"\
           "lower-upper-punct passwords (active);"\
           "lower-digit-punct passwords (active);"\
           "upper-digit-punct passwords (active);"\
           "lower-upper-digit-punct passwords (active);"\
           "1st frequent password;"\
           "2nd frequent password;"\
           "3rd frequent password;"\
           "4th frequent password;"\
           "5th frequent password;"\
           "6th frequent password;"\
           "7th frequent password;"\
           "8th frequent password;"\
           "9th frequent password;"\
           "10th frequent password;"\
           "1st password occurrence;"\
           "2nd password occurrence;"\
           "3rd password occurrence;"\
           "4th password occurrence;"\
           "5th password occurrence;"\
           "6th password occurrence;"\
           "7th password occurrence;"\
           "8th password occurrence;"\
           "9th password occurrence;"\
           "10th password occurrence;"\
           "1st frequent password (active);"\
           "2nd frequent password (active);"\
           "3rd frequent password (active);"\
           "4th frequent password (active);"\
           "5th frequent password (active);"\
           "6th frequent password (active);"\
           "7th frequent password (active);"\
           "8th frequent password (active);"\
           "9th frequent password (active);"\
           "10th frequent password (active);"\
           "1st password occurrence (active);"\
           "2nd password occurrence (active);"\
           "3rd password occurrence (active);"\
           "4th password occurrence (active);"\
           "5th password occurrence (active);"\
           "6th password occurrence (active);"\
           "7th password occurrence (active);"\
           "8th password occurrence (active);"\
           "9th password occurrence (active);"\
           "10th password occurrence (active);"\
           "1rst frequent pattern;"\
           "2nd frequent pattern;"\
           "3rd frequent pattern;"\
           "4th frequent pattern;"\
           "5th frequent pattern;"\
           "6th frequent pattern;"\
           "7th frequent pattern;"\
           "8th frequent pattern;"\
           "9th frequent pattern;"\
           "10th frequent pattern;"\
           "1st pattern occurrence;"\
           "2nd pattern occurrence;"\
           "3rd pattern occurrence;"\
           "4th pattern occurrence;"\
           "5th pattern occurrence;"\
           "6th pattern occurrence;"\
           "7th pattern occurrence;"\
           "8th pattern occurrence;"\
           "9th pattern occurrence;"\
           "10th pattern occurrence;"\
           "1st frequent pattern (active);"\
           "2nd frequent pattern (active);"\
           "3rd frequent pattern (active);"\
           "4th frequent pattern (active);"\
           "5th frequent pattern (active);"\
           "6th frequent pattern (active);"\
           "7th frequent pattern (active);"\
           "8th frequent pattern (active);"\
           "9th frequent pattern (active);"\
           "10th frequent pattern (active);"\
           "1st pattern occurrence (active);"\
           "2nd pattern occurrence (active);"\
           "3rd pattern occurrence (active);"\
           "4th pattern occurrence (active);"\
           "5th pattern occurrence (active);"\
           "6th pattern occurrence (active);"\
           "7th pattern occurrence (active);"\
           "8th pattern occurrence (active);"\
           "9th pattern occurrence (active);"\
           "10th pattern occurrence (active);"\
           "passwords resist some seconds;"\
           "passwords resist some minutes;"\
           "passwords resist some hours;"\
           "passwords resist some days;"\
           "passwords resist some years;"\
           "passwords resist some seconds (active);"\
           "passwords resist some minutes (active);"\
           "passwords resist some hours (active);"\
           "passwords resist some days (active);"\
           "passwords resist some years (active);"\
           "passwords empty;"\
           "passwords based on username;"\
           "passwords in top 10 most common;"\
           "passwords based on company name;"\
           "passwords in top 1000 most common;"\
           "passwords as username extrapolation;"\
           "passwords related to company context;"\
           "passwords with 4 characters or less;"\
           "passwords in top 1M most common;"\
           "passwords with 6 characters or less;"\
           "passwords with 2 charsets or less;"\
           "passwords present in global wordlists;"\
           "passwords present in locale wordlists;"\
           "passwords leaked;"\
           "passwords weakness undetermined;"\
           "passwords empty (active);"\
           "passwords based on username (active);"\
           "passwords in top 10 most common (active);"\
           "passwords based on company name (active);"\
           "passwords in top 1000 most common (active);"\
           "passwords as username extrapolation (active);"\
           "passwords related to company context (active);"\
           "passwords with 4 characters or less (active);"\
           "passwords in top 1M most common (active);"\
           "passwords with 6 characters or less (active);"\
           "passwords with 2 charsets or less (active);"\
           "passwords present in global wordlists (active);"\
           "passwords present in locale wordlists (active);"\
           "passwords leaked (active);"\
           "passwords weakness undetermined (active)\n")
    passwords = getPass(compromised)

    # synthesis
    synth = statSynthesis(users, compromised)
    f.write(f"{synth[0]};{synth[1]};{synth[6]};{synth[2]};"\
            f"{synth[3]};{synth[4]};{synth[7]};{synth[5]};")

    # unicity
    unicity = statUniq(passwords)
    f.write(f"{unicity[2]};{unicity[5]};")

    # Sensitive
    crit = statSensitive(compromised)
    f.write(f"{len(crit['all']['likely']) + len(crit['all']['admin'])};")
    f.write(f"{len(crit['all']['admin'])};")
    f.write(f"{len(crit['active']['likely']) + len(crit['active']['admin'])};")
    f.write(f"{len(crit['active']['admin'])};")

    # lengths:
    lengths = statLength(passwords)
    for i in range(16):
        f.write(f"{lengths['all'][i]};")
    for i in range(16):
        f.write(f"{lengths['active'][i]};")

    # charset
    charsets = statCharset(passwords)
    f.write(f"{charsets['all'][''] + charsets['all']['l'] + charsets['all']['u'] + charsets['all']['d'] + charsets['all']['p']};")
    f.write(f"{charsets['all']['lu'] + charsets['all']['ld'] + charsets['all']['lp'] + charsets['all']['ud'] + charsets['all']['up'] + charsets['all']['dp']};")
    f.write(f"{charsets['all']['lud'] + charsets['all']['lup'] + charsets['all']['ldp'] + charsets['all']['udp']};")
    f.write(f"{charsets['all']['ludp']};")
    f.write(f"{charsets['active'][''] + charsets['active']['l'] + charsets['active']['u'] + charsets['active']['d'] + charsets['active']['p']};")
    f.write(f"{charsets['active']['lu'] + charsets['active']['ld'] + charsets['active']['lp'] + charsets['active']['ud'] + charsets['active']['up'] + charsets['active']['dp']};")
    f.write(f"{charsets['active']['lud'] + charsets['active']['lup'] + charsets['active']['ldp'] + charsets['active']['udp']};")
    f.write(f"{charsets['active']['ludp']};")
    f.write(f"{charsets['all']['']};{charsets['all']['l']};{charsets['all']['u']};{charsets['all']['d']};{charsets['all']['p']};{charsets['all']['lu']};{charsets['all']['ld']};{charsets['all']['lp']};{charsets['all']['ud']};{charsets['all']['up']};{charsets['all']['dp']};{charsets['all']['lud']};{charsets['all']['lup']};{charsets['all']['ldp']};{charsets['all']['udp']};{charsets['all']['ludp']};")
    f.write(f"{charsets['active']['']};{charsets['active']['l']};{charsets['active']['u']};{charsets['active']['d']};{charsets['active']['p']};{charsets['active']['lu']};{charsets['active']['ld']};{charsets['active']['lp']};{charsets['active']['ud']};{charsets['active']['up']};{charsets['active']['dp']};{charsets['active']['lud']};{charsets['active']['lup']};{charsets['active']['ldp']};{charsets['active']['udp']};{charsets['active']['ludp']};")

    # freq
    occ = statFreq(passwords)
    occ_all = sorted(occ["all"].items(), key=lambda x: x[1], reverse=True)
    l = len(occ_all)
    for i in range(10):
        f.write([";", f"{occ_all[i][0]};"][i<l])
    for i in range(10):
        f.write([";", f"{occ_all[i][1]};"][i<l])
    occ_act = sorted(occ["active"].items(), key=lambda x: x[1], reverse=True)
    l = len(occ_act)
    for i in range(10):
        f.write([";", f"{occ_act[i][0]};"][i<l])
    for i in range(10):
        f.write([";", f"{occ_act[i][1]};"][i<l])

    # pattern
    patterns = statPattern(passwords)
    pat_all = sorted(patterns["all"].items(), key=lambda x: x[1], reverse=True)
    l = len(pat_all)
    for i in range(10):
        f.write([";", f"{pat_all[i][0]};"][i<l])
    for i in range(10):
        f.write([";", f"{pat_all[i][1]};"][i<l])
    pat_act = sorted(patterns["active"].items(), key=lambda x: x[1], reverse=True)
    l = len(pat_act)
    for i in range(10):
        f.write([";", f"{pat_act[i][0]};"][i<l])
    for i in range(10):
        f.write([";", f"{pat_act[i][1]};"][i<l])

    # robustness
    rob_all = statRobustness(compromised, 'all')
    rob_act = statRobustness(compromised, 'active')
    f.write(f"{sum(rob_all[0].values())};{sum(rob_all[1].values())};{sum(rob_all[2].values())};{sum(rob_all[3].values())};{synth[2]};")
    f.write(f"{sum(rob_act[0].values())};{sum(rob_act[1].values())};{sum(rob_act[2].values())};{sum(rob_act[3].values())};{synth[5]};")
    f.write(f"{rob_all[0]['empty']};{rob_all[0]['login based']};{rob_all[0]['top 10 common']};{rob_all[0]['company name']};"\
        f"{rob_all[1]['top 1000 common']};{rob_all[1]['login extrapolation']};{rob_all[1]['company context related']};{rob_all[1]['4 char or less']};"\
        f"{rob_all[2]['top 1M common']};{rob_all[2]['6 char or less']};{rob_all[2]['2 charsets or less']};"\
        f"{rob_all[3]['present in attack wordlist']};{rob_all[3]['present in locale attack wordlist']};{rob_all[3]['leaked']};{rob_all[3]['undetermined']};")
    f.write(f"{rob_act[0]['empty']};{rob_act[0]['login based']};{rob_act[0]['top 10 common']};{rob_act[0]['company name']};"\
        f"{rob_act[1]['top 1000 common']};{rob_act[1]['login extrapolation']};{rob_act[1]['company context related']};{rob_act[1]['4 char or less']};"\
        f"{rob_act[2]['top 1M common']};{rob_act[2]['6 char or less']};{rob_act[2]['2 charsets or less']};"\
        f"{rob_act[3]['present in attack wordlist']};{rob_act[3]['present in locale attack wordlist']};{rob_act[3]['leaked']};{rob_act[3]['undetermined']}")
    f.close()

def main():
    parser = argparse.ArgumentParser(description='Analysis of cracked domain accounts', add_help=True)
    parser.add_argument('JOHN_FILE', action="store",
            help="The cracked passwords by john (john --show command)")
    parser.add_argument('USERS_FILE', action="store",
            help="The file containing the Domain users info (from ldapdomaindump: domain_users.grep)")
    parser.add_argument('--wordlists', action="store", dest="wpath", default=None,
            help='Specify a path to the wordlists for robustness analysis')
    parser.add_argument('--priv', action="store_true", default=False,
            help='Specify that you want to display the list of enabled privileged users at the end of the process')
    parser.add_argument('--stats', action="store_true", default=False,
            help='Compute stats about the passwords. Stored in lestat.csv')
    args = parser.parse_args()

    user_out = "users_compromised.csv"
    group_out = "group_compromised.csv"
    spath = "lestat.csv"

    print(f"[*] Importing john result from {args.JOHN_FILE} and domain info from {args.USERS_FILE}")
    users, cu = initInfo(args.JOHN_FILE, args.USERS_FILE)
    populateUsers(cu, users)
    if args.wpath:
        print("[*] Computing robustness, could be long if the wordlists are huge...")
        wordlists = {}
        wordlists['wl_0_top10'] = args.wpath+"/wl_0_top10.txt"
        wordlists['wl_0_company'] = args.wpath+"/wl_0_company_name.txt"
        wordlists['wl_1_top1000'] = args.wpath+"/wl_1_top1000.txt"
        wordlists['wl_1_company_context'] = args.wpath+"/wl_1_company_context_related.txt"
        wordlists['wl_2_top1M'] = args.wpath+"/wl_2_top1M.txt"
        wordlists['wl_3_all'] = args.wpath+"/wl_3_all_common.txt"
        wordlists['wl_3_locale'] = args.wpath+"/wl_3_locale_common.txt"
        computeRobustness(cu, wordlists)
    print("[*] Computing groups information")
    cg = populateGroups(cu)
    print(f"[*] Exporting data to {user_out} and {group_out}")
    exportUsers(cu, user_out, args.priv)
    exportGroups(cg, group_out)
    if args.stats:
        print(f"[*] Computing stats and exporting to lestat.csv")
        produceStats(spath, users, cu)

if __name__ == '__main__':
    main()
