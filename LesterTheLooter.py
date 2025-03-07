#!/usr/bin/python3

import string
import argparse
import csv
import json
from collections import Counter
from termcolor import colored
import xlsxwriter
from TonyTheTagger import *
from GregTheGrapher import *

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
        "domain admins",
        "enterprise admins",
        "print operators",
        "replicator",
        "schema admins",
        "server operators"
        ]

robkeys = ["seconds", "minutes", "hours", "days"]

#########
# Utils #
#########


def beautifyName(person):
    """remove domain prefix/suffix and lowercase everything"""
    person = person.lower()
    dom = ''
    # astar.org\\jdupond
    if '\\' in person:
        dom, person = person.split('\\')
    # jdupond@astar.org
    if '@' in person:
        person, dom = person.split('@')
    return person, dom

def isPriv(elem, groups=None):
    """check clues about an element (a user or a group) being privileged"""
    global PRIVILEGED_GROUPS
    suspected_admin = "adm" in elem and "administratif" not in elem
    # if elem is a user, variable "groups" is a list
    if groups:
        for i in sorted(groups, key=len):
            if i in PRIVILEGED_GROUPS:
                return i
            if "adm" in i and "administratif" not in i:
                suspected_admin = True
        if suspected_admin:
           return "likely admin"
        else:
            return None
    # if elem is a group, variable "groups" is empty
    else:
        if elem in PRIVILEGED_GROUPS:
            return elem
        elif suspected_admin:
            return "likely"
        else:
            return None

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

def parsePassfile(pass_file):
    """verify passwords file's content"""
    """get the user:pass"""
    """check robustness indicator"""
    """check if the leakTheWeak module was used on the john file"""
    global robkeys
    compromised = {}
    with open(pass_file, "r") as f:
        john = f.read().splitlines()
        domains = set()
        for line in john:
            person = line.split(':')
            reason = "undetermined"
            robustness = 3
            lpers = len(person)
            if lpers < 2:
                print(f"[!] Line ignored in {pass_file} file (not a valid user:password form): {line}")
                continue
            if lpers > 4 or lpers ==3 :
                print(f"[!] Line used but seems to contain more than only a user:password form (or user:password:robustness:reason form): {line}")
            if lpers == 4 and person[2] in robkeys:
                robustness = robkeys.index(person[2])
                reason = person[3]
            bname, dom = beautifyName(person[0])
            domains.add(dom)
            compromised[bname] = {"password":person[1], "groups":[], "status":[], "lastchange":"", "lastlogon":"", "robustness":robustness, "reason":reason, "priv":None, "description":""}
    print(f"[*] Company name can sometimes be infered from domain name : {domains}")
    return compromised, domains

def parseUserfileFromJSON(user_file):
    """Check domain users information can be imported"""
    with open(user_file) as f:
        try:
            data = json.load(f)
            return data
        except Exception as e:
            print(f"[!] Impossible to import domain users information from {user_file} : {e}")
            exit(1)


def parseUserfile(user_file):
    """check domain users info file's format"""
    res = []
    with open(user_file,"r") as f:
        users = f.read().lower().splitlines()
        # check first line
        if users[0] != 'cn\tname\tsamaccountname\tmemberof\tprimarygroupid\twhencreated\twhenchanged\tlastlogon\tuseraccountcontrol\tpwdlastset\tobjectsid\tdescription':
            print("[!] Bad user file")
            exit(1)
        col = users[0].split('\t')
        for line in users[1:]:
            info = line.split('\t')
            if len(info) != 12:
                print(f"[!] Bad line in user file: {line}")
                exit(1)
            res.append(dict(zip(col, info)))
    return res

def populateUsersFromJSON(compromised, users):
    """complete info about users compromised by using the domain users info file"""
    primary = { 513: "domain users", 512: "domain admins", 514: "domain guests", 
               521: "enterprise domain controllers", 518: "schema admins", 519: "enterprise admins",
               572: "denied rodc password replication group"}
    for p in users:
        name = p['attributes']['sAMAccountName'][0].lower()
        if name in compromised :
            compromised[name]['lastchange'] = p['attributes']['pwdLastSet'][0]
            if 'lastLogonTimestamp' in p['attributes']:
                compromised[name]['lastlogon'] = p['attributes']['lastLogonTimestamp'][0]
            ac = p['attributes']['userAccountControl'][0]
            compromised[name]['status'] = "disabled" if bin(ac)[-2] == '1' else "enabled"
            compromised[name]['groups'] = [ primary[p['attributes']['primaryGroupID'][0]] ]
            if 'memberOf' in p['attributes']:
                for group in p['attributes']['memberOf']:
                    compromised[name]['groups'].append(group.split(',')[0].split('CN=')[1].lower())
            if 'description' in p['attributes']:
                compromised[name]['description'] = p['attributes']['description'][0]
    # check privilege
    for acc, info in compromised.items():
        if len(info["groups"]) == 0:
            print(f"[!] {acc} not consolidated from domain users info")
        else:
            info["priv"] = isPriv(acc, info['groups'])


def populateUsers(compromised, users):
    """complete info about users compromised by using the domain users info file"""
    for p in users:
        if p["samaccountname"] in compromised:
            compromised[p["samaccountname"]]["groups"] = p["memberof"].split(', ')
            compromised[p["samaccountname"]]["lastchange"] = p["pwdlastset"]
            compromised[p["samaccountname"]]["lastlogon"] = p["lastlogon"]
            compromised[p["samaccountname"]]["groups"].append(p["primarygroupid"])
            compromised[p["samaccountname"]]["status"] = p["useraccountcontrol"].split(', ')
            compromised[p["samaccountname"]]["description"] = p["description"]
    # check privilege
    for acc, info in compromised.items():
        if len(info["groups"]) == 0:
            print(f"[!] {acc} not consolidated from domain users info")
        else:
            info["priv"] = isPriv(acc, info['groups'])


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

def displayUsers(compromised, priv):
    """Print main info about users compromised"""
    print(f"[*] {'Privileged' if priv else 'All'} enabled accounts compromised are listed below:")
    print(f"\t{'STATUS'.ljust(9)} {'USERNAME'.ljust(22)} {'PASSWORD'.ljust(18)} {'SENSITIVE'.ljust(17)} {'#GROUPS'.ljust(8)} DESCRIPTION")
    for acc, info in compromised.items() :
        user = {"name": acc}
        user['password'] = info['password']
        user['status'] = 'disabled' if 'account_disabled' in info['status'] else 'enabled'
        user['num groups'] = str(len( info['groups'] ))
        user['sensitive'] = info['priv'] if info['priv'] else "unknown"
        user['description'] = info['description']
        if user['status'] == "enabled" and (not priv or user['sensitive'] != 'unknown') :
            c = "yellow" if user['sensitive'] == "likely admin" else "red"
            if user['sensitive'] == 'unknown':
                c = "white"
            print(colored(f"[+]\t{user['status'].ljust(9)} {user['name'].ljust(22)} {user['password'].ljust(18)} {user['sensitive'].ljust(17)} {user['num groups'].ljust(8)} {user['description']}", c))

def exportUsers(compromised, output):
    """write consolidated info about users into CSV format with ; separator"""
    global robkeys
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
            user['robustness'] = robkeys[info['robustness']]
            user['reason'] = info['reason']
            user['description'] = info['description']
            if not w:
                w = csv.DictWriter(f, user.keys(), delimiter=";")
                w.writeheader()
            w.writerow(user)

def exportGroups(compromised_groups, output):
    """write consolidated info about groups into CSV format with ; separator"""
    global robkeys
    with open(output, 'w') as f:
        w = None
        for gr, info in compromised_groups.items() :
            group = {"name": gr}
            group['members compromised'] = len( info['disabled'] ) + len( info['enabled'] )
            group['sensitive'] = info['priv'] if info['priv'] else "unknown"
            group['robustness'] = robkeys[info['robustness']]
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


def exportExcel(compromised, compromised_groups, stats, excelpath):
    global robkeys
    workbook = xlsxwriter.Workbook(excelpath)
    firstline_format = workbook.add_format({'font_color': '#F4F5F5', 
                                        'align': 'vcenter', 
                                        'align': 'center',
                                        'text_wrap': True,
                                        'bg_color': '#051F34'})
    passline_format = workbook.add_format({'text_wrap': True, 'align': 'vcenter'})
    disabled_format = workbook.add_format({'text_wrap': True, 'align': 'vcenter', 'bg_color': '#d9d9d9'})
    sensitive_format = workbook.add_format({'text_wrap': True, 'align': 'vcenter', 'bg_color': '#c80000'})
    likely_format = workbook.add_format({'text_wrap': True, 'align': 'vcenter', 'bg_color': '#ff6400'})
    uc = workbook.add_worksheet('Users Compromised')
    uc.set_row(0, None, firstline_format)
    uc.autofilter(0,0,0,9)
    uc.freeze_panes(1, 0)
    for col, text in enumerate(['Username', 'Password', 'Status', 'Last logon', 'Last change', '# groups', 'Groups', 'Sensitivity', 'Robustness', 'Reason', 'Description']):
        uc.write(0, col, text)
    uc.set_column(0,0, 11)
    uc.set_column(1,1, 15)
    uc.set_column(2,2, 9)
    uc.set_column(3,3, 11)
    uc.set_column(4,4, 11)
    uc.set_column(5,5, 7)
    uc.set_column(6,6, 100)
    uc.set_column(7,7, 11)
    uc.set_column(8,8, 9)
    uc.set_column(9,9, 11)
    uc.set_column(10,10,80)
    line = 1
    for acc, info in compromised.items() :
        uc.write(line, 0, acc)
        uc.write(line, 1, info['password'])
        uc.write(line, 2, 'disabled' if 'account_disabled' in info['status'] else 'enabled')
        uc.write(line, 3, info['lastlogon'])
        uc.write(line, 4, info['lastchange'])
        uc.write(line, 5, len(info['groups']))
        uc.write(line, 6, ', '.join(info['groups']))
        uc.write(line, 7, info['priv'] if info['priv'] else "unknown")
        uc.write(line, 8, robkeys[info['robustness']])
        uc.write(line, 9, info['reason'])
        uc.write(line, 10, info['description'])
        if 'account_disabled' in info['status']:
            uc.set_row(line, None, disabled_format)
        elif info['priv'] == 'likely admin':
            uc.set_row(line, None, likely_format)
        elif info['priv'] :
            uc.set_row(line, None, sensitive_format)
        else:
            uc.set_row(line, None, passline_format)
        line += 1

    gc = workbook.add_worksheet('Groups Compromised')
    gc.set_row(0, None, firstline_format)
    gc.autofilter(0,0,0,5)
    gc.freeze_panes(1, 0)
    for col, text in enumerate(['Name', '# compromised', 'Sensitivity', 'Robustness', 'Enabled members compromised', 'Disabled members compromised']):
        gc.write(0, col, text)
    gc.set_column(0,0, 25)
    gc.set_column(1,1, 11)
    gc.set_column(2,2, 9)
    gc.set_column(3,3, 9)
    gc.set_column(4,4, 80)
    gc.set_column(5,5, 75)
    line = 1
    for gr, info in compromised_groups.items():
        gc.write(line, 0, gr)
        gc.write(line, 1, len(info['disabled']) + len(info['enabled']))
        gc.write(line, 2, info['priv'] if info['priv'] else "unknown")
        gc.write(line, 3, robkeys[info['robustness']])
        gc.write(line, 4, ', '.join(info['enabled']))
        gc.write(line, 5, ', '.join(info['disabled']))
        if len(info['enabled']) == 0:
            gc.set_row(line, None, disabled_format)
        elif info['priv'] == 'likely':
            gc.set_row(line, None, likely_format)
        elif info['priv'] :
            gc.set_row(line, None, sensitive_format)
        else:
            gc.set_row(line, None, passline_format)
        line +=1
    
    st = workbook.add_worksheet('Statistics')
    st.set_row(0, None, firstline_format)
    for i in range(1,1000):
        st.set_row(i, None, disabled_format)
    st.freeze_panes(1, 0)
    for col, text in enumerate(stats[0].keys()):
        st.write(0, col, text)
    for col, v in enumerate(stats[0].values()):
        st.write(1, col, v)
    for col, v in enumerate(stats[1].values()):
        st.write(2, col, v)
    charts = exportCharts(stats, "Fileless", False)
    offset_col = 1
    offset_row = 4
    for field in charts:
        for buffer in charts[field]:
            st.insert_image(offset_row, offset_col, "", {'image_data': buffer})
            offset_col += 10
        offset_col = 1
        offset_row += 25

    workbook.close()


#########
# Stats #
#########


def getPass(compromised):
    """just create a dict with two lists: one for all the acounts, another for the active accounts only"""
    passwords = {"all":[], "active":[]}
    for c in compromised:
        passwords["all"].append(compromised[c]['password'])
        if 'account_disabled' not in compromised[c]['status']:
            passwords["active"].append(compromised[c]['password'])
    return passwords

def statSynthesis(users, compromised, status):
    """produce data for synthesis stats"""
    synth = {"total": -1, "cracked": 0, "safe":0}
    for i in compromised:
        if status == 'all' or 'account_disabled' not in compromised[i]['status']:
            synth['cracked'] += 1
    for i in users:
        if status == 'all' or 'account_disabled' not in i["useraccountcontrol"]:
            synth['total'] += 1
    synth['safe'] = synth['total'] - synth['cracked']
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
    rob = {0:{}, 1:{}, 2:{}, 3:{}}
    for acc, info in compromised.items():
        if status == 'all' or 'account_disabled' not in info["status"]:
            if info['reason'] not in rob[info['robustness']]:
                rob[info['robustness']][info['reason']] = 0
            rob[info['robustness']][info['reason']] += 1
    return rob

def produceStats(users, compromised):
    """ Compute stats """

    global robkeys

    passwords = getPass(compromised)
    stats = []

    for status in ["all", "active"]:
        stat = {}
        stat['field'] = f"{status} accounts"

        # synthesis
        synth = statSynthesis(users, compromised, status)
        stat['total accounts'] = synth['total']
        stat['compromised accounts'] = synth['cracked']
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
            stat[f"{i+1}th frequent password"] = f"{occ[i][1]}:{occ[i][0].replace(';','[semicolon]')}" if i<l else ":"

        # pattern
        pat = sorted(statPattern(passwords, status).items(), key=lambda x: x[1], reverse=True)
        l = len(pat)
        for i in range(10):
            stat[f"{i+1}th frequent pattern"] = f"{pat[i][1]}:{pat[i][0].replace(';','[semicolon]')}" if i<l else ":"

        # robustness
        rob = statRobustness(compromised, status)
        for i in range(len(robkeys)):
            stat[f"password resists some {robkeys[i]}"] = sum(rob[i].values())
        stat['password resists some years']   = synth['safe']
        for robustness in rob:
            for reason in rob[robustness]:
                stat[f"cracked because {reason} ({robkeys[robustness]})"] = rob[robustness][reason]

        stats.append(dict(stat))

    return stats

def main():
    parser = argparse.ArgumentParser(description='Analysis of cracked domain accounts', add_help=True)
    parser.add_argument('JOHN_FILE', action="store",
            help="The cracked passwords by john (john --show command)")
    parser.add_argument('USERS_FILE', action="store",
            help="The file containing the Domain users info (from ldapdomaindump: domain_users.grep)")
    parser.add_argument('--priv', action="store_true", default=False,
            help='Specify that you want to display only the privileged users compromised (default is all)')
    parser.add_argument('--csv', action="store_true", default=False,
            help='Export in 3 CSV files instead of one XLSX')
    args = parser.parse_args()

    user_out = "users_compromised.csv"
    group_out = "group_compromised.csv"
    stat_out = "lestat.csv"

    print(f"[*] Importing domain info from {args.USERS_FILE}")
    users = parseUserfile(args.USERS_FILE)
    print(f"[*] Importing john result from {args.JOHN_FILE}")
    cu, dom = parsePassfile(args.JOHN_FILE)
    populateUsers(cu, users)
    print("[*] Assigning robustness")
    populateRobustness(cu, dom)
    print("[*] Computing groups information")
    cg = populateGroups(cu)
    print("[*] Computing stats")
    st = produceStats(users, cu)
    displayUsers(cu, args.priv)
    if args.csv:
        print(f"[*] Exporting to CSV format: {user_out}, {group_out} and  {stat_out}")
        exportUsers(cu, user_out)
        exportGroups(cg, group_out)
        exportStats(st, stat_out)
    else:
        print(f"[*] Exporting to XLSX format in lestat.xlsx")
        exportExcel(cu, cg, st, "lestat.xlsx")
    print("[+] Export successful. All finished !")

if __name__ == '__main__':
    main()
