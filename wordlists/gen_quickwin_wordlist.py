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

export_filename = 'quickwin.wordlist'

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        }

common_special = [
        "!",
        ".",
        ""
        ]

common_words = [
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
# 10 -> now
common_numeric.update( [str(i)[-2:] for i in range(2010, int(time.strftime("%Y"))+1)] )
# 0 -> 9
common_numeric.update( [str(i) for i in range(10)] )
# common numbers
common_numeric.update( ['01', '123', '1234'] )

common_prefix = set()
common_suffix = set()

########
# COOK #
########

def nickname_variation(word):
    res = set()
    l = len( word )

    # usefull for shortnames and cleaned names
    consonants = str.maketrans('','','aeiouy')

    # if compound name
    if re.match(r'.*[-\ \._]', word):
        parts = re.split(r'[\-\ \._]',word)
        # general electric => ge
        res.add( ''.join([i[0:1] for i in parts]) )
        # if there are two parts
        if len(parts) ==2:
            # jc-decaud => jcd
            res.add( parts[0] + parts[1][0] )
            # ch-toulouse => chtoulouse
            res.add( ''.join(parts) )

    # if the word is atomic
    else:
        res.add( word )
        # shortnames
        if l > 3 and word.isalpha() :
            # airbus => air
            res.add( word[:3] )
            # goldman => gold
            res.add( word[:4] )
            # microsoft => micro
            res.add( word[0:l//2+l%2] )
            # chrysler => cr
            res.add( word[0] + word[-1] )
        # if the name start with a consonant
        if word[0] not in 'aeiou':
            # remove voyels
            cons = word.translate(consonants)
            l_cons = len(cons)
            if l_cons > 1:
                # tetrapak => ttrpk
                res.add( cons )
            if l_cons > 3:
                # tetrapak => ttr
                res.add( cons[0:(l_cons//2)+(l_cons%2)] )

    return res

def combine(words, nicks):
    res = set()
    res |= case_variation(words)
    res |= case_variation(nicks)
    return res

def case_variation(words):
    res = set()
    for word in words:
        res.update( [word, word.upper(), word.capitalize()] )
    return res


def leet_variation(words):
    global leet_swap
    res = set()

    for word in words:
        res.add(word)
        if word.isalpha() and len(set(word)) > 1 and len(word) > 2:
            need = [c for c in leet_swap.keys() if c in word.lower()]
            for i in range(len(need)):
                nee1 = need[i]
                for sub in leet_swap[nee1]:
                    res.add(re.sub(nee1, sub, word, flags=re.I))
    return res

def compute_fix():
    global common_prefix
    global common_suffix
    global common_numeric
    global common_special
    global common_words

    # pre compute the lists of prefixes and suffixes
    common_prefix = case_variation(leet_variation(common_words))
    common_suffix = set([n + s for n in common_numeric for s in common_special])

    log.info(f"[*] {len(common_prefix)} prefix computed, {len(common_suffix)} suffix computed")


def common_variation(words):
    global common_prefix
    global common_suffix

    res = set()
    with click.progressbar(words) as wordsbar:
        for word in wordsbar:
            for fix in common_prefix:
                res.add(fix + word)
            for fix in common_suffix:
                res.add(word + fix)
    return res

########
# MAIN #
########

def import_words(f, n):
    global common_numeric
    words = set()
    nicks = set()
    if n:
        nicks |= nickname_variation(f.readline().strip().lower())
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
    """Combine and mangle words about a company to create a quickwin wordlist. We recommend using name - place - activity - number"""
    words = set()
    log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

    with open(wordsfile) as f:
        words, nicks = import_words(f,n)
        log.info(f"[*] {len(words)+len(nicks)} words imported \n{words|nicks}")
        log.info("[*] Computing prefixes and suffixes...")
        compute_fix()

        # second we compute case variations
        log.info("[*] Computing case variations...")
        words = combine(words, nicks)
        log.info(f"[+] {len(words)} combinations\n{list(words)}...")

        # third we compute leet variations
        log.info("[*] Computing leet variations...")
        words = leet_variation(words)
        log.info(f"[+] {len(words)} leet variations computed\n{list(words)[:50]}...")

        # 4th we combine words and suffixes/prefixes
        log.info("[*] Adding suffixes and prefixes...")
        words = common_variation(words)
        log.info(f"[+] {len(words)} final password candidates computed\n{list(words)[:50]}...")

        # opening the output file for writing
        with open(export_filename, 'w') as fo:
            log.info("[*] Writing...")
            for word in words:
                fo.write(word+'\n')
            log.info(f"[+] Export complete to {export_filename}, all is finished")


if __name__ == '__main__':
    main()
