#!/usr/bin/python3

import time
import logging as log
import click

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

def ingest_names(input_file):
    # get the list of common firstnames from various languages
    log.info(f"[*] Import input file {input_file}...")
    with open(input_file) as f:
        names = f.read().lower().split('\n')[0:-1]
    log.info("[+] Input file imported")
    return names

def compute_suffixes():
    suffixes = ['']
    # birthdates
    for m in [str(i).zfill(2) for i in range(1,13)]:
        for d in [str(i).zfill(2) for i in range(1,32)]:
            # add 3112 3112! 3112. 3112$ 1231 1231! 1231. 1231$
            suffixes += [ d+m, d+m+'!', d+m+'.', d+m+'$', m+d, m+d+'!', m+d+'.', m+d+'$' ]
    # years
    for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
        # add 2013 2013! 2013. 2013$ 13 13! 13. 13$
        suffixes += [y, y+'!', y+'.', y+'$', y[2:], y[2:]+'!', y[2:]+'.', y[2:]+'$']
    # digits
    for d in map(str, range(10)):
        # simple digits 0 0! 0. 0$
        suffixes += [d, d+'!', d+'.', d+'$']
    # common numbers
    suffixes += ['123', '1234']
    # french DOM/TOM
    suffixes += ['971', '972', '973', '974', '975', '976', '984', '986', '987', '988']
    suffixes = set(suffixes)
    return suffixes

def derivate(names):
    log.info("[*] Computing name derivation...")
    derivated = set()
    with click.progressbar(names) as namesbar:
        for name in namesbar:
            # shortnames for eg Nicolas: nicolas, nic, nico, nini
            shortnames = [name, name[:3], name[:4], name[:2] + name[:2]]
            derivated.update(shortnames)
            # uppercase: NICOLAS, NIC, NICO, NINI
            derivated.update(map(str.upper,shortnames))
            # capitalize: Nicolas, Nic, Nico, Nini
            derivated.update(map(str.capitalize,shortnames))
            # first lower then upper: nICOLAS, nIC, nICO, nINI
            derivated.update([i[0] + i[1:].upper() for i in shortnames])
    log.info("[+] Derivation finished")
    return derivated

def combine(prefixes, suffixes, output_file=None, hash_function=None, hashes=None):
    log.info("[*] Combine names and numbers...")
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
        names = set()
        with click.progressbar(prefixes) as prefixbar:
            for p in prefixbar:
                for s in suffixes:
                    names.add(p+s)
        return names

def cook_names(input_file, output_file=None, hash_function=None, hashes=None):
    names = ingest_names(input_file)
    suffixes = compute_suffixes()
    names = derivate(names)
    names = combine(names, suffixes, output_file, hash_function, hashes)
    return names

def main():
    input_file = 'names.txt'
    output_file = "names.wordlist"
    cook_names(input_file, output_file)
    log.info(f"[+] Complete, {output_file} written")

if __name__ == '__main__':
    main()
