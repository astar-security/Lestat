#!/usr/bin/python3

import time
import re
import logging as log
import click
from variations import *

#########
# CONST #
#########

export_filename = 'quickwin.wordlist'

########
# MODE #
########

def tiny(f):
    """Get the approximative 10 most likely passwords"""
    words = set()
    
    numeric = ['']
    special =  ['', '!']
    
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.append(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words)} words imported: {' '.join(list(words))}")
 
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case(words, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res = affix(res, 1, [], suffixes)
    log.info(f"[*] {len(res)} candidates after adding suffixes: {' '.join(list(res)[:50])}")
    return res 

def short(f):
    """Get the approximative 100 most likely passwords"""
    words = set()
    
    numeric = ['', '1', '01', '123']
    special =  ['', '!']
    leet_swap = {'a':['4'], 'e':['3'], 'i':['1'], 'o':['0']}
    
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.append(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words)} words imported: {' '.join(list(words))}")

    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case(words, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res2 = leet(res, 1, leet_swap)
    log.info(f"[*] {len(res2)} candidates after leet substitution: {' '.join(list(res2)[:50])}")
    res2 = affix(res2, 1, [], special)
    # we avoid to have numbers from numeric AND leet
    res = affix(res, 1, [], suffixes) | res2
    log.info(f"[*] {len(res)} candidates after adding suffixes: {' '.join(list(res)[:50])}")
    return res 

def common(f):
    """Get the approximative 1000 most likely passwords"""
    words = set()
   
    tags = ['', 'adm', 'admin']
    numeric = set(['', '1', '01', '123'])
    # 2015 -> now
    numeric.update( [str(i) for i in range(2015, int(time.strftime("%Y"))+1)] )
    # 2k15 -> now
    numeric.update( ["2k"+str(i)[-2:] for i in range(2015, int(time.strftime("%Y"))+1)] )
    # 2K15 -> now
    numeric.update( ["2K"+str(i)[-2:] for i in range(2015, int(time.strftime("%Y"))+1)] )
    # 0 -> 9 and 00 -> 09
    numeric.update( [str(i) for i in range(10)] )
    numeric.update( [str(i).zfill(2) for i in range(10)] )
    special =  ['', '!', '.']
    leet_num = {'a':['4'], 'e':['3'], 'i':['1'], 'o':['0']}
    leet_spe =  {'a':['@'], 'i':['!'], 's':['$']}

    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.add(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words)} words imported: {' '.join(list(words))}")
    
    prefixes = case(tags, 3)
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case(words, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res_num = leet(res, 1, leet_num)
    res_spe = leet(res, 1, leet_spe)
    log.info(f"[*] {len(res_num|res_spe)} candidates after leet substitution: {' '.join(list(res_num|res_spe)[:50])}")
    res = affix(res, 1, prefixes, suffixes) | affix(res_num, 1, prefixes, special) | affix(res_spe, 1, prefixes, numeric) 
    log.info(f"[*] {len(res)} candidates after adding prefixes and suffixes: {' '.join(list(res)[:50])}")
    return res 


def extended(f):
    """Get the approximative 25 000 most likely passwords"""
    words = set()

    tags = ['', 'adm', 'admin']
    numeric = set(['', '123', '1234'])
    # 2015 -> now
    numeric.update( [str(i) for i in range(2015, int(time.strftime("%Y"))+1)] )
    # 2k15 -> now
    numeric.update( ["2k"+str(i)[-2:] for i in range(2015, int(time.strftime("%Y"))+1)] )
    # 2K15 -> now
    numeric.update( ["2K"+str(i)[-2:] for i in range(2015, int(time.strftime("%Y"))+1)] )
    # 0 -> 9 and 00 -> now and 60 -> 99
    numeric.update( [str(i) for i in range(10)] )
    numeric.update( [str(i)[-2:] for i in range(2000, int(time.strftime("%Y"))+1)] )
    numeric.update( [str(i).zfill(2) for i in range(60, 100)] )
    special =  ['', '!', '.', '*']
    leet_swap = {'a':['4', '@'], 'e':['3'], 'i':['1', '!'], 'o':['0'], 's':['$'], 't':['7']}

    name = f.readline().strip().lower()
    words.add(name)
    nicks = nickname(name, 3)
    log.info(f"[*] first word is assumed to be a name, {len(nicks)} nicknames were computed: {' '.join(list(nicks))}")
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.add(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words|nicks)} words imported: {' '.join(list(words|nicks))}")

    prefixes = case(tags, 3)
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case(words, 4)
    # we do this to avoid leet variation over nicknames
    res2 = res | case(nicks, 3)
    log.info(f"[*] {len(res2)} candidates after case variation: {' '.join(list(res2)[:50])}")
    res2 |= leet(res, 2, leet_swap)
    log.info(f"[*] {len(res2)} candidates after leet substitution: {' '.join(list(res2)[:50])}")
    res = affix(res2, 1, prefixes, suffixes)
    del(res2)
    log.info(f"[*] {len(res)} candidates after adding prefixes and suffixes: {' '.join(list(res)[:50])}")
    return res 


def insane(f):
    """Get the most likely passwords"""
    words = set()

    tags = ['', 'adm', 'admin', 'adm', 'pwd', 'pass']
    numeric = set(['', '123', '1234'])
    # 2010 -> now
    numeric.update( [str(i) for i in range(2010, int(time.strftime("%Y"))+1)] )
    # 2k10 -> now
    numeric.update( ["2k"+str(i)[-2:] for i in range(2010, int(time.strftime("%Y"))+1)] )
    # 2K10 -> now
    numeric.update( ["2K"+str(i)[-2:] for i in range(2010, int(time.strftime("%Y"))+1)] )
    # 0 -> 9 and 00 -> 99
    numeric.update( [str(i) for i in range(10)] )
    numeric.update( [str(i).zfill(2) for i in range(0, 100)] )
    special =  ['', '!', '.', '*', '@', '$', '%', '?']
    leet_swap = {'a':['4', '@'], 'e':['3'], 'i':['1', '!'], 'o':['0'], 's':['5', '$'], 't':['7'], 'g':['9']}

    name = f.readline().strip().lower()
    words.add(name)
    nicks = nickname(name, 3)
    log.info(f"[*] first word is assumed to be a name, {len(nicks)} nicknames were computed: {' '.join(list(nicks))}")
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.add(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words|nicks)} words imported: {' '.join(list(words|nicks))}")

    prefixes = case(leet(tags, 1, leet_swap), 3)
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case(words, 4)
    res |= case(nicks, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res |= leet(res, 2, leet_swap)
    log.info(f"[*] {len(res)} candidates after leet substitution: {' '.join(list(res)[:50])}")
    res = affix(res, 2, prefixes, suffixes)
    log.info(f"[*] {len(res)} candidates after adding prefixes and suffixes: {' '.join(list(res)[:50])}")
    return res 


########
# MAIN #
########

@click.command()
@click.option('--mode', default="common", help='indicate the number of passwords to generate: tiny (around 10), short (around 100), common (around 1000), extended (around 25 000), insane (as many as necessary). Default is common')
@click.argument('wordsfile')
def main(wordsfile, mode):
    """Mangle words about a short set to create a quickwin wordlist."""
    if mode not in ('tiny', 'short', 'common', 'extended', 'insane'):
        log.error("[!] Incorrect mode. Choices are tiny, short, common, extended, insane") 
        exit(1)
    words = set()
    log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

    with open(wordsfile) as f:
        words = eval(f"{mode}(f)")
        log.info(f"[+] {len(words)} final password candidates computed")

        # opening the output file for writing
        with open(export_filename, 'w') as fo:
            log.info("[*] Writing...")
            for word in words:
                fo.write(word+'\n')
            log.info(f"[+] Export complete to {export_filename}, all is finished")


if __name__ == '__main__':
    main()
