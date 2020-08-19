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
        "/",
        "?",
        ".",
        ""
        ]

common_numeric = [str(i) for i in range(2010,int(time.strftime("%Y"))+1)] + [str(i)[-2:] for i in range(2000,int(time.strftime("%Y"))+1)] + ["2k"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)] + ["2K"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)] + [str(i) for i in range(10)] + ['123', '1234'] + ['']

def leet_variation(words, full):
    res = set()
    """take two depth of l33t substitution"""
    for word in words:
        res.add(word)
        for key, values in leet_swap.items():
            for value in values:
                if full:
                    for key2, values2 in leet_swap.items():
                        for value2 in values2:
                            first = re.sub(key, value, word, flags=re.I)
                            sec = re.sub(key2, value2, first, flags=re.I)
                            res.add(first)
                            res.add(sec)
                else:
                    res.add(re.sub(key, value, word, flags=re.I))
    return res

def common_variation(word, full):
    res = set()
    for i in common_suffix:
        if full:
            for j in common_numeric:
                for k in common_words:
                    res.add(k + word + j + i)
                    res.add(word + k + j + i)
        else:
            for j in common_numeric:
                res.add(word + j + i)
            for k in common_words:
                res.add(word + k + i)
    return res

def combine(words, perm, full):
    res = []
    tot = len(words)
    # add each word, its capitalized version and its short name
    sys.stderr.write(f"[*] {tot} base words\n")
    with click.progressbar(words, label="Mix case and combine base words") as wordsbar:
        for word in wordsbar:
            res.append(word)
            res.append(word.capitalize())
            res.append(word.upper())
            tot += 2
            if full:
                l = len(word)
                mid = word[0:l//2+l%2]
                res.append(mid)
                res.append(mid.capitalize())
                res.append(mid.upper())
                tot += 3
    #sys.stderr.write(f"[*] {tot} with case variations\n")
    # add each 2 words permutations
    if perm:
        for p in itertools.permutations(words, 2):
            res.append(''.join(p))
            res.append(''.join(map(str.capitalize,p)))
            res.append(''.join(map(str.upper,p)))
            tot += 3
    res = set(res)
    sys.stderr.write(f"[*] {len(res)} unique words after mixing case and combinations\n")
    return res

def mangle(words_file, perm, full):
    """get the base words then apply variations"""
    # combine the base words
    words = combine(words_file.read().lower().splitlines(), perm, full)
    tot = 0
    with click.progressbar(words, label="[*] Computing variations ...", file=sys.stderr) as wordsbar:
        for word in wordsbar:
            mangled = common_variation(word, full)
            mangled = leet_variation(mangled, full)
            tot += len(mangled)
            print(*(mangled), sep='\n')
    sys.stderr.write(f"[*] {tot} candidates computed after variations\n")



def main():    
    parser = argparse.ArgumentParser(description='Derivation of a wordlist to make a efficient crack dictionnary', add_help=True)
    parser.add_argument('-f', action="store", dest="input_file", default=None, 
            help='Specify a wordlist file, if not, stdin is read')
    parser.add_argument('--no-perm', action="store_false", dest="perm", default=True,
            help='Do not mix words 2 by 2, only perform variations over unique words')
    parser.add_argument('--light', action="store_false", dest="full", default=True,
            help='Limit processing to the quick wins')
    args = parser.parse_args()

    if args.input_file:
        with open(args.input_file, "r") as words_file:
            mangle(words_file, args.perm, args.full)
    else:
        words_file = sys.stdin
        mangle(words_file, args.perm, args.full)

if __name__ == '__main__':
    main()
