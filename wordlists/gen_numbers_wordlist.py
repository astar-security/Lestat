#!/usr/bin/python3

import logging as log
import click

# init logging format
log.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', level=log.INFO)

def cook_numbers(limit, output_file=None, hash_function=None, hashes=None):
    if output_file:
        with open(output_file, 'w') as f:
            for i in range(1,limit+1):
                with click.progressbar(range(10**i)) as numbersbar:
                    for j in numbersbar:
                        f.write( str(j).zfill(i) + '\n' )
    elif hash_function:
        result = {}
        for i in range(1,limit+1):
            with click.progressbar(range(10**i)) as numbersbar:
                for j in numbersbar:
                    h = hash_function( candidate := str(j).zfill(i) )
                    if h not in result and h in hashes:
                        result[h] = candidate
        return result
    else:
        numbers = []
        for i in range(1,limit+1):
            with click.progressbar(range(10**i)) as numbersbar:
                for j in numbersbar:
                    number.append(str(j).zfill(i) )
        return numbers

def main():
    output_file = "numbers.wordlist"
    cook_numbers(8, output_file)
    log.info(f"[+] Complete, {output_file} written")

if __name__ == '__main__':
    main()
