#!/usr/bin/python3

import time
import logging as log
import click

#########
# CONST #
#########

export_filename = 'dates.wordlist'

months_en = [ "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "spring", "summer", "autumn", "winter" ]
months_nl = [ "januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december", "lente", "zomer", "herfst", "winter" ]
months_fr = [ "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre", "printemps", "ete", "automne", "hivers" ]

########
# INIT #
########

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

# merge all the known months names
months = [ months_en, months_fr, months_nl ]

# init the wordlist
words = set()

suffix = []
for y in map(str, range(1950, int(time.strftime("%Y"))+1)):
    # for 1988 add 1988, 1988!, 88, 88!
    suffix += ['', y, y + '!', y[2:], y[2:] + '!']
    if int(y) > 2009:
        # for 2017, add 2k17, 2K17, 2k17!, 2K17!
        suffix += ["2k" + y[2:], "2K" + y[2:], "2k" + y[2:] + '!', "2K" + y[2:] + '!']

suffix = set(suffix)

########
# COOK #
########

# for each year since 100 years ago to now
log.info("[*] Computing combination for each language...")

with click.progressbar(months) as monthsbar:
    for l in monthsbar:
        for m in l:
            # for december add december, dec
            prefix = ['', m.lower(), m.lower()[:3]]
            for p in prefix:
                for s in suffix:
                # derivate each candidate with various case
                    words.add( p+s )
                    words.add( p.upper()+s )
                    words.add( p.capitalize()+s )

log.info("[+] Complete")

##########
# EXPORT #
##########

# write the wordlist into a file
log.info(f"[*] Exporting to the file {export_filename}...")
with open(export_filename, 'w') as f:
    print(*(words), sep='\n', file=f)
log.info("[+] Export complete, all is finished")
