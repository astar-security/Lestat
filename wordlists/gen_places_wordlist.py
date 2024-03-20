#!/usr/bin/python3

import time
import logging as log
import click
import string

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

def asciize(word):
    """remove foreign characters from a given word"""
    asciize = str.maketrans("àäâąãảạầằẩắéèëêệěēếėęìïîḯĩıịĭỉòöôõōơộốőơờúùüûūůủüưýỹÿỳğçłśșňñľđḑḏðẕźżḩḥẖťṭț",
                            "aaaaaaaaaaaeeeeeeeeeeiiiiiiiiiooooooooooouuuuuuuuuyyyygclssnnlddddzzzhhhttt")
    asciize2 = str.maketrans({"œ":"oe", "ß":"ss", "æ":"ae"})
    return word.translate(asciize).translate(asciize2)

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

def ingest_places(input_file):
    # get the list of common places from various languages
    log.info(f"[*] Import input file {input_file}...")
    with open(input_file) as f:
        places = f.read().lower().split('\n')
    log.info("[+] Input file imported")
    return places

def compute_suffixes():
    suffixes = ['']
    special = ['', '!', '.', '$']
    # birthdates
    for m in [str(i).zfill(2) for i in range(1,13)]:
        for d in [str(i).zfill(2) for i in range(1,32)]:
            # add 3112 3112! 3112. 3112$ 1231 1231! 1231. 1231$
            suffixes += [i+j for i in [d+m, m+d] for j in special]
    # years
    for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
        # add 2013 2013! 2013. 2013$ 13 13! 13. 13$
        suffixes += [i+j for i in [y, y[2:]] for j in special]
    # digits
    suffixes += [i+j for i in map(str, range(10)) for j in special]
    # common numbers
    suffixes += [i+j for i in ['123', '1234'] for j in special]
    # french DOM/TOM
    suffixes += [i+j for i in ['971', '972', '973', '974', '975', '976', '984', '986', '987', '988'] for j in special]
    suffixes = set(suffixes)
    return suffixes

def getRoot(name):
    """remove numbers and punctuation from a giver word"""
    root = str.maketrans('', '', string.digits + string.punctuation)
    return name.translate(root)


def derivate(places):
    log.info("[*] Computing places derivation...")
    derivated = set()
    with click.progressbar(places) as placesbar:
        for place in placesbar:
            # remove accent
            asciized = asciize(place)
            # shortnames for eg: france, fr
            derivated.update([place, place[:2], asciized])
            # évry-sur-seine -> évrysurseine
            derivated |= shortname(place, 1)
            if asciized != place:
                derivated |= shortname(asciized, 1)
            # case
            derivated |= cases(derivated, 3)
    log.info("[+] Derivation finished")
    if '' in derivated:
        derivated.remove('')
    return derivated

def combine(prefixes, suffixes, output_file=None, hash_function=None, hashes=None):
    log.info("[*] Combine places and numbers...")
    if output_file:
        with open(output_file, 'w') as f:
            with click.progressbar(prefixes) as prefixbar:
                 for p in prefixbar:
                    for s in suffixes:
                        # writing on the fly is faster than one big write
                        # but the output wordlist could have duplicates
                        f.write( p+s+'\n' )
    elif hash_function:
        result = {}
        with click.progressbar(prefixes) as prefixbar:
             for p in prefixbar:
                for s in suffixes:
                    h = hash_function( candidate := p+s )
                    if h not in result and h in hashes:
                        result[h] = candidate
        return result
    else:
        places = set()
        with click.progressbar(prefixes) as prefixbar:
            for p in prefixbar:
                for s in suffixes:
                    places.add(p+s)
        return places

def cook_places(input_file, output_file=None, hash_function=None, hashes=None):
    places = ingest_places(input_file)
    suffixes = compute_suffixes()
    places = derivate(places)
    places = combine(places, suffixes, output_file, hash_function, hashes)
    return places

def main():
    input_file = 'places.txt'
    output_file = "places.wordlist"
    cook_places(input_file, output_file)
    log.info(f"[+] Complete, {output_file} written")

if __name__ == '__main__':
    main()
