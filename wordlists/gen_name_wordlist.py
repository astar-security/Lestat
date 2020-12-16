#!/usr/bin/python3

import time
import requests

root = str.maketrans('','','aeiouy')

r = requests.get("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt")
names = r.text.split("\n")
words = set()
for year in range(int(time.strftime("%Y"))-100, int(time.strftime("%Y"))+1):
    y = str(year)
    suffix = ['', y, y + '!', y[2:], y[2:] + '!']
    for name in names:
        name = name.lower()
        prefix = [name, name[:3], name[:4], name[:2] + name[:2], name.translate(root)]
        for p in prefix:
            for s in suffix:
                words.add( p+s )
                words.add( p.upper()+s )
                words.add( p.capitalize()+s )

with open('names.wordlist', 'w') as f:
    print(*(words), sep='\n', file=f)
