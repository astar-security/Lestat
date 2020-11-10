#!/usr/bin/python3

import argparse
import sys
import itertools
import time
import re
import click

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        'g':['9'],
        't':['7']
        }

common_words = [
        "pw",
        "pwd",
        "sys",
        "admin",
        "pass",
        "Pass",
        "Admin",
        "adm",
        "Adm",
        ""
        ]

common_suffix = [
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

# 2010 -> now
common_numeric  = [str(i) for i in range(2010,int(time.strftime("%Y"))+1)]
# 00 -> 20
common_numeric += [str(i)[-2:] for i in range(2000,int(time.strftime("%Y"))+1)]
# 2k10 -> now
common_numeric += ["2k"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)]
# 2K10 -> now
common_numeric += ["2K"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)]
# 0 -> 9
common_numeric += [str(i) for i in range(10)]
common_numeric += ['123', '1234'] + ['']


def leet_variation(words):
    global leet_swap
    res = set()
    first_pass = []
    for word in words: 
        res.add(word)
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

def common_variation(word):
    global common_numeric
    global common_suffix
    global common_words
    res = set()
    for i in common_suffix:
        for j in common_numeric:
            for k in common_words:
                # common + root + numeric + suffix
                res.add(k + word + j + i)
                # root + common + numeric + suffix
                res.add(word + k + j + i)
    return res

def nickname_variation(word): 
    res = set()
    res.add( word )
    l = len( word )

    # if compound name
    if re.match(r'.*[-\ \._]', word): 
        parts = re.split(r'[\-\ \._]',word)
        # j-l.melenchon => jlm; general electric => ge
        res.add( ''.join([i[0:1] for i in parts]) )
        # jc-decaud => jcd; fx.demaison => fxd
        if len(parts) == 2:
            res.add( parts[0]+parts[1][0] )
        # d.soria => soria; ch-pasteur => ch, pasteur
        for part in parts:
            if len(part) > 1:
                res.add( part )
        # ch-toulouse => chtoulouse
        res.add( ''.join(parts) )

    else:
        # first and last char
        if l > 2 and word.isalpha() and word[-1] not in 'aeiou':
            res.add(word[0] + word[-1])

        # first half 
        if l > 3 and word.isalpha() :    
            res.add(word[0:l//2+l%2])

        # if doesn't start with vowel
        if word[0] not in 'aeiouy' and word.isalpha():
            # sub vowels
            subbled = re.sub(r'[aeiouyAEIOUY]','',word)
            l_subbled = len(subbled)
            if l_subbled > 1 :
                res.add(subbled)
            # first half of vowels subbing 
            if l_subbled > 3 :
                res.add(subbled[0:l_subbled//2+l_subbled%2])

    return list(res)

def join_variation(word1, word2):
    res = set()
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


def combine(words, perm):
    global common_numeric
    res = set()

    if perm:
        selection = []
        # To change (only first word)
        nicknames = nickname_variation(words.pop(0))

        for word in words:
            if word.isdigit():
                common_numeric.append(word)
            else:
                selection.append(word)
        selection.append('')

        for p in itertools.permutations(selection, 2): 
            res |= join_variation(*p)
        
        for nick in nicknames: 
            for word in selection: 
                res |= join_variation(nick, word)
                res |= join_variation(word, nick)

    else:
        for word in words:
            nicknames = nickname_variation(word)
            for nick in nicknames:
                res.add( nick )
                res.add( nick.upper() )
                res.add( nick.capitalize() )

    sys.stderr.write(f"[*] {len(res)} unique words after mixing case and combinations: {res}\n")
    return res

def mangle(words_file, perm):
    """get the base words then apply variations"""
    words = words_file.read().lower().splitlines() 
    sys.stderr.write(f"[*] {len(words)} base words: {words}\n")
    # combine words
    words = combine(words, perm)
    tot = 0
    with click.progressbar(words, label="[*] Computing variations ...", file=sys.stderr) as wordsbar:
        for word in wordsbar:
            mangled = common_variation(word)
            mangled = leet_variation(mangled)
            tot += len(mangled)
            print(*(mangled), sep='\n')

    sys.stderr.write(f"[*] {tot} candidates computed after variations\n")


def main():
    parser = argparse.ArgumentParser(description='Derivation of a wordlist to make a efficient crack dictionnary', add_help=True)
    parser.add_argument('-f', action="store", dest="input_file", default=None,
            help='Specify a wordlist file, if not, stdin is read')
    parser.add_argument('--no-perm', action="store_false", dest="perm", default=True,
            help='Do not mix words 2 by 2, only perform variations over unique words')
    args = parser.parse_args()

    if args.input_file:
        with open(args.input_file, "r") as words_file:
            mangle(words_file, args.perm)
    else:
        words_file = sys.stdin
        mangle(words_file, args.perm)

if __name__ == '__main__':
    main()
