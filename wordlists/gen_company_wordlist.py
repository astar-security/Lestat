#!/usr/bin/python3

import time
import logging as log
import click
import itertools
from variations import *

#########
# CONST #
#########

export_filename = 'company.wordlist'

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        'g':['9'],
        't':['7']
        }

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

common_prefix = set()
common_suffix = set()
common_complete = set()

########
# COOK #
########

def combine(words, nicks):
    res = set()
    res |= case(words, 3)
    res |= case(nicks, 3)
    if len(nicks) != 0:
        for n in nicks:
            for p in itertools.product([n], words):
                res |= case_combination(p)
            for p in itertools.product(words, [n]):
                res |= case_combination(p)
    for p in itertools.permutations(words, 2):
        res |= case_combination(p)
    return res

def case_combination(t):
    res = set()
    word1, word2 = t
    # lower lower
    res.add(f'{word1}{word2}')
    # lower Capi
    res.add(f'{word1}{word2.capitalize()}')
    # lower UPPER
    res.add(f'{word1}{word2.upper()}')
    # Capi lower
    res.add(f'{word1.capitalize()}{word2}')
    # Capi Capi
    res.add(f'{word1.capitalize()}{word2.capitalize()}')
    # Capi UPPER
    res.add(f'{word1.capitalize()}{word2.upper()}')
    # UPPER lower
    res.add(f'{word1.upper()}{word2}')
    # UPPER Capi
    res.add(f'{word1.upper()}{word2.capitalize()}')
    # UPPER UPPER
    res.add(f'{word1.upper()}{word2.upper()}')
    return res


def compute_fix():
    global common_prefix
    global common_suffix
    global common_complete
    global common_numeric
    global common_special
    global common_words
    global leet_swap

    # pre compute the lists of prefixes and suffixes
    common_prefix = case(leet(common_words, 2, leet_swap), 3)
    common_suffix = set([n + s for n in common_numeric for s in common_special])
    common_complete = set(itertools.product(common_prefix, common_suffix))

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

def import_words(f, n):
    global common_numeric
    words = set()
    nicks = set()
    if n:
        nicks |= nickname(f.readline().strip().lower(), 1)
    for line in f.read().splitlines():
        if line.isdigit():
            common_numeric.add( line )
        else:
            words.add( line.lower() )
    return words, nicks

@click.command()
@click.option('-n/--nickname', default=False, help='Treat the first word of the list as the company name and compute nickname variations over it')
@click.argument('wordsfile')
def main(wordsfile, n):
    """Combine and mangle words about a company to create a wordlist"""
    global leet_swap
    words = set()
    log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

    with open(wordsfile) as f:
        words, nicks = import_words(f,n)
        log.info(f"[*] {len(words)+len(nicks)} words imported \n{words|nicks}")
        log.info("[*] Computing prefixes and suffixes...")
        compute_fix()

        # second we combine words two by two and compute case variations
        log.info("[*] Combining words...")
        words = combine(words, nicks)
        log.info(f"[+] {len(words)} combinations\n{list(words)}...")

        # third we compute leet variations
        log.info("[*] Computing leet variations...")
        words = leet(words, 2, leet_swap)
        log.info(f"[+] {len(words)} leet variations computed\n{list(words)[:50]}...")

        # opening the output file for writing
        with open(export_filename, 'w') as fo:
            # finally we add prefixes and suffixes
            log.info("[*] Adding prefixes and suffixes...")
            common_variation(words, fo)
            log.info(f"[+] {len(words)*len(common_complete)*2} prefixes and suffixes added")

        log.info(f"[+] Export complete to {export_filename}, all is finished")


if __name__ == '__main__':
    main()
