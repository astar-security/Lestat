#!/usr/bin/python3

import argparse
import sys

def readHashFile(hashfile):
    f = open(hashfile)
    hashes = f.read().split('\n')[:-1]
    ntlm ={"cracked":{}, "safe":{}}
    f.close()
    for i in hashes:
        try:
            h = i.split(':')
            ntlm["safe"][h[3].upper()] = h[0].lower()
        except Exception as e:
            pass
    return hashes, ntlm

def searchLeaked(leakfile, ntlm, verbose):
    leak = open(leakfile,"r")
    cpt = 0
    print("[*] Checking leaked database against hashes (long) ...", file=sys.stderr)
    for line in leak:
        if line[:-1] in ntlm["safe"]:
            ntlm["cracked"][line[:-1]] = ntlm["safe"][line[:-1]]
            cpt += 1
            del(ntlm["safe"][line[:-1]])
            if verbose:
                print(line[:-1], ntlm["cracked"][line[:-1]])
    print(f"{cpt} compromised", file=sys.stderr)
    leak.close()

def export(ntlm, john_result_file='', output=''):
    john = ''
    if john_result_file:
        f = open(john_result_file)
        john = f.read().lower()
        f.close()
    if output:
        f = open(output, "a+")
    cpt = 0
    for c in ntlm["cracked"]:
        line = f"{ntlm['cracked'][c]}:<LeakTheWeak>:LEAK:NOLM:{c}:::"
        if ntlm["cracked"][c] not in john:
            if output :
                f.write(line+'\n')
            else:
                print(line)
            cpt += 1
    if john_result_file:
        print(f"New {cpt} compromised")
    if output:
        f.close()

def main():
    parser = argparse.ArgumentParser(description='List accounts compromised in public leaked NTLMs', add_help=True)
    parser.add_argument('-w', '--write', action="store", dest="path", default='', 
            help='A path to store the results. Default is stdout')
    parser.add_argument('HASH_FILE', action="store", 
            help="The result file of impacket-secretsdump")
    parser.add_argument('-j', '--john', action="store", dest="john_file", default='',
            help="If used, only the accounts not cracked by john are displayed")  
    parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", default=False,
            help="display the cracked accounts in real time")
    parser.add_argument('LEAK_FILE', action="store",  
            help="The wordlist containing the NTLM leaked")   
    args = parser.parse_args()
    
    hashes, ntlm = readHashFile(args.HASH_FILE)
    searchLeaked(args.LEAK_FILE, ntlm, args.verbose)
    export(ntlm, args.john_file, args.path)
    


if __name__ == '__main__':
    main()

