#!/usr/bin/python3

import time
import requests
import logging as log
import click

#########
# CONST #
#########

export_filename = 'names.wordlist'
input_filename = 'names.txt'

########
# INIT #
########

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

# get the list of common firstnames from various languages
log.info(f"[*] Import input file {input_filename}...")
f = None
names = None
try:
    f = open(input_filename)
    names = f.read().lower().split('\n')[0:-1]
    f.close()
except Exception as e:
    log.error(f"[!] Error: {e}")
    exit(1)
log.info("[+] Input file imported")

# init the wordlist
words = set()

suffixes = ['']
for m in [str(i).zfill(2) for i in range(1,13)]:
    for d in [str(i).zfill(2) for i in range(1,32)]:
        # add 3112 3112! 3112. 3112$ 1231 1231! 1231. 1231$
        suffixes += [ d+m, d+m+'!', d+m+'.', d+m+'$', m+d, m+d+'!', m+d+'.', m+d+'$' ]

for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
    # add 2013 2013! 2013. 2013$ 13 13! 13. 13$
    suffixes += [y, y+'!', y+'.', y+'$', y[2:], y[2:]+'!', y[2:]+'.', y[2:]+'$']

for d in map(str, range(10)):
    # simple digits 0 0! 0. 0$
    suffixes += [d, d+'!', d+'.', d+'$']

# common numbers
suffixes += ['123', '1234']

# french DOM/TOM
suffixes += ['971', '972', '973', '974', '975', '976', '984', '986', '987', '988']

suffixes = set(suffixes)

########
# COOK #
########

log.info("[*] Computing name derivation...")

prefix = set()
with click.progressbar(names) as namesbar:
    for name in namesbar:
        # prefix for eg Nicolas: nicolas, nic, nico, nini
        prefix.update([name, name[:3], name[:4], name[:2] + name[:2]])

log.info("[+] Derivation finished")
log.info("[*] Combine names and numbers...")

with open(export_filename, 'w') as f:
    with click.progressbar(prefix) as prefixbar:
         for p in prefixbar:
            for s in suffixes:
                # derivate each candidate with various case david David DAVID dAVID
                f.write( p+s+'\n' )
                f.write( p.upper()+s+'\n' )
                f.write( p.capitalize()+s+'\n' )
                f.write( p[0:1] + p[1:].upper() + s + '\n' )

log.info(f"[+] Complete, file {export_filename} written")
