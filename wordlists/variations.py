#!/usr/bin/python3

import time
import re
import click
import string

separators = r'.*[\-\'\ \._&/]'

def asciize(word):
    """remove special characters"""
    asciize = str.maketrans("àäâąãảạầằẩắéèëêệěēếėęìïîḯĩıịĭỉòöôõōơộốőơờúùüûūůủüưýỹÿỳğçłśșňñľđḑḏðẕźżḩḥẖťṭț",
                            "aaaaaaaaaaaeeeeeeeeeeiiiiiiiiiooooooooooouuuuuuuuuyyyygclssnnlddddzzzhhhttt")
    asciize2 = str.maketrans({"œ":"oe", "ß":"ss", "æ":"ae"})
    return word.translate(asciize).translate(asciize2)

def dissect(word, deep):
    global separators
    """manage compound words"""
    res = set() 
    parts = re.split(separators, word)
    # new-york => [new, york]
    res.update(parts)
    # new-york => ny, j-l.lemenchon => jll
    res.add( ''.join([i[0:1] for i in parts]) )
    # saint tome & principe => sainttome
    res.add( ''.join(parts[0:2]) )
    if deep > 1:
        # new-york => NewYork
        res.add(''.join(map(str.capitalize,parts)))
        # saint tome & principe => sainttomeprincipe
        res.add( ''.join(parts) )
    # if there are two parts
    if len(parts) == 2:
        # trigram : gustave.limace => gli
        res.add( parts[0][0:1] + parts[1][0:2] )
        if deep > 1 :
            # jc-decaud => jcd
            res.add( parts[0] + parts[1][0] )
    return res

def shortname(word, deep):
    res = set()
    res.add(word)
    consonants = str.maketrans('','','aeiou')
    root = str.maketrans('', '', string.digits + string.punctuation)
    cleaned = word.translate(root)
    res.add(cleaned)
    l = len(cleaned)
    if l > 3 :
        # sebastien => seb
        res.add(cleaned[:3])
        # nicolas => nico
        res.add(cleaned[:4])
        # hendrick => hk, Boeing => bg
        res.add( cleaned[0] + cleaned[-1] )
        if deep > 1:
            # christopher => chris
            res.add(cleaned[:5])
            # microsoft => micro
            res.add( cleaned[0:l//2+l%2] )
            # ffuyons => fuyons
            res.add( cleaned[1:] )
    # if the name start with a consonant
    if l > 1 and cleaned[0] not in 'aeiou':
        if cleaned[1] in 'aeiouy':
            # lucille => lulu
            res.add( cleaned[:2] + cleaned[:2] )
        # remove voyels
        cons = cleaned.translate(consonants)
        l_cons = len(cons)
        if l_cons > 1:
            # Nike => nk
            res.add(cons[0:2])
            if deep > 1:
                # Nintendo => nd
                res.add(cons[0]+cons[-1])
                # Goldman => gld
                res.add( cons[0:(l_cons//2)+(l_cons%2)] )
    return res

def nickname(word, deep):
    res = set()
    words = [word]
    # if compound name
    if re.match(separators, word):
        words = dissect(word, deep)
    for word in words:
        res |= shortname(word, deep)
    del(words)
    return res


def case(words, deep):
    res = set()
    for word in words:
        # david, DAVID, David, dAVID
        variation = [word, word.upper(), word.capitalize(), word.capitalize().swapcase()]
        res.update( variation[0:deep] )
    return res


def leet(words, deep, leet_swap):
    """p3rf0rm 1337 5ub57!7u7!0n"""
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


