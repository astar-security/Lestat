#!/usr/bin/python3

import time
import requests
import logging as log
import click

#########
# CONST #
#########

export_filename = 'names.wordlist'

########
# INIT #
########

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

# useful for voyel substitution: david -> dvd, julia -> jl, roxane -> rxn
root = str.maketrans('','','aeiouy')

# get the list of common firstnames from various languages
log.info("[*] Requesting firstnames list from github...")
r = requests.get("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt")
if not r.ok:
    log.error("[!] download failed")
    exit(1)
log.info("[+] list downloaded")

# the list of firstnames
names = r.text.split("\n")

# init the wordlist
words = set()

birthdates = []
for m in [str(i).zfill(2) for i in range(1,13)]:
    for d in [str(i).zfill(2) for i in range(1,32)]:
        birthdates += [ d+m, d+m+'!', m+d, m+d+'!' ]

for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
    birthdates += ['', y, y + '!', y[2:], y[2:] + '!']

birthdates = set(birthdates)

########
# COOK #
########

log.info("[*] Computing combination for each name...")

with click.progressbar(names) as namesbar:
     for name in namesbar:
        name = name.lower()
        # prefix for eg Nicolas: nicolas, nic, nico, nini, ncls
        prefix = [name, name[:3], name[:4], name[:2] + name[:2], name.translate(root)]
        for p in prefix:
            for s in birthdates:
                # derivate each candidate with various case
                words.add( p+s )
                words.add( p.upper()+s )
                words.add( p.capitalize()+s )
                words.add( p[0:1] + p[1:].upper() + s )

log.info("[+] Complete")

##########
# EXPORT #
##########

# write the wordlist into a file
log.info(f"[*] Exporting to the file {export_filename}...")
with open(export_filename, 'w') as f:
    print(*(words), sep='\n', file=f)
log.info("[+] Export complete, all is finished")
