#!/usr/bin/python3

import time
import re
import logging as log
import click
import string
import itertools

#########
# CONST #
#########

export_filename = 'users.wordlist'

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        't':['7']
        }

common_special = [
        "!",
        "$",
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
# 50 years ago -> now
common_numeric.update( [str(i) for i in range(int(time.strftime("%Y"))-50, int(time.strftime("%Y"))+1)] )
# 2k10 -> now
common_numeric.update( ["2k"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)] )
# 2K10 -> now
common_numeric.update( ["2K"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)] )
# 0 -> 9
common_numeric.update( [str(i) for i in range(10)] )
# 00 -> 99
common_numeric.update( [str(i).zfill(2) for i in range(100)] )
# common numbers
common_numeric.update( ['123', '1234'] )
# birthdates
for day in range(1,32):
    for month in range(1,13):
        common_numeric.add( f"{day:02}{month:02}" )
        common_numeric.add( f"{month:02}{day:02}" )

common_prefix = set()
common_suffix = set()
common_complete = set()

########
# COOK #
########

def nickname_variation(word):
    res = set()
    res.add( word )
    l = len( word )

    # usefull for shortnames and cleaned names
    consonants = str.maketrans('','','aeiouy')
    root = str.maketrans('', '', string.digits + string.punctuation)

    # if compound name
    if re.match(r'.*[-\ \._]', word):
        parts = re.split(r'[\-\ \._]',word)
        # if all the part are made of letters
        if all([i.isalpha() for i in parts]):
            # j-l.lemenchon => jll; paul.bismuth => pb
            res.add( ''.join([i[0:1] for i in parts]) )
            # if there is two parts
            if len(parts) ==2:
                # trigram: gustave.limace => gli
                res.add( parts[0][0:1] + parts[1][0:2] )
                # if the 1st part is made of initials
                if len(parts[0]) < 3 :
                    # jm-levag => jml; fx.demaison => fxd
                    res.add( parts[0] + parts[1][0] )
                    # ch-toulouse => chtoulouse
                    res.add( ''.join(parts) )
        for part in parts:
            if len(part) > 1:
                # d.soria => soria
                res.update( nickname_variation(part) )

    # if the word is atomic
    else:
        # cleaned: confcall_9 => confcall
        cleaned = word.translate(root)
        if len(cleaned) > 1:
            res.add( cleaned )

        # shortnames
        if l > 3 and word.isalpha() :
            # nicolas => nic
            res.add( word[:3] )
            # nicolas => nico
            res.add( word[:4] )
            # if the name start with a consonant and a voyel
            if word[0] not in 'aeiou' and word[1] in 'aeiou':
                # nicolas => nini
                res.add( word[:2] + word[:2] )
            # if the name start with a consonant
            if word[0] not in 'aeiou':
            # nicolas => nc
                cons = word.translate(consonants)[0:2]
                if len(cons) > 1:
                    res.add( cons )

    return res

def case_variation(words):
    res = set()
    for word in words:
        res.update( [word, word.upper(), word.capitalize()] )
    return res


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


# pre compute the lists of prefixes and suffixes
common_prefix = set(case_variation(leet_variation(common_words)))
common_suffix = [n + s for n in common_numeric for s in common_special]
common_complete = list(itertools.product(common_prefix, common_suffix))
# common_complete = [p + s for p in common_prefix for s in common_suffix]

print(f"{len(common_prefix)} prefix computed")
print(f"{len(common_suffix)} suffix computed")
print(f"{len(common_complete)} prefix+suffix computed")

def common_variation(words, f):
    global common_complete
    global common_prefix
    global common_suffix

    with click.progressbar(words) as wordsbar:
        for word in wordsbar:
            #print(*[i[0]+i[1]+i[2]+'\n'+i[1]+i[0]+i[2] for i in itertools.product(common_prefix, [word], common_suffix)], sep='\n', file=f)
            print(*[word + fix[0] + fix[1] + '\n' + fix[0] + word + fix[1] for fix in common_complete], sep='\n', file=f)
            #print(*[word + s for s in common_complete], sep='\n', file=f)
            #print(*[p + word + s for p in common_prefix for s in common_suffix], sep='\n', file=f)

########
# MAIN #
########

def import_users(f, raw, enabled):
    if raw and enabled:
        log.error("[!] --raw-input and --enabled-only options are mutually exclusive")
        exit(1)
    if raw:
        return [line.lower() for line in f.read().splitlines()]
    if enabled:
        users = []
        for line in f.read().splitlines()[1:]:
            l = line.split('\t')
            if "ACCOUNT_DISABLED" not in l[8].upper():
                users.append(l[2].lower())
        return users
    else:
        return [line.split('\t')[2].lower() for line in f.read().splitlines()[1:]]


@click.command()
@click.option('-r/--raw-input', default=False, help='If you want tu submit a file with only the raw usernames instead of a domain_users.grep file')
@click.option('-e/--enabled-only', default=False, help="Do not compute disabled account names")
@click.argument('userfile') #,help='the grepable domain users file from ldapdomaindump')
def main(userfile, r, e):
    """Mangle users from a ldapdomaindump file (domain_users.grep) to create a wordlist"""
    words = set()
    log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

    with open(userfile) as f:
        # the first line is the names of the column, we omit it, the SAMACCountName is the 3rd column
        users = import_users(f, r, e)
        log.info(f"[*] {len(users)} users loaded\n{users}")
        mangling = set()
        # first we derivate nicknames from sam account names
        with click.progressbar(users) as usersbar:
            log.info("[*] Computing nicknames...")
            for line in usersbar:
                mangling |= nickname_variation(line)
        log.info(f"[+] {len(mangling)} nicknames computed\n{list(mangling)[:50]}...")

        # second we compute leet and case variations
        log.info("[*] Computing leet variations...")
        mangling = leet_variation(mangling)
        log.info(f"[+] {len(mangling)} leet variations computed\n{list(mangling)[:50]}...")

        log.info("[*] Computing case variations...")
        mangling = case_variation(mangling)
        log.info(f"[+] {len(mangling)} case variations computed\n{list(mangling)[:50]}...")

        # opening the output file for writing
        with open(export_filename, 'w') as f:
            # finally we add prefixes and suffixes
            log.info("[*] Adding prefixes and suffixes...")
            common_variation(mangling, f)
            log.info(f"[+] {len(users)*len(common_complete)*2} prefixes and suffixes added")

        log.info("[+] Export complete, all is finished")


if __name__ == '__main__':
    main()