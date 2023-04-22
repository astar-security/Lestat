#!/usr/bin/python3

import time
import logging as log
import click

########
# INIT #
########

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

months_en = ['january','february','march','april','may','june','july','august','september','october','november','december']
months_nl = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']
months_fr = ['janvier','fevrier','mars','avril','mai','juin','juillet','aout','septembre','octobre','novembre','decembre']
months_es = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','setiembre','octubre','noviembre','dicembre']
seasons_en = ['spring', 'summer', 'autumn', 'winter' ]
seasons_nl = ['lente', 'zomer', 'herfst', 'winter' ]
seasons_fr = ['printemps', 'ete', 'automne', 'hivers' ]
seasons_es = ['primavera', 'verano', 'otono', 'invierno']
# merge all the known months and seasons names
months = set(months_en + months_fr + months_nl + months_es) 
moments = set(months_en + months_fr + months_nl + months_es + seasons_en + seasons_fr + seasons_nl + seasons_es)

def compute_suffixes():
    global months
    suffixes = ['']
    birthdates = []
    special = ['', '!', '.', '$']
    # years
    for y in map(str, range(1913, int(time.strftime("%Y"))+1)):
        # add 2013 13 
        suffixes += [i+j for i in [y, y[2:]] for j in special]
        if int(y) > 2009:
            # for 2017, add 2k17, 2K17
            suffixes += [i+j for i in ["2k"+y[2:], "2K"+y[2:]] for j in special]
        # months in format 01, 02, ...
        for m in [str(i).zfill(2) for i in range(1,13)]:
            # days in format 01, 02, ...
            for d in [str(i).zfill(2) for i in range(1,32)]:
                # add 311299 31-12-99 31/12/99 31121999 31-12-1999 31/12/1999 
                birthdates += [ d+m+y[2:], "-".join([d,m,y[2:]]), "/".join([d,m,y[2:]]), 
                        d+m+y, "-".join([d,m,y]), "/".join([d,m,y])]
                # add english version
                birthdates += [ m+d+y[2:], "-".join([m,d,y[2:]]), "/".join([m,d,y[2:]]), 
                        m+d+y, "-".join([m,d,y]), "/".join([m,d,y])]
                # add 3112 3112! 3112. 3112$ and 1231 1231! 1231. 1231$ as suffixes
                suffixes += [i+j for i in [d+m, m+d] for j in special]
         # months in format january, february, ...
        for m in months:
            # days in format 1, 2, ...
            for d in [str(i) for i in range(1,32)]:
                # 2Novembre 2novembre 
                birthdates += [ d+m, d+m.capitalize() ]
                # add 2Novembre22 2novembre22 2novembre2022 2Novembre2022
                birthdates += [ d+m.capitalize()+y[2:], d+m+y[2:], d+m+y, d+m.capitalize()+y]
                # add 2Nov22 2nov22 2nov2022 2Nov2022
                birthdates += [ d+m.capitalize()[:3]+y[2:], d+m[:3]+y[2:], d+m[:3]+y, d+m.capitalize()[:3]+y ]
    # add special char at the end
    birthdates += [ i+j for i in birthdates for j in special]
    suffixes = set(suffixes)
    bithdates = set(birthdates)
    return suffixes, birthdates

def derivate(moments):
    derivated = set('')
    with click.progressbar(moments) as momentsbar:
        for moment in momentsbar:
            # Add the 3 and 4 letters variation too : january -> jan, janu
            shortnames = [moment, moment[:3], moment[:4]]
            derivated.update(shortnames)
            # uppercase: JANUARY JAN
            derivated.update(map(str.upper,shortnames))
            # capitalize: January Jan
            derivated.update(map(str.capitalize,shortnames))
    return derivated

def combine(prefixes, birthdates, suffixes, output_file=None, hash_function=None, hashes=None):
    if output_file:
        with open(output_file, 'w') as f:
            for b in birthdates:
                f.write( b+'\n')
            with click.progressbar(prefixes) as prefixbar:
                 for p in prefixbar:
                    for s in suffixes:
                        # writing on the fly is faster than one big write
                        # but the output wordlist could have duplicates
                        f.write( p+s+'\n' )
    elif hash_function:
        result = {}
        for b in birthdates:
            h = hash_function(b)
            if h not in result and h in hashes:
                result[h] = b
        with click.progressbar(prefixes) as prefixbar:
             for p in prefixbar:
                for s in suffixes:
                    h = hash_function( candidate := p+s )
                    if h not in result and h in hashes:
                        result[h] = candidate
        return result
    else:
        dates = set()
        dates.update(birthdates)
        with click.progressbar(prefixes) as prefixbar:
            for p in prefixbar:
                for s in suffixes:
                    dates.add(p+s)
        return dates

def cook_dates(output_file=None, hash_function=None, hashes=None):
    global moments
    suffixes, birthdates = compute_suffixes()
    moments = derivate(moments)
    moments = combine(moments, birthdates, suffixes, output_file, hash_function, hashes)
    return moments

def main():
    output_file = "dates.wordlist"
    cook_dates(output_file)
    log.info(f"[+] Complete, {output_file} written")

if __name__ == '__main__':
    main()
