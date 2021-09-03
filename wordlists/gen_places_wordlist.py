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
log.info("[*] Import input file {input_filename}...")
f = None
places = None
try:
    f = open(input_filename)
    places = f.read().split('\n')[0:-1]
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

suffixes = set(suffixes)

########
# COOK #
########

log.info("[*] Computing combination for each place...")

with click.progressbar(places) as placesbar:
     for place in placesbar:
        place = place.lower()
        for s in suffixes:
            # derivate each candidate with various case lacanau Lacanau LACANAU lACANAU
            words.add( place+s )
            words.add( place.upper()+s )
            words.add( place.capitalize()+s )
            words.add( place[0:1] + place[1:].upper() + s )

log.info("[+] Complete")

##########
# EXPORT #
##########

# write the wordlist into a file
log.info(f"[*] Exporting to the file {export_filename}...")
with open(export_filename, 'w') as f:
    print(*(words), sep='\n', file=f)
log.info("[+] Export complete, all is finished")
