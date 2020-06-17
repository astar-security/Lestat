#!/usr/bin/python3

import string
import argparse

#########
# Const #
#########

PRIVILEGED_GROUPS = [
        "admins du domaine",
        "administrateurs du schéma",
        "administrateurs de l’entreprise",
        "administrateurs",
        "propriétaires créateurs de la stratégie de groupe"
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
        cs += 'n'
    if any([i for i in passwd if i in string.punctuation]):
        cs += 's'
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
    f.write("name;num;sensitive;robustness;enabled members;disabled members\n")
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

def statUniq(passwords, active_or_all):
    """produce data about unicity stats"""
    empty = passwords[active_or_all].count('')
    non_empty = len(passwords[active_or_all]) - empty
    uniq = len(set(passwords[active_or_all]))
    return (empty, non_empty, uniq)

def statSensitive(compromised, active_or_all):
    """produce data about the privilege of the users"""
    crit = {}
    for u in compromised:
        if active_or_all == "all" or 'account_disabled' not in compromised[u]["status"]:
            if compromised[u]['priv'] :
                if 'likely' in compromised[u]['priv']:
                    crit[u] = ('likely', compromised[u]['robustness'], compromised[u]['reason'])
                else:
                    crit[u] = ('admin', compromised[u]['robustness'], compromised[u]['reason'])
    return crit

def statLength(passwords, active_or_all):
    """produce data for length stats"""
    lengths = {}
    for p in passwords[active_or_all]:
        l = len(p)
        if l not in lengths:
            lengths[l] = 0
        lengths[l] += 1
    return lengths

def statCharset(passwords, active_or_all):
    """produce data for charset stats"""
    charsets = {'':0, 'l':0, 'u':0, 'n':0, 's':0, 'lu':0, 'ln':0, 'ls':0, 'un':0, 'us':0, 'ns':0, 'lun':0, 'lus':0, 'lns':0, 'uns':0, 'luns':0}
    for p in passwords[active_or_all]:
        c = getCharsets(p)
        charsets[c] +=1
    return charsets

def statFreq(passwords, active_or_all):
    """produce data for most frequent passwords stats"""
    occ = {}
    for p in set(passwords[active_or_all]):
        o = passwords[active_or_all].count(p)
        occ[p] = o
    return occ

def statPattern(passwords, active_or_all):
    """produce data for most frequent patterns stats"""
    patterns = {}
    digit_isolation = str.maketrans('', '', string.ascii_letters+string.punctuation)
    for p in passwords[active_or_all]:
        r = getRoot(p)
        d = p.translate(digit_isolation)
        if len(r) > 3 :
            if r not in patterns:
                patterns[r] = 0
            patterns[r] += 1
        if len(d) > 1 :
            if d not in patterns:
                patterns[d] = 0
            patterns[d] += 1
    return patterns

def statRobustness(compromised, active_or_all):
    """produce data for robustness stats"""
    rob = {0:{"empty":0, "login based":0, "top 10 common":0, "company name":0},
            1:{"top 1000 common":0, "login extrapolation":0, "company context related":0, "4 char or less":0},
            2:{"top 1M common":0, "6 char or less":0, "2 charsets or less":0},
            3:{"present in attack wordlist":0, "present in locale attack wordlist":0, "leaked":0, "undetermined":0}}
    for acc in compromised:
        if active_or_all == "all" or 'account_disabled' not in compromised[acc]["status"]:
            rob[compromised[acc]["robustness"]][compromised[acc]["reason"]] += 1
    return rob

def produceStats(output, users, compromised, active_or_all, trigger_freq, trigger_pat):
    """ write the stats to a file"""
    f = open(output,"w")
    passwords = getPass(compromised)
    # synthesis
    synth = statSynthesis(users, compromised)
    f.write("\n# Synthesis\n\n")
    f.write(f"accounts:{synth[0]}:100%\n")
    f.write(f"-compromised accounts:{synth[1]}:{round(100*synth[1]/synth[0],1)}%\n")
    f.write(f"-unsafe accounts (leaked):{synth[6]}:{round(100*synth[6]/synth[0],1)}%\n")
    f.write(f"-safe accounts:{synth[2]}:{round(100*synth[2]/synth[0],1)}%\n")
    f.write("\n## Active accounts only\n\n")
    f.write(f"-active accounts:{synth[3]}:{round(100*synth[3]/synth[0],1)}%\n")
    f.write(f"--which are compromised:{synth[4]}:{round(100*synth[4]/synth[3],1)}%\n")
    f.write(f"--which are unsafe:{synth[7]}:{round(100*synth[7]/synth[3],1)}%\n")
    f.write(f"--which are safe:{synth[5]}:{round(100*synth[5]/synth[3],1)}%\n")
    # unicity
    unicity = statUniq(passwords, active_or_all)
    f.write(f"\n# Diversity about {active_or_all} accounts\n\n")
    f.write(f"empty passwords:{unicity[0]}:{round(100*unicity[0]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"non empty passwords:{unicity[1]}:{round(100*unicity[1]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"unique passwords:{unicity[2]}:{round(100*unicity[2]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    # Sensitive
    crit = statSensitive(compromised, active_or_all)
    tot_crit = len(crit)
    f.write(f"\n# Sensitive users in {active_or_all} accounts\n\n")
    f.write(f"total:{tot_crit}:{round(100*tot_crit/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write("account:sensitive:robustness:reason\n")
    for u in crit:
        f.write(f"{u}:{crit[u][0]}:{['seconds','minutes','hours','days'][crit[u][1]]}:{crit[u][2]}\n")
    # lengths:
    lengths = statLength(passwords, active_or_all)
    f.write(f"\n# Lenghts for {active_or_all} accounts\n\n")
    for i in range(max(lengths.keys())+1):
        if i in lengths:
            f.write(f"{i}:{lengths[i]}:{round(100*lengths[i]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
        else:
            f.write(f"{i}:0:0%\n")
    # charset
    charsets = statCharset(passwords, active_or_all)
    one_charset = charsets[''] + charsets['l'] + charsets['u'] + charsets['n'] + charsets['s']
    two_charset = charsets['lu'] + charsets['ln'] + charsets['ls'] + charsets['un'] + charsets['us'] + charsets['ns']
    three_charset = charsets['lun'] + charsets['lus'] + charsets['lns'] + charsets['uns']
    f.write(f"\n# Charsets analysis for {active_or_all} accounts\n\n")
    f.write(f"Only 1 charset:{one_charset}:{round(100*one_charset/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"2 different charsets:{two_charset}:{round(100*two_charset/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"3 different charsets:{three_charset}:{round(100*three_charset/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"All the charsets:{charsets['luns']}:{round(100*charsets['luns']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n\n")
    f.write("Composition:Lowercase:Uppercase:Digits:Punctuation:Score:%\n")
    f.write(f"Empty:::::{charsets['']}:{round(100*charsets['']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerOnly:X::::{charsets['l']}:{round(100*charsets['l']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"UpperOnly::X:::{charsets['u']}:{round(100*charsets['u']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"NumOnly:::X::{charsets['n']}:{round(100*charsets['n']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"PuncOnly::::X:{charsets['s']}:{round(100*charsets['s']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerUpper:X:X:::{charsets['lu']}:{round(100*charsets['lu']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerNum:X::X::{charsets['ln']}:{round(100*charsets['ln']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerPunc:X:::X:{charsets['ls']}:{round(100*charsets['ls']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"UpperNum::X:X::{charsets['un']}:{round(100*charsets['un']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"UpperPunc::X::X:{charsets['us']}:{round(100*charsets['us']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"NumPunc:::X:X:{charsets['ns']}:{round(100*charsets['ns']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerUpperNum:X:X:X::{charsets['lun']}:{round(100*charsets['lun']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerUpperPunc:X:X::X:{charsets['lus']}:{round(100*charsets['lus']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"LowerNumPunc:X::X:X:{charsets['lns']}:{round(100*charsets['lns']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"UpperNumPunc::X:X:X:{charsets['uns']}:{round(100*charsets['uns']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    f.write(f"All:X:X:X:X:{charsets['luns']}:{round(100*charsets['luns']/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    # freq
    occ = statFreq(passwords, active_or_all)
    f.write(f"\n# Passwords frequency analysis for {active_or_all} accounts\n\n")
    for p in sorted(occ.items(), key=lambda x: x[1], reverse=True):
        if p[1] >= trigger_freq:
            f.write(f"{p[0]}:{p[1]}:{round(100*p[1]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    # pattern
    patterns = statPattern(passwords, active_or_all)
    f.write(f"\n# Patterns frequency analysis for {active_or_all} accounts\n\n")
    for p in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        if p[1] >= trigger_pat:
            f.write(f"{p[0]}:{p[1]}:{round(100*p[1]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
    # robustness
    rob = statRobustness(compromised, active_or_all)
    seco = sum(rob[0].values())
    minu = sum(rob[1].values())
    hour = sum(rob[2].values())
    days = sum(rob[3].values())
    year = [synth[2],synth[5]][active_or_all=='active']
    f.write(f"\n# Passwords ({active_or_all}) robustness against hacker\n\n")
    f.write("Time before being cracked:num:%\n")
    f.write(f"seconds:{seco}:{round(100*seco/[synth[0],synth[3]][active_or_all=='active'],1)}%\n")
    f.write(f"minutes:{minu}:{round(100*minu/[synth[0],synth[3]][active_or_all=='active'],1)}%\n")
    f.write(f"hours:{hour}:{round(100*hour/[synth[0],synth[3]][active_or_all=='active'],1)}%\n")
    f.write(f"days:{days}:{round(100*days/[synth[0],synth[3]][active_or_all=='active'],1)}%\n")
    f.write(f"years:{year}:{round(100*year/[synth[0],synth[3]][active_or_all=='active'],1)}%\n")
    f.write("\nReasons:num:%\n")
    for r in rob:
        for reason in rob[r]:
            f.write(f"{reason}:{rob[r][reason]}:{round(100*rob[r][reason]/[synth[1],synth[4]][active_or_all=='active'],1)}%\n")
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
    parser.add_argument('--all', action="store_true", default=False,
            help='Specify that you want passwords stats about all the accounts and not ENABLED ones only')
    parser.add_argument('--stats', action="store", dest="spath", default=None,
            help='Specify a filename for the passwords stats results')
    args = parser.parse_args()

    user_out = "users_compromised.csv"
    group_out = "group_compromised.csv"

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
    if args.spath:
        print(f"[*] Computing stats and exporting to {args.spath}")
        filt = "all" if args.all else "active"
        produceStats(args.spath, users, cu, filt, 2, 3)

if __name__ == '__main__':
    main()

