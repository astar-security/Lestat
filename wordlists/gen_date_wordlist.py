#!/usr/bin/python3

import time

months_en = [ "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "spring", "summer", "autumn", "winter" ]
months_nl = [ "januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december", "lente", "zomer", "herfst", "winter" ]
months_fr = [ "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre", "printemps", "ete", "automne", "hivers" ]

months = [ months_en, months_fr, months_nl ]

words = set()
for year in range(1950, int(time.strftime("%Y"))+1):
    y = str(year)
    suffix = ['', y, y + '!', y[2:], y[2:] + '!']
    for l in months:
        for m in l:
            prefix = ['', m, m.upper(), m.capitalize(), m[:3], m[:3].upper(), m[:3].capitalize()]
            for p in prefix:
                for s in suffix:
                    words.add( p+s )        

with open('dates.wordlist', 'w') as f:
    print(*(words), sep='\n', file=f)
