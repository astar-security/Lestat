#!/usr/bin/python3

import argparse
import sys
import itertools
import time
import re
import click
import select

leet_swap = {
        's':['5','$'],
        'e':['3'],
        'a':['4','@'],
        'o':['0'],
        'i':['1','!'],
        'g':['9'],
        't':['7']
        }

common_suffix = [
        "!",
        "@",
        "$",
        "%",
        "&",
        "*",
        "?",
        ".",
        ""
        ]

list_profile = {
    "default": {
        "nickname": False,
        "permutation" : True, 
        "numeric_conv" : True, 
        "birthdate" : False,
        "nickname_user" : False
    }, 
    "user": {
        "nickname": True, 
        "permutation" : False,
        "numeric_conv" : False,
        "birthdate" : True, 
        "nickname_user" : True
    }
}

profile = "default"
config = list_profile[profile]


# 2010 -> now
common_numeric  = [str(i) for i in range(2010,int(time.strftime("%Y"))+1)]
# 00 -> 20
common_numeric += [str(i)[-2:] for i in range(2000,int(time.strftime("%Y"))+1)]
# 2k10 -> now
common_numeric += ["2k"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)]
# 2K10 -> now
common_numeric += ["2K"+str(i)[-2:] for i in range(2010,int(time.strftime("%Y"))+1)]
# 0 -> 9
common_numeric += [str(i) for i in range(10)]
common_numeric += ['123', '1234'] + ['']

def common_words(): 
    result = [""]
    if profile != "user": 
        result += [
            "pw",
            "pwd",
            "sys",
            "admin",
            "pass",
            "Pass",
            "Admin",
            "adm",
            "Adm"
            ]
    return result

def birth_date(): 
    result = []
    for day in range(1,31): 
        for month in range(1,12): 
            result.append(f'{day:02}{month:02}')
    return result

def leet_variation(words):
    global leet_swap
    res = set()
    first_pass = []
    for word in words: 
        res.add(word)
        needles = [c for c in leet_swap.keys() if c in word.lower()]
        for i in range(len(needles)):
            nee1 = needles[i]
            for sub in leet_swap[nee1]:
                first_pass.append(re.sub(nee1, sub, word, flags=re.I))
            res |= set(first_pass)
            
            for j in range(i+1,len(needles)):
                nee2 = needles[j]
                for word2 in first_pass:
                    for sub in leet_swap[nee2]:
                        res.add(re.sub(nee2, sub, word2, flags=re.I))
            first_pass = []

    return res

def common_variation(word):
    global common_numeric
    global common_suffix
    words = common_words()
    if config["birthdate"] : 
        common_numeric += birth_date()
    res = set()
    for i in common_suffix:
        for j in common_numeric:
            for k in words:
                # common + root + numeric + suffix
                res.add(k + word + j + i)
                if word != "": 
                    # root + common + numeric + suffix
                    res.add(word + k + j + i)
    return res



def nickname_variation(word, company=False): 
    res = set()
    res.add( word )
    l = len( word )

    # if compound name
    if re.match(r'.*[-\ \._]', word): 
        parts = re.split(r'[\-\ \._]',word)
        # j-l.melenchon => jlm; general electric => ge
        res.add( ''.join([i[0:1] for i in parts]) )
        if len(parts[0]) < 3 :
            # jc-decaud => jcd; fx.demaison => fxd
            if len(parts) == 2 :
                res.add( parts[0]+parts[1][0] )
            # ch-toulouse => chtoulouse
            res.add( ''.join(parts) )

        if config["nickname_user"] and not company: 
            # d.soria => soria; 
            for part in parts:
                if len(part) > 1:
                    res.add( part )
                    res.update(nickname_variation(part))
            
            # Gustave Limace => GLI; 
            if len(parts) == 2 :
                res.add(parts[0][0]+parts[1][:2])

    else: 
        if not config["nickname_user"] or company: 
            # first and last char
            if l > 2 and word.isalpha() and word[-1] not in 'aeiou':
                res.add(word[0] + word[-1])
            # if doesn't start with vowel
            if word[0] not in 'aeiouy' and word.isalpha():
                # sub vowels
                subbled = re.sub(r'[aeiouyAEIOUY]','',word)
                l_subbled = len(subbled)
                if l_subbled > 1 :
                    res.add(subbled)
                # first half of vowels subbing : nikolas => NK
                if l_subbled > 3 :
                    res.add(subbled[0:l_subbled//2+l_subbled%2])

        # first half 
        if l > 3 and word.isalpha() :    
            res.add(word[0:l//2+l%2])



    return list(res)

def join_variation(word1, word2):
    res = set()
    # lower lower
    res.add(f'{word1}{word2}')
    # lower Capi
    res.add(f'{word1}{word2.capitalize()}')
    # lower UPPER
    res.add(f'{word1}{word2.upper()}')
    # Capi lower
    res.add(f'{word1.capitalize()}{word2}')
    # Capi Capi
    res.add(f'{word1.capitalize()}{word2.capitalize()}')
    # Capi UPPER
    res.add(f'{word1.capitalize()}{word2.upper()}')
    # UPPER lower
    res.add(f'{word1.upper()}{word2}')
    # UPPER Capi
    res.add(f'{word1.upper()}{word2.capitalize()}')
    # UPPER UPPER
    res.add(f'{word1.upper()}{word2.upper()}')   
    return res


def combine(words):
    global common_numeric
    res = set()
    tmp_res = set()
    selection = []
    tmp_selection = []
    company_nicks = None 
    for word in words:
        if word.isdigit() and config["numeric_conv"] :
            common_numeric.append(word)
        else:
            selection.append(word)

    if config["nickname"] : 
        for word in selection: 
            tmp_selection += list(nickname_variation(word))
        selection = tmp_selection

    if config["company"] : 
        nicknames = nickname_variation(config["company"], True)
        for nick in nicknames: 
            for word in selection + ['']: 
                res |= join_variation(nick, word)
                res |= join_variation(word, nick)

    if config["permutation"] : 
        selection.append('')
        for p in itertools.permutations(selection, 2): 
            res |= join_variation(*p)

    else : 
        for word in selection:
            nicknames = nickname_variation(word)
            for nick in nicknames:
                res.add( nick )
                res.add( nick.upper() )
                res.add( nick.capitalize() )

    sys.stderr.write(f"[*] {len(res)} unique words after mixing case and combinations: {res}\n")
    return res

def load_profile(args): 
    global config
    global profile
    if args.users : 
        profile = "user"
        config = list_profile[profile]

    config["company"] = False
    if args.company : 
        config["company"] = args.company.lower()

def mangle(words_file, args):
    """get the base words then apply variations"""
    load_profile(args)
    words = words_file.read().lower().splitlines() 
    sys.stderr.write(f"[*] {len(words)} base words: {words}\n")
    # combine words
    words = combine(words)
    tot = 0
    with click.progressbar(words, label="[*] Computing variations ...", file=sys.stderr) as wordsbar:
        for word in wordsbar:
            mangled = common_variation(word)
            mangled = leet_variation(mangled)
            tot += len(mangled)
            print(*(mangled), sep='\n')

    sys.stderr.write(f"[*] {tot} candidates computed after variations\n")

def gotSTDIN():
    return select.select([sys.stdin,],[],[],0.0)[0];

def main():
    stdin_mode = gotSTDIN()
    parser = argparse.ArgumentParser(description='Derivation of a wordlist to make a efficient crack dictionnary', add_help=True)
    if not stdin_mode: 
        parser.add_argument('input_file', action="store", help='Specify a wordlist file, if not, stdin is read')
    parser.add_argument('--users', action="store_true", dest="users", default=False, 
    help='Treat the input as a list of user, (limit the variations and add specifics ones like birth date)')
    parser.add_argument('--company', dest="company", 
    help='More variations are apply to the company name (do not add it to your list)')
    args = parser.parse_args()

    if stdin_mode:
        words_file = sys.stdin
        mangle(words_file, args)
    else: 
        with open(args.input_file, "r") as words_file:
            mangle(words_file, args)


if __name__ == '__main__':
    main()
