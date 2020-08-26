#!/usr/bin/python3

import string
import argparse
import csv
import matplotlib.pyplot as plt
from collections import Counter
from termcolor import colored

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
    if priv :
        print("[*] Privileged accounts compromised are listed below:")
    with open(output, 'w') as f:
        w = None
        for acc, info in compromised.items() :
            user = {"name": acc}
            user['password'] = info['password']
            user['status'] = 'disabled' if 'account_disabled' in info['status'] else 'enabled'
            user['lastlogon'] = info['lastlogon']
            user['lastchange'] = info['lastchange']
            user['num groups'] = len( info['groups'] )
            user['groups'] = ', '.join( info['groups'] )
            user['sensitive'] = info['priv'] if info['priv'] else "unknown"
            user['robustness'] = ["seconds", "minutes", "hours", "days"][info['robustness']]
            user['reason'] = info['reason']
            if priv and user['sensitive'] != 'unknown':
                c = "magenta"
                if user['status'] == "enabled":
                    c = "white" if user['sensitive'] == "likely admin" else "red"
                print(colored(f"[+]\t{user['status'].ljust(12)} {user['sensitive'].ljust(20)} {user['name'].ljust(24)} {user['password']}", c))

            if not w:
                w = csv.DictWriter(f, user.keys(), delimiter=";")
                w.writeheader()
            w.writerow(user)

def exportGroups(compromised_groups, output):
    """write consolidated info about groups into CSV format with ; separator"""
    with open(output, 'w') as f:
        w = None
        for gr, info in compromised_groups.items() :
            group = {"name": gr}
            group['members compromised'] = len( info['disabled'] ) + len( info['enabled'] )
            group['sensitive'] = info['priv'] if info['priv'] else "unknown"
            group['robustness'] = ["seconds", "minutes", "hours", "days"][info['robustness']]
            group['enabled members compromised'] = ', '.join( info['enabled'] )
            group['disabled members compromised'] = ', '.join( info['disabled'] )

            if not w:
                w = csv.DictWriter(f, group.keys(), delimiter=";")
                w.writeheader()
            w.writerow(group)

def exportStats(stats, spath):
    """write stats to a csv file with ; separator"""
    with open(spath, 'w') as f:
        w = csv.DictWriter(f, stats[0].keys(), delimiter=";")
        w.writeheader()
        for stat in stats :
            w.writerow(stat)

def exportCharts(st, chartpath, wordlist):
    """produce charts in PNG format"""
    # used to maintain the same scale between all accounts and active only
    max_length = 0
    max_top = 0
    max_top_p = 0
    max_charset = 0
    for field in st:
        name = field['field']
        
        # main chart
        fig, ax = plt.subplots()
        values = [ field['compromised accounts'], field['safe accounts'] ]
        labels = [ 'compromised accounts', 'safe accounts' ]
        colors = [ '#dd0000', '#00c800' ]
        if field['unsafe accounts'] != 0 :
            values.append( field['unsafe accounts'] )
            labels.append( 'unsafe accounts' )
            colors.append( '#ff0000' )
        ax.pie(values, labels=labels, colors=colors, autopct=lambda p : '{:,.0f}% ({:,.0f})'.format(p,p * sum(values)/100), wedgeprops={"edgecolor":"white",'linewidth': 1, 'linestyle': 'solid', 'antialiased': True} )
        ax.set_title(f"Overall results for {name}")
        plt.tight_layout()
        plt.savefig(f"main_{name}.png", bbox_inches="tight", transparent=True)

        # reason of compromise
        if wordlist:
            fig, ax = plt.subplots()
            reasons = [('passwords empty', '#bb0000'), 
                ('passwords based on username', '#bb0000'),
                ('passwords in top 10 most common', '#bb0000'),
                ('passwords based on company name', '#bb0000'),
                ('passwords in top 1000 most common', '#ff0000'),
                ('passwords as username extrapolation', '#ff0000'),
                ('passwords related to company context', '#ff0000'),
                ('passwords with 4 characters or less', '#ff0000'),
                ('passwords in top 1M most common', '#ff6400'),
                ('passwords with 6 characters or less', '#ff6400'),
                ('passwords with 2 charsets or less', '#ff6400'),
                ('passwords present in global wordlists', '#ffc800'),
                ('passwords present in locale wordlists', '#ffc800'),
                ('passwords leaked', '#ffc800'),
                ('passwords weakness undetermined', '#ffc800')]
            values = []
            labels = []
            colors = []
            for r in reasons:
                if field[r[0]] / (field['compromised accounts']+field['unsafe accounts'])*100 >=1:
                    values.append( field[r[0]] )
                    labels.append( r[0][9:] )
                    colors.append( r[1] )
            ax.pie(values, labels=labels, colors=colors, autopct='%1i%%', wedgeprops={"edgecolor":"white",'linewidth': 1, 'linestyle': 'solid', 'antialiased': True} )
            ax.set_title(f"Reasons of weakness for {name}")
            plt.tight_layout()
            plt.savefig(f"weaknesses_{name}.png", bbox_inches='tight', transparent=True)

        # cracked passwords by charset
        fig, ax = plt.subplots()
        values = [ field['passwords with 1 charset'], field['passwords with 2 charsets'], field['passwords with 3 charsets'], field['passwords with all charsets']]
        if max_charset == 0:
            max_charset = max(values)
        ax.barh('1 charset', field['passwords with 1 charset'], color='#ff0000')
        ax.barh('2 charsets', field['passwords with 2 charsets'], color='#ff6400')
        ax.barh('3 charsets', field['passwords with 3 charsets'], color='#ffc800')
        ax.barh('all charsets', field['passwords with all charsets'], color='#00c800')
        ax.set_title(f"Cracked passwords by charset ({name})")
        plt.xlim(0, max_charset +10)
        for ind, val in enumerate(values):
            plt.text(val, ind, str(val), ha="left", va="center")
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.savefig(f"pass_by_charset_{name}.png", bbox_inches="tight", transparent=True) 

        # cracked passwords by length
        fig, ax = plt.subplots()
        values = []
        labels = []
        for i in range(15):
            values.append( field[f"password length {i}"] )
            labels.append( str(i) )
        values.append( field['password length 15 or more'] )
        if max_length == 0:
            max_length = max(values)
        labels.append('15+')
        ax.bar(labels[0], values[0], color='#bb0000')
        ax.bar(labels[1:5], values[1:5], color='#ff0000')
        ax.bar(labels[5:8], values[5:8], color='#ff6400')
        ax.bar(labels[8:13], values[8:13], color='#ffc800')
        ax.bar(labels[13:], values[13:], color='#00c800')
        ax.set_title(f"Cracked passwords per length ({name})")
        plt.ylim(0, max_length +10)
        for ind, val in enumerate(values):
            plt.text(ind, val, str(val), ha="center", va="bottom")
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.savefig(f"pass_by_length_{name}.png", bbox_inches="tight", transparent=True)
        
        # robustness
        if wordlist:
            fig, ax = plt.subplots()
            resist = [ 'passwords resist some seconds', 
                        'passwords resist some minutes', 
                        'passwords resist some hours',
                        'passwords resist some days',
                        'passwords resist some years' ]
            start = [ 0, field[resist[0]] ]
            ax.barh( [""], [ field[resist[0]] ], height=0.1, color='#bb0000', label='seconds' )
            ax.barh( [""], [ field[resist[1]] ], height=0.1, color='#ff0000', label='minutes', left=start[-1] )
            start.append( start[-1] + field[resist[1]] )
            ax.barh( [""], [ field[resist[2]] ], height=0.1, color='#ff6400', label='hours', left=start[-1] )
            start.append( start[-1] + field[resist[2]] )
            ax.barh( [""], [ field[resist[3]] ], height=0.1, color='#ffc800', label='days', left=start[-1] )
            start.append( start[-1] + field[resist[3]] )
            ax.barh( [""], [ field[resist[4]] ], height=0.1, color='#00c800', label='years', left=start[-1] )
            # the following line is juste here because this is the only way I found to not have
            # a very thick horizontal bar : if every bar is 0.1 height, they take all the place
            # shame on me
            ax.barh( [""], [0], height=0.5)
            ax.set_title(f"Password resistance against hacker ({name})")
            ax.legend(bbox_to_anchor=(0.5, -0.2), loc="lower center", ncol=5)
            for spine in plt.gca().spines.values():
                spine.set_visible(False)
            plt.savefig(f"pass_resistance_{name}.png", bbox_inches="tight", transparent=True)

        # most frequent passwords
        fig, ax = plt.subplots()
        values = []
        labels = []
        for i in range(10):
            values.append(int(field[f"{i+1}th frequent password"].split(':',1)[0]))
            labels.append(field[f"{i+1}th frequent password"].split(':',1)[1])
        if max_top == 0:
            max_top = max(values)
        values.reverse()
        labels.reverse()
        ax.barh(labels, values)
        ax.set_title(f"Top cracked passwords for {name}")
        plt.xlim(0, max_top +5)
        for ind, val in enumerate(values):
            plt.text(val, ind, str(val), ha="left", va="center")
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.savefig(f"top_passwords_{name}.png", bbox_inches="tight", transparent=True)
        
        # most frequent patterns
        fig, ax = plt.subplots()
        values = []
        labels = []
        for i in range(10):
            values.append(int(field[f"{i+1}th frequent pattern"].split(':',1)[0]))
            labels.append(field[f"{i+1}th frequent pattern"].split(':',1)[1])
        if max_top_p == 0:
            max_top_p = max(values)
        values.reverse()
        labels.reverse()
        ax.barh(labels, values, color = "cyan")
        ax.set_title(f"Top patterns in cracked passwords for {name}")
        plt.xlim(0, max_top_p +5)
        for ind, val in enumerate(values):
            plt.text(val, ind, str(val), ha="left", va="center")
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.savefig(f"top_patterns_{name}.png", bbox_inches="tight", transparent=True)
 

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

def statSynthesis(users, compromised, status):
    """produce data for synthesis stats"""
    synth = {"total": -1, "cracked": 0, "unsafe": 0, "safe":0}
    for i in compromised:
        if status == 'all' or 'account_disabled' not in compromised[i]['status']:
            if compromised[i]['reason'] == 'leaked':
                synth['unsafe'] += 1
            synth['cracked'] += 1
    synth['cracked'] -= synth['unsafe']
    for i in users:
        if status == 'all' or 'account_disabled' not in i.split('\t')[8]:
            synth['total'] += 1
    synth['safe'] = synth['total'] - synth['cracked'] - synth['unsafe']
    return synth

def statUniq(passwords, status):
    """produce data about unicity stats"""
    unicity = {"empty":0, "non empty": 0, "unique": 0}
    unicity['empty'] = passwords[status].count('')
    unicity['non empty'] = len( passwords[status] ) - unicity['empty']
    unicity['unique'] = len( set( passwords[status] ))
    return unicity

def statSensitive(compromised, status):
    """produce data about the privilege of the users"""
    crit = {"likely":{}, "admin": {}}
    for u in compromised:
        if compromised[u]['priv'] :
            field = 'likely' if 'likely' in compromised[u]['priv'] else 'admin'
            if status == 'all' or 'account_disabled' not in compromised[u]["status"]:
                crit[field][u] = (compromised[u]['robustness'], compromised[u]['reason'])
    return crit

def statLength(passwords, status):
    """produce data for length stats"""
    lengths = [0]*16
    for p in passwords[status]:
        l = len(p)
        if l >= 15:
            lengths[15] += 1
        else:
            lengths[l] += 1
    return lengths

def statCharset(passwords, status):
    """produce data for charset stats"""
    charsets = {'':0,
        'l':0, 'u':0, 'd':0, 'p':0,
        'lu':0, 'ld':0, 'lp':0, 'ud':0, 'up':0, 'dp':0,
        'lud':0, 'lup':0, 'ldp':0, 'udp':0,
        'ludp':0}
    for p in passwords[status]:
        c = getCharsets(p)
        charsets[c] +=1
    return charsets

def statFreq(passwords, status):
    """produce data for most frequent passwords stats"""
    occ = Counter(passwords[status])
    return occ

def statPattern(passwords, status):
    """produce data for most frequent patterns stats"""
    patterns = {}
    digit_isolation = str.maketrans('', '', string.ascii_letters+string.punctuation)
    for p in passwords[status]:
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

def produceStats(users, compromised, wordlist):
    """ Compute stats """
    
    passwords = getPass(compromised)
    stats = []

    for status in ["all", "active"]:
        stat = {}
        stat['field'] = f"{status} accounts"

        # synthesis
        synth = statSynthesis(users, compromised, status)
        stat['total accounts'] = synth['total']
        stat['compromised accounts'] = synth['cracked']
        stat['unsafe accounts'] = synth['unsafe']
        stat['safe accounts'] = synth['safe']

        # unicity
        unicity = statUniq(passwords, status)
        stat['unique passwords compromised'] = unicity['unique']

        # Sensitive
        crit = statSensitive(compromised, status)
        stat['likely sensitive users compromised'] = len( crit['likely'] ) + len( crit['admin'] )
        stat['firm sensitive users compromised'] = len( crit['admin'] )

        # lengths:
        lengths = statLength(passwords, status)
        for i in range(15):
            stat[f"password length {i}"] = lengths[i]
        stat["password length 15 or more"] = lengths[15]

        # charset
        charsets = statCharset(passwords, status)
        stat['passwords with 1 charset'] = charsets[''] + charsets['l'] + charsets['u'] + charsets['d'] + charsets['p']
        stat['passwords with 2 charsets'] = charsets['lu'] + charsets['ld'] + charsets['lp'] + charsets['ud'] + charsets['up'] + charsets['dp']
        stat['passwords with 3 charsets'] = charsets['lud'] + charsets['lup'] + charsets['ldp'] + charsets['udp']
        stat['passwords with all charsets'] = charsets['ludp']
        stat['empty password'] = charsets['']
        stat['lowercase passwords'] = charsets['l']
        stat['uppercase passwords'] = charsets['u']
        stat['digit passwords'] = charsets['d']
        stat['punctuation passwords'] = charsets['p']
        stat['lower-upper passwords'] = charsets['lu']
        stat['lower-digit passwords'] = charsets['ld']
        stat['lower-punct passwords'] = charsets['lp']
        stat['upper-digit passwords'] = charsets['ud']
        stat['upper-punct passwords'] = charsets['up']
        stat['digit-punct passwords'] = charsets['dp']
        stat['lower-upper-digit passwords'] = charsets['lud']
        stat['lower-upper-punct passwords'] = charsets['lup']
        stat['lower-digit-punct passwords'] = charsets['ldp']
        stat['upper-digit-punct passwords'] = charsets['udp']
        stat['lower-upper-digit-punct passwords'] = charsets['ludp']

        # freq
        occ = sorted(statFreq(passwords, status).items(), key=lambda x: x[1], reverse=True)
        l = len(occ)
        for i in range(10):
            stat[f"{i+1}th frequent password"] = [":", f"{occ[i][1]}:{occ[i][0].replace(';','[semicolon]')}"][i<l]

        # pattern
        pat = sorted(statPattern(passwords, status).items(), key=lambda x: x[1], reverse=True)
        l = len(pat)
        for i in range(10):
            stat[f"{i+1}th frequent pattern"] = [":", f"{pat[i][1]}:{pat[i][0].replace(';','[semicolon]')}"][i<l]
        
        # robustness
        if wordlist:
            rob = statRobustness(compromised, status)
            stat['passwords resist some seconds'] = sum( rob[0].values() )
            stat['passwords resist some minutes'] = sum( rob[1].values() )
            stat['passwords resist some hours']   = sum( rob[2].values() )
            stat['passwords resist some days']    = sum( rob[3].values() )
            stat['passwords resist some years']   = synth['safe']
            stat['passwords empty'] = rob[0]['empty']
            stat['passwords based on username'] = rob[0]['login based']
            stat['passwords in top 10 most common'] = rob[0]['top 10 common']
            stat['passwords based on company name'] = rob[0]['company name']
            stat['passwords in top 1000 most common'] = rob[1]['top 1000 common']
            stat['passwords as username extrapolation'] = rob[1]['login extrapolation']
            stat['passwords related to company context'] = rob[1]['company context related']
            stat['passwords with 4 characters or less'] = rob[1]['4 char or less']
            stat['passwords in top 1M most common'] = rob[2]['top 1M common']
            stat['passwords with 6 characters or less'] = rob[2]['6 char or less']
            stat['passwords with 2 charsets or less'] = rob[2]['2 charsets or less']
            stat['passwords present in global wordlists'] = rob[3]['present in attack wordlist']
            stat['passwords present in locale wordlists'] = rob[3]['present in locale attack wordlist']
            stat['passwords leaked'] = rob[3]['leaked']
            stat['passwords weakness undetermined'] = rob[3]['undetermined']

        stats.append(dict(stat))

    return stats

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
    stat_out = "lestat.csv"
    chart_out = "charts/"

    print(f"[*] Importing john result from {args.JOHN_FILE} and domain info from {args.USERS_FILE}")
    users, cu = initInfo(args.JOHN_FILE, args.USERS_FILE)
    populateUsers(cu, users)
    if args.wpath:
        print("[*] Computing robustness (could be long if the wordlists are huge)")
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
        st = produceStats(users, cu, args.wpath)
        exportStats(st, stat_out)
        exportCharts(st, chart_out, args.wpath)

if __name__ == '__main__':
    main()
