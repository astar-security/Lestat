#!/usr/bin/python3

import time
import re
import logging as log
import click
import string
import itertools
from variations import *

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

common_prefix = set()
common_suffix = set()
common_complete = set()

########
# COOK #
########


def compute_fix(birthdate):
    global common_prefix
    global common_suffix
    global common_complete
    global common_numeric
    global common_special
    global common_words
    global leet_swap

    if birthdate:
        for day in range(1,32):
            for month in range(1,13):
                common_numeric.add(f"{day:02}{month:02}" if birthdate == "DDMM" else f"{month:02}{day:02}")

    # pre compute the lists of prefixes and suffixes
    common_prefix = set(case(leet(common_words, 2, leet_swap), 4))
    common_suffix = [n + s for n in common_numeric for s in common_special]
    common_complete = list(itertools.product(common_prefix, common_suffix))
    
    log.info(f"[*] {len(common_prefix)} prefix computed, {len(common_suffix)} suffix computed, {len(common_complete)} prefix+suffix computed")


def common_variation(words, f):
    global common_complete
    global common_prefix
    global common_suffix

    with click.progressbar(words) as wordsbar:
        for word in wordsbar:
            print(*[word + fix[0] + fix[1] + '\n' + fix[0] + word + fix[1] for fix in common_complete], 
                    sep='\n', file=f)


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
@click.option('--birthdates', type=click.Choice(['DDMM', 'MMDD'], case_sensitive=False), help="Add birthdates to the common numeric suffixes") 
@click.argument('userfile') 
def main(userfile, r, e, birthdates):
    """Mangle users from a ldapdomaindump file (domain_users.grep) to create a wordlist"""
    global leet_swap
    words = set()
    log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

    log.info("[*] Computing prefixes and suffixes...")
    compute_fix(birthdates)

    with open(userfile) as f:
        # the first line is the names of the column, we omit it, the SAMACCountName is the 3rd column
        users = import_users(f, r, e)
        log.info(f"[*] {len(users)} users loaded\n{users}")
        mangling = set()
        # first we derivate nicknames from sam account names
        with click.progressbar(users) as usersbar:
            log.info("[*] Computing nicknames...")
            for line in usersbar:
                mangling |= nickname(line, 2)
        log.info(f"[+] {len(mangling)} nicknames computed\n{list(mangling)[:50]}...")

        # second we compute leet and case variations
        log.info("[*] Computing leet variations...")
        mangling = leet(mangling, 2, leet_swap)
        log.info(f"[+] {len(mangling)} leet variations computed\n{list(mangling)[:50]}...")

        log.info("[*] Computing case variations...")
        mangling = case(mangling, 4)
        log.info(f"[+] {len(mangling)} case variations computed\n{list(mangling)[:50]}...")

        # opening the output file for writing
        with open(export_filename, 'w') as fo:
            # finally we add prefixes and suffixes
            log.info("[*] Adding prefixes and suffixes...")
            common_variation(mangling, fo)
            log.info(f"[+] {len(users)*len(common_complete)*2} prefixes and suffixes added")

        log.info("[+] Export complete, all is finished")


if __name__ == '__main__':
    main()
