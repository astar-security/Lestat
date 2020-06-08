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
        "123",
        "1234"
        ]

suffix = [
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

def leet_variation(word, res):
    """take two depth of l33t substitution"""
    for key, values in leet_swap.items():
        for value in values:
            for key2, values2 in leet_swap.items():
                for value2 in values2:
                    first = re.sub(key, value, word, flags=re.I)
                    sec = re.sub(key2, value2, first, flags=re.I)
                    for j in suffix:
                        res.add(first + j)
                        res.add(sec + j)
    return res

def common_variation(word, res):
    for i in common_words:
        for suff in suffix:
            res.add(i + word + suff)
            res.add(word + i + suff)
    return res

def years_variation(word, res):
    for i in range(2010, int(time.strftime("%Y"))+1):
        for j in suffix:
            res.add(word + str(i) + j)
            res.add(word + str(i).replace('0','k') + j)
            res.add(word + str(i).replace('0','K') + j)
            res.add(word + str(i-2000) + j)
    return res

def number_variation(word, res):
    for i in range(10):
        for j in suffix:
            res.add(word+str(i)+j)
            res.add(word+"0"+str(i)+j)
    return res

def combine(words):
    res = set()
    # add each word, its capitalized version and its short name
    for word in words:
        res.add(word)
        res.add(word.capitalize())
        res.add(word.upper())
        l = len(word)
        mid = word[0:l//2+l%2]
        res.add(mid)
    # add each 2 words permutations
    for p in itertools.product(res, repeat=2):
        res.add(''.join(p))
    # add mid word and duplicate mid word
    print(*(res), sep='\n')
    return res

def variate(words):
    res = set()
    for word in words:
        # reverse
        res.add(word[::-1])
        # common prefix and suffix
        res = common_variation(word, res)
        # years
        res = years_variation(word, res)
        # numbers
        res = number_variation(word, res)
        # l33t
        res = leet_variation(word, res)
    print(*(res), sep='\n')

def mangle(words_file):
    """get the base words then apply variations"""
    # combine the base words
    words = combine(words_file.read().lower().splitlines())
    variate(words)

def main():    
    parser = argparse.ArgumentParser(description='Derivation of a wordlist to make a efficient crack dictionnary', add_help=True)
    parser.add_argument('-f', action="store", dest="input_file", default=None, 
            help='Specify a wordlist file, if not, stdin is read')
    args = parser.parse_args()

    if args.input_file:
        with open(args.input_file, "r") as words_file:
            mangle(words_file)
    else:
        words_file = sys.stdin
        mangle(words_file)

if __name__ == '__main__':
    main()

