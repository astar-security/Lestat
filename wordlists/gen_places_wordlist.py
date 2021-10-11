#!/usr/bin/python3

import time
import logging as log
import click

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

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

def asciize(name):
    asciize = str.maketrans("àäâąãảạầằẩắéèëêệěēếėęìïîḯĩıịĭỉòöôõōơộốőơờúùüûūůủüưýỹÿỳğçłśșňñľđḑḏðẕźżḩḥẖťṭț",
                            "aaaaaaaaaaaeeeeeeeeeeiiiiiiiiiooooooooooouuuuuuuuuyyyygclssnnlddddzzzhhhttt")
    asciize2 = str.maketrans({"œ":"oe", "ß":"ss", "æ":"ae"})
    return name.translate(asciize).translate(asciize2)

def unseparate(name):
    separator = (' ', '/', '-', ' & ', "'")
    unseparate = str. maketrans('','',(" /-&'"))
    res = [name.translate(unseparate)]
    for i in separator:
        if len((s := name.split(i))) > 1:
            res += s
            res.append(''.join([i[0:1] for i in s]))
            res.append(''.join(s))
            res.append(''.join(map(str.capitalize,s)))
    return res

def derivate(places):
    log.info("[*] Computing places derivation...")
    derivated = set()
    with click.progressbar(places) as placesbar:
        for place in placesbar:
            # remove accent
            asciized = asciize(place)
            # shortnames for eg: france, fr
            shortnames = [place, place[:2], asciized]
            # évry-sur-seine -> évrysurseine
            shortnames += unseparate(place)
            shortnames += unseparate(asciized)
            derivated.update(shortnames)
            # uppercase
            derivated.update(map(str.upper,shortnames))
            # capitalize
            derivated.update(map(str.capitalize,shortnames))
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
