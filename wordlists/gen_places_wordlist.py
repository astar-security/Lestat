#!/usr/bin/python3

import time
import requests
import logging as log
import click

#########
# CONST #
#########

export_filename = 'places.wordlist'
input_filename = 'places.txt'

########
# INIT #
########

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

# get the list of common places : cities and countries
log.info(f"[*] Import input file {input_filename}...")
f = None
places = None
try:
    f = open(input_filename)
    places = f.read().lower().split('\n')[0:-1]
    f.close()
except Exception as e:
    log.error(f"[!] Error: {e}")
    exit(1)
log.info("[+] Input file imported")

# init the wordlist
words = set()

# init suffixes based on years and zip code number
suffixes = []
for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
    # add 2013 2013! 2013. 2013$ 13 13! 13. 13$
    suffixes += ['', y, y+'!', y+'.', y+'$', y[2:], y[2:]+'!', y[2:]+'.', y[2:]+'$']

for d in map(str, range(10)):
    # add dimple digit 0 0! 0. 0$
    suffixes += [d, d+'!', d+'.', d+'$']

# common numbers
suffixes += ['123', '1234']

# french DOM/TOM
suffixes += ['971', '972', '973', '974', '975', '976', '984', '986', '987', '988']

suffixes = set(suffixes)

########
# COOK #
########

log.info("[*] Computing combination for each place...")

with open(export_filename, 'w') as f:
    with click.progressbar(places) as placesbar:
         for place in placesbar:
            for s in suffixes:
                # derivate each candidate with various case lacanau Lacanau LACANAU lACANAU
                f.write( place+s+'\n' )
                f.write( place.upper()+s+'\n' )
                f.write( place.capitalize()+s+'\n' )
                f.write( place[0:1] + place[1:].upper() + s + '\n' )

log.info(f"[+] Complete, file {export_filename} writtent")

