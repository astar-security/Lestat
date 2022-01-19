#!/usr/bin/python3

import time
import re
import logging as log
import click
import itertools

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
        for part in parts:
            if len(part) > 1:
                # treat each part as a specific word
                res.update( nickname_variation(part) )

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

def compute_fix():
    global common_prefix
    global common_suffix
    global common_complete
    global common_numeric
    global common_special
    global common_words

    # pre compute the lists of prefixes and suffixes
    common_prefix = case_variation(leet_variation(common_words))
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
    """Combine and mangle words about a company to create a wordlist"""
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
        words = leet_variation(words)
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
