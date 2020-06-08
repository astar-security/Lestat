#!/usr/bin/python3

import argparse
import sys
import itertools
import time
import re

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        'l':['1','!'],
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

def leet_substitution(words):
    """take two depth of l33t substitution"""
    res = set()
    for word in words:
        for key, values in leet_swap.items():
            for value in values:
                for key2, values2 in leet_swap.items():
                    for value2 in values2:
                        first = re.sub(key, value, word, flags=re.I)
                        sec = re.sub(key2, value2, first, flags=re.I)
                        res.add(first)
                        res.add(sec)
    return res

def common_variation(words):
    res = set()
    for word in words:
        for i in common_words:
            for j in common_numeric:
                for k in common_suffix:
                    res.add(i + word + j + k)
                    res.add(word + i + j + k)
    return res

def combine(words, perm):
    res = set()
    # add each word, its capitalized version and its short name
    for word in words:
        res.add(word)
        res.add(word.capitalize())
        res.add(word.upper())
        l = len(word)
        mid = word[0:l//2+l%2]
        res.add(mid)
        res.add(mid.capitalize())
        res.add(mid.upper())
    # add each 2 words permutations
    if perm:
        for p in itertools.product(res, repeat=2):
            res.add(''.join(p))
    return res

def mangle(words_file, perm):
    """get the base words then apply variations"""
    # combine the base words
    words = combine(words_file.read().lower().splitlines(), perm)
    words = common_variation(words)
    words = leet_substitution(words)
    print(*(words), sep='\n')

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
