#!/usr/bin/python3

import time
import re
import click
import string
from pathlib import Path

separators = r'[\-\'\ \._&/]'

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        'g':['9'],
        't':['7']
        }

def asciize(word):
    """remove foreign characters from a given word"""
    asciize = str.maketrans("àäâąãảạầằẩắéèëêệěēếėęìïîḯĩıịĭỉòöôõōơộốőơờúùüûūůủüưýỹÿỳğçłśșňñľđḑḏðẕźżḩḥẖťṭț",
                            "aaaaaaaaaaaeeeeeeeeeeiiiiiiiiiooooooooooouuuuuuuuuyyyygclssnnlddddzzzhhhttt")
    asciize2 = str.maketrans({"œ":"oe", "ß":"ss", "æ":"ae"})
    return word.translate(asciize).translate(asciize2)


def getRoot(name):
    """remove numbers and punctuation from a giver word"""
    root = str.maketrans('', '', string.digits + string.punctuation)
    return name.translate(root)


def dissect(words, deep):
    global separators
    """manage compound words"""
    res = set() 
    for word in words:
        parts = re.split(separators, word)
        # new-york => [new, york]
        if deep > 1 :
            # compute shortnames of each part
            for part in parts:
                res.update(shortname(part, deep-1))
        else:
            res.update(parts)
        # new-york => ny, j-l.lemenchon => jll
        res.add( ''.join([i[0:1] for i in parts]) )
        # saint tome & principe => sainttome
        res.add( ''.join(parts[0:2]) )
        if len(parts) > 1 and deep > 1:
            # new-york => NewYork
            res.add(''.join(map(str.capitalize,parts)))
            # saint tome & principe => sainttomeprincipe
            res.add( ''.join(parts) )
            # if there are two parts
            if len(parts) == 2:
                # trigram : gustave.limace => gli
                res.add( parts[0][0:1] + parts[1][0:2] )
                # username : david soria -> dsoria
                res.add( parts[0][0:1] + parts[1] )
                # jc-decaud => jcd
                res.add( parts[0] + parts[1][0] )
    return res

def shortname(word, deep):
    """compute common shortname/surname over a given word"""
    res = set([word])
    consonants = str.maketrans('','','aeiou')
    cleaned = getRoot(word)
    res.add(cleaned)
    l = len(cleaned)
    if l > 3 :
        # sebastien => seb
        res.add(cleaned[:3])
        # nicolas => nico
        res.add(cleaned[:4])
        if deep > 1:
            # christopher => chris
            res.add(cleaned[:5])
            # microsoft => micro
            res.add( cleaned[0:l//2+l%2] )
            # ffuyons => fuyons
            res.add( cleaned[1:] )
            # hendrick => hk, Boeing => bg
            res.add( cleaned[0] + cleaned[-1] )
    # if the name start with a consonant
    if l > 1 and cleaned[0] not in 'aeiou':
        if cleaned[1] in 'aeiouy':
            # lucille => lulu
            res.add( cleaned[:2] + cleaned[:2] )
        if deep > 1 :
            # remove voyels
            cons = cleaned.translate(consonants)
            l_cons = len(cons)
            if l_cons > 1:
                # Nike => nk
                res.add(cons[0:2])
                # Goldman => gld
                res.add( cons[0:3] )
    return res

# Attention je ne l'utilise plus, j'inclus direct shortname dans dissect
def nickname(word, deep):
    global separators
    res = set()
    words = [word]
    # if compound name
    if re.match(separators, word):
        words = dissect(word, deep)
    for w in words:
        res |= shortname(w, deep)
    del(words)
    return res


def numbers(deep):
    """compute a list of probable numbers"""
    res = set()
    # common numbers
    res.update(['01', '123'])
    # 0 -> 9
    res.update( [str(i) for i in range(10)] )
    if deep > 1 :
        # 50 years ago -> now : 1988 and 88
        res.update([str(i) for i in range(int(time.strftime("%Y"))-50, int(time.strftime("%Y"))+1)] )
        res.update([str(i)[2:] for i in range(int(time.strftime("%Y"))-50, int(time.strftime("%Y"))+1)] )
    if deep > 2 :
        # 00 -> 99
        res.update([str(i).zfill(2) for i in range(100)])
        # add special french DOM numbers
        res.update(['971', '972', '973', '974', '975', '976', '984', '986', '987', '988'])
        # 2k10 -> now
        res.update(["2k"+str(i)[2:] for i in range(2010,int(time.strftime("%Y"))+1)] )
        # 2K10 -> now
        res.update(["2K"+str(i)[2:] for i in range(2010,int(time.strftime("%Y"))+1)] )
    if deep > 3 :
        for day in range(1,32):
            for month in range(1,13):
                # 3112
                res.add(f"{day:02}{month:02}")
                if deep > 4:
                    # 1231
                    res.add(f"{month:02}{day:02}")
    return res

def cases(words, deep):
    """compute case variations over a list of words"""
    res = set()
    if deep > 4 :
        # all the posible combinations
        for word in words :
            l = len(word)
            word_l = word.lower()
            for mask in [bin(i)[2:].zfill(l) for i in range(2**l)] :
                res.add(''.join([ [word_l[c].upper(), word_l[c]][mask[c] == '0'] for c in range(l) ]))
    else:
        for word in words :
            # david, DAVID, David, dAVID
            variation = [word, word.lower(), word.capitalize(), word.upper(), word.capitalize().swapcase()]
            res.update( variation[0:1+deep] )
    return res


def leetspeak(words, deep, leet_swap):
    """p3rf0rm 1337 5ub57!7u7!0n over a list of words"""
    res = set()
    first_pass = []
    for word in words:
        res.add(word)
        # if the word is composed of alphabet and more than one letter
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

def combine(words, comb):
    res = set()
    sep = ['']
    if comb == 4:
        sep = ['', '-', '_']
    l = len(words)
    p = list(words)
    for w1 in range(l):
        for w2 in range(w1+1, l):
            for s in sep:
                res.add(p[w1]+s+p[w2])
                res.add(p[w2]+s+p[w1])
    del(p)
    return res

def affix(words, deep, prefixes, suffixes):
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

@click.command()
@click.option('--nick', default=0, help='Guess shortname/nicknames: 0 disabled, 1 (jean-baptiste -> jean, baptiste, jb, jeanbaptiste), 2 (jean-baptiste -> JeanBaptiste, jba, jbaptiste, jeanb, bap, bapt, baba, jea, jeje), 3 (aptiste, bapti, bp, be, bpt, ean, jn)')
@click.option('--case', default=0, help='Set the level of case variation: 0 (keep original), 1 (original + david), 2 (add David), 3 (add DAVID), 4 (add dAVID), 5 (all the possible variations)')
@click.option('--leet', default=0, help='Set the number of substitutions: 0 disabled, 1 letter, 2 letters')
@click.option('--num', default=0, help='Add numeric suffixes: 0 disabled, 1 (0->9 01 123), 2 (50 last years: 1988 and 88 formats), 3 (complete 00->99 and 2k18 years format), 4 (add birthdates), 5 (add english birthdates)')
@click.option('--punc', default=0, help='Add punctuation: 0 disabled, 1 (!), 2 (add $ . -), 3 (add * ? & _)')
@click.option('--pref', default=0, help='Add prefixes: 0 disabled, 1 (pass), 2 (add adm), 3 (add admin pwd)')
@click.option('--comb', default=0, help='Add combinations between words: 0 (disabled), 1 (2x2 before case and nick variations), 2 (2x2 after nickname variation), 3 (2x2 after case computation), 4 (2x2 with separators - and _)')
@click.argument('word')
def main(word, nick, case, leet, num, punc, pref, comb):
    """
    Compute string variations over words (separated with comma) or a file with one word per line
    """
    global leet_swap
    prefixes = ['']
    inter = ['']
    final = ['']
    numerals = set([''])
    combinations = ['']
    words = set([word])
    result = set()
    lines = None
    # check if word is a word or a file
    if Path(word).is_file():
        with open(word) as f:
            lines = list(map(str.strip,f.readlines()))
    # check if there is multiple words separated with comma
    if ',' in word:
        lines = word.split(',')
    if lines :
        words = set([i for i in lines if not i.isdigit()])
        numerals.update([i for i in lines if i.isdigit()])
        if comb == 1:
            words.update(combine(words, comb))
    # treat compound words
    if nick > 0 :
        words.update(dissect(words, nick))
    if comb == 2:
        words.update(combine(words, comb))
    # case
    if case > 0 :
        words.update(cases(words, case))
    if comb >= 3:
        words.update(combine(words, comb))
    # leet
    if leet > 0 :
        words.update(leetspeak(words, leet, leet_swap))
    # numerics
    if num > 0 :
        numerals.update(numbers(num))
    # punctuation
    if punc > 0 :
        inter = ['_','-'][0:punc]
        final = ((''), ('','!'), ('','!','$','.'), ('','!','$','.','*','?','&','%'))[punc]
    # prefixes
    if pref > 0 :
        prefixes = set([['pass'], ['pass', 'adm'], ['pass', 'adm', 'pwd', 'admin']][pref-1])
        if case > 0 :
            prefixes.update([i.upper() for i in prefixes])
            if case > 1 :
                prefixes.update([i.capitalize() for i in prefixes])
        prefixes.add('')

    for prefix in prefixes:
        for word in words:
            for numeral in numerals:
                # PassDavid1988
                result.add(prefix + word + numeral)
                if punc :
                    for p in inter:
                        if prefix != '':
                            # Pass_David1988
                            result.add(prefix + p + word + numeral)
                        if numeral != '':
                            # PassDavid_1988
                            result.add(prefix + word + p + numeral)
                    for p in final:
                        result.add(prefix + word + numeral + p)
                        if punc > 1 and numeral != '':
                            result.add(prefix + word + p + numeral)

    #result.update([prefix + word + numeral + p1 for prefix in prefixes for word in result for numeral in numerals for p1 in final])
    
    print(*(result),sep='\n')
    #print(f"{len(result)} candidates computed")

if __name__ == '__main__':
    main()

