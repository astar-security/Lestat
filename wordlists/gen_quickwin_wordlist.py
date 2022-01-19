#!/usr/bin/python3

import time
import re
import logging as log
import click

#########
# CONST #
#########

export_filename = 'quickwin.wordlist'

########
# UTIL #
########

def nickname_variation(word):
    res = set()
    l = len( word )

    # usefull for shortnames and cleaned names
    consonants = str.maketrans('','','aeiouy')

    # if compound name
    if re.match(r'.*[-\ \._]', word):
        parts = re.split(r'[\-\ \._]',word)
        res.update(parts)
        # general electric => ge
        res.add( ''.join([i[0:1] for i in parts]) )
        # if there are two parts
        if len(parts) == 2:
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


def case_variation(words, deep):
    res = set()
    for word in words:
        variation = [word, word.upper(), word.capitalize(), word.capitalize().swapcase()]
        res.update( variation[0:deep] )
    return res


def leet_variation(words, leet_swap, deep):
    res = set()
    first_pass = []
    for word in words:
        res.add(word)
        if word.isalpha() and len(set(word)) > 1 and len(word) > 2:
            need = [c for c in leet_swap.keys() if c in word.lower()]
            for i in range(len(need)):
                nee1 = need[i]
                for sub in leet_swap[nee1]:
                    first_pass.append(re.sub(nee1, sub, word, flags=re.I))
                res |= set(first_pass)
                if deep == 2:
                    for j in range(i+1, len(need)):
                        nee2 = need[j]
                        for word2 in first_pass:
                            for sub in leet_swap[nee2]:
                                res.add(re.sub(nee2, sub, word2, flags=re.I))
                first_pass = []
    return res



def common_variation(words, prefixes, suffixes, deep):
    """apply common prefixes and suffixes to the root words"""
    res = set()
    with click.progressbar(words) as wordsbar:
        for word in wordsbar:
            for p in prefixes:
                res.add(p + word)
                if deep == 2:
                    for s in suffixes:
                        res.add(p + word + s)
                        res.add(word + p + s)
                        res.add(word + '_' + p + s)
            if deep == 1:
                for s in suffixes:
                    res.add(word + s)
    return res


########
# MODE #
########

def tiny(f):
    """Get the approximative 10 most likely passwords"""
    words = set()
    
    numeric = ['', '1']
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
    res = case_variation(words, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res = common_variation(res, [], suffixes, 1)
    log.info(f"[*] {len(res)} candidates after adding suffixes: {' '.join(list(res)[:50])}")
    return res 

def short(f):
    """Get the approximative 100 most likely passwords"""
    words = set()
    
    numeric = ['', '1', '01', '123']
    special =  ['', '!']
    leet = {'a':['4'], 'e':['3'], 'i':['1'], 'o':['0']}
    
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.append(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words)} words imported: {' '.join(list(words))}")

    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case_variation(words, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res2 = leet_variation(res, leet, 1)
    log.info(f"[*] {len(res2)} candidates after leet substitution: {' '.join(list(res2)[:50])}")
    res2 = common_variation(res2, [], special, 1)
    # we avoid to have numbers from numeric AND leet
    res = common_variation(res, [], suffixes, 1) | res2
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
    
    prefixes = case_variation(tags, 3)
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case_variation(words, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res_num = leet_variation(res, leet_num, 1)
    res_spe = leet_variation(res, leet_spe, 1)
    log.info(f"[*] {len(res_num|res_spe)} candidates after leet substitution: {' '.join(list(res_num|res_spe)[:50])}")
    res = common_variation(res, prefixes, suffixes, 1) | common_variation(res_num, prefixes, special, 1) | common_variation(res_spe, prefixes, numeric, 1) 
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
    leet = {'a':['4', '@'], 'e':['3'], 'i':['1', '!'], 'o':['0'], 's':['$'], 't':['7']}

    name = f.readline().strip().lower()
    words.add(name)
    nicks = nickname_variation(name)
    log.info(f"[*] first word is assumed to be a name, {len(nicks)} nicknames were computed: {' '.join(list(nicks))}")
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.add(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words|nicks)} words imported: {' '.join(list(words|nicks))}")

    prefixes = case_variation(tags, 3)
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case_variation(words, 4)
    # we do this to avoid leet variation over nicknames
    res2 = res | case_variation(nicks, 3)
    log.info(f"[*] {len(res2)} candidates after case variation: {' '.join(list(res2)[:50])}")
    res2 |= leet_variation(res, leet, 2)
    log.info(f"[*] {len(res2)} candidates after leet substitution: {' '.join(list(res2)[:50])}")
    res = common_variation(res2, prefixes, suffixes, 1)
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
    leet = {'a':['4', '@'], 'e':['3'], 'i':['1', '!'], 'o':['0'], 's':['5', '$'], 't':['7'], 'g':['9']}

    name = f.readline().strip().lower()
    words.add(name)
    nicks = nickname_variation(name)
    log.info(f"[*] first word is assumed to be a name, {len(nicks)} nicknames were computed: {' '.join(list(nicks))}")
    for line in f.read().splitlines():
        # if a number is given, it is added to the numeric suffixes
        if line.isdigit():
            numeric.add(line)
        else:
            words.add( line.lower() )
    log.info(f"[*] {len(words|nicks)} words imported: {' '.join(list(words|nicks))}")

    prefixes = case_variation(leet_variation(tags, leet, 1), 3)
    suffixes = set([n + s for n in numeric for s in special])

    res = set()
    res = case_variation(words, 4)
    res |= case_variation(nicks, 3)
    log.info(f"[*] {len(res)} candidates after case variation: {' '.join(list(res)[:50])}")
    res |= leet_variation(res, leet, 2)
    log.info(f"[*] {len(res)} candidates after leet substitution: {' '.join(list(res)[:50])}")
    res = common_variation(res, prefixes, suffixes, 2)
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
