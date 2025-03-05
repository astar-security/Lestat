#!/usr/bin/python3

import argparse
import csv
import matplotlib.pyplot as plt
import os
import re
import io


def CSV2Stats(csvfilename):
    print("[*] Reading the CSV input file")
    with open(csvfilename, newline='') as csvfile:
        try :
            reader = csv.DictReader(csvfile, delimiter=';')
            print("[+] Input file imported and parsed")
            fields = []
            for field in reader:
                fields.append(field)
            return fields
        except Exception as e:
            print(f"[!] Error during CSV parsing : {e}")
            exit(1)


def exportCharts(reader, chartpath, transparency):
    """produce charts in PNG format"""

    # creating path to write charts if it does not exist
    if not os.path.exists(chartpath):
        os.makedirs(chartpath)

    # used to maintain the same scale between 'all accounts' and 'active accounts' cases
    max_length = 0
    max_top = 0
    max_top_p = 0
    max_charset = 0

    charts = {}
    for field in reader:
        name = field['field']
        charts[name] = []
        print(f"[*] Making the charts for {name}...")
        charts[name].append(compromisedPie(field, chartpath, transparency))
        filename, max_lenght = lengthCompare(field, chartpath, transparency, max_length)
        charts[name].append(filename)
        filename, max_charset = charsetCompare(field, chartpath, transparency, max_charset)
        charts[name].append(filename)
        filename, max_top = frequentPasswords(field, chartpath, transparency, max_top)
        charts[name].append(filename)
        filename, max_top_p = frequentPatterns(field, chartpath, transparency, max_top_p)
        charts[name].append(filename)
        charts[name].append(compromisedReasonPie(field, chartpath, transparency))
        charts[name].append(robustnessBar(field, chartpath, transparency))
    return charts

def compromisedPie(field, chartpath, transparency):
    name = field['field']
    fig, ax = plt.subplots()
    values = [ int(field['compromised accounts']), int(field['safe accounts']) ]
    labels = [ 'compromised accounts', 'safe accounts' ]
    colors = [ '#dd0000', '#00c800' ]
    ax.pie(values, labels=labels, colors=colors, autopct=lambda p : '{:,.0f}% ({:,.0f})'.format(p,p * sum(values)/100), wedgeprops={"edgecolor":"white",'linewidth': 1, 'linestyle': 'solid', 'antialiased': True} )
    ax.set_title(f"Overall results for {name}")
    plt.tight_layout()
    dest = f"{chartpath}/main_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches="tight", transparent=transparency)
    #print("[+] Overall results chart created")
    return dest

def compromisedReasonPie(field, chartpath, transparency):
    name = field['field']
    fig, ax = plt.subplots()
    reason_colors = {"seconds": '#bb0000',
                     "minutes": '#ff0000',
                     "hours": '#ff6400',
                     "days": '#ffc800'}
    values = []
    labels = []
    colors = []
    regex = r"cracked because (.+?) \((.+?)\)"
    for f in field:
        match = re.search(regex, f)
        if match:
            num = (int(field[f]))
            # on néglige les valeurs trop peu significatives
            if num / (int(field['compromised accounts']))*100 >=1:
                values.append(num)
                labels.append(match.group(1))
                colors.append(reason_colors[match.group(2)])
    ax.pie(values, labels=labels, colors=colors, autopct=lambda p : '{:,.0f}% ({:,.0f})'.format(p,p * sum(values)/100), wedgeprops={"edgecolor":"white",'linewidth': 1, 'linestyle': 'solid', 'antialiased': True} )
    ax.set_title(f"Reasons of weakness for {name}")
    plt.tight_layout()
    dest = f"{chartpath}/weaknesses_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches='tight', transparent=transparency)
    #print("[+] Reasons of weakness chart created")
    return dest

def charsetCompare(field, chartpath, transparency, max_charset):
    # cracked passwords by charset
    name = field['field']
    fig, ax = plt.subplots()
    values = [int(i) for i in [ field['passwords with 1 charset'], field['passwords with 2 charsets'], field['passwords with 3 charsets'], field['passwords with all charsets']] ]
    if max_charset == 0:
        max_charset = max(values)
    ax.barh('1 charset', int(field['passwords with 1 charset']), color='#ff0000')
    ax.barh('2 charsets', int(field['passwords with 2 charsets']), color='#ff6400')
    ax.barh('3 charsets', int(field['passwords with 3 charsets']), color='#ffc800')
    ax.barh('all charsets', int(field['passwords with all charsets']), color='#00c800')
    ax.set_title(f"Cracked passwords by charset ({name})")
    plt.xlim(0, max_charset +10)
    for ind, val in enumerate(values):
        plt.text(val, ind, str(val), ha="left", va="center")
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    dest = f"{chartpath}/pass_by_charset_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches="tight", transparent=transparency)
    #print("[+] Cracked passwords by charset chart created")
    return dest, max_charset

def lengthCompare(field, chartpath, transparency, max_length):
    # cracked passwords by length
    name = field['field']
    fig, ax = plt.subplots()
    values = []
    labels = []
    for i in range(15):
        values.append( int(field[f"password length {i}"]) )
        labels.append( str(i) )
    values.append( int(field['password length 15 or more']) )
    if max_length == 0:
        max_length = max(values)
    labels.append('15+')
    ax.bar(labels[0], values[0], color='#bb0000')
    ax.bar(labels[1:5], values[1:5], color='#ff0000')
    ax.bar(labels[5:8], values[5:8], color='#ff6400')
    ax.bar(labels[8:13], values[8:13], color='#ffc800')
    ax.bar(labels[13:], values[13:], color='#00c800')
    ax.set_title(f"Cracked passwords per length ({name})")
    plt.ylim(0, max_length +10)
    for ind, val in enumerate(values):
        plt.text(ind, val, str(val), ha="center", va="bottom")
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    dest = f"{chartpath}/pass_by_length_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches="tight", transparent=transparency)
    #print("[+] Cracked passwords per length chart created")
    return dest, max_length

def robustnessBar(field, chartpath, transparency):
    name = field['field']
    fig, ax = plt.subplots()
    resist = [ 'password resists some seconds',
                'password resists some minutes',
                'password resists some hours',
                'password resists some days',
                'password resists some years' ]
    f0, f1, f2, f3, f4 = int(field[resist[0]]), int(field[resist[1]]), int(field[resist[2]]), int(field[resist[3]]), int(field[resist[4]])
    start = [ 0, f0 ]
    ax.barh( [""], [ f0 ], height=0.1, color='#bb0000', label='seconds' )
    ax.text( f0//2, 0, f0, ha='center', va='center', color='black')
    ax.barh( [""], [ f1 ], height=0.1, color='#ff0000', label='minutes', left=start[-1] )
    ax.text( f0+f1//2, 0, f1, ha='center', va='center', color='black')
    start.append( start[-1] + f1 )
    ax.barh( [""], [ f2 ], height=0.1, color='#ff6400', label='hours', left=start[-1] )
    ax.text( start[-1]+f2//2, 0, f2, ha='center', va='center', color='black')
    start.append( start[-1] + f2 )
    ax.barh( [""], [ f3 ], height=0.1, color='#ffc800', label='days', left=start[-1] )
    ax.text( start[-1]+f3//2, 0, f3, ha='center', va='center', color='black')
    start.append( start[-1] + f3 )
    ax.barh( [""], [ f4 ], height=0.1, color='#00c800', label='years', left=start[-1] )
    ax.text( start[-1]+f4//2, 0, f4, ha='center', va='center', color='black')
    # the following line is juste here because this is the only way I found to not have
    # a very thick horizontal bar : if every bar is 0.1 height, they take all the place
    # shame on me
    ax.barh( [""], [0], height=0.5)
    ax.set_title(f"Password resistance against hacker ({name})")
    ax.legend(bbox_to_anchor=(0.5, -0.2), loc="lower center", ncol=5)
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    dest = f"{chartpath}/pass_resistance_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches="tight", transparent=transparency)
    #print("[+] Password resistance chart created")
    return dest

def frequentPasswords(field, chartpath, transparency, max_top):
    # most frequent passwords
    name = field['field']
    fig, ax = plt.subplots()
    values = []
    labels = []
    i = 1
    while f"{i}th frequent password" in field and field[f"{i}th frequent password"] != ':':
        values.append(int(field[f"{i}th frequent password"].split(':',1)[0]))
        labels.append(field[f"{i}th frequent password"].split(':',1)[1])
        i += 1
    if max_top == 0:
        max_top = max(values)
    values.reverse()
    labels.reverse()
    ax.barh(labels, values)
    ax.set_title(f"Top cracked passwords for {name}")
    plt.xlim(0, max_top +5)
    for ind, val in enumerate(values):
        plt.text(val, ind, str(val), ha="left", va="center")
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    dest = f"{chartpath}/top_passwords_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches="tight", transparent=transparency)
    #print("[+] Top cracked passwords chart created")
    return dest, max_top

def frequentPatterns(field, chartpath, transparency, max_top_p):
    # most frequent patterns
    name = field['field']
    fig, ax = plt.subplots()
    values = []
    labels = []
    i = 1
    while f"{i}th frequent pattern" in field and field[f"{i}th frequent pattern"] != ':':
        values.append(int(field[f"{i}th frequent pattern"].split(':',1)[0]))
        labels.append(field[f"{i}th frequent pattern"].split(':',1)[1])
        i += 1
    if max_top_p == 0:
        max_top_p = max(values)
    values.reverse()
    labels.reverse()
    ax.barh(labels, values, color = "cyan")
    ax.set_title(f"Top patterns in cracked passwords for {name}")
    plt.xlim(0, max_top_p +5)
    for ind, val in enumerate(values):
        plt.text(val, ind, str(val), ha="left", va="center")
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
    dest = f"{chartpath}/top_patterns_{name}.png"
    if chartpath == "Fileless":
        dest = io.BytesIO()
    plt.savefig(dest, bbox_inches="tight", transparent=transparency)
    #print("[+] Top patterns in cracked passwords chart created")
    return dest, max_top_p

def main():
    parser = argparse.ArgumentParser(description='Produce charts from passwords stats', add_help=True)
    parser.add_argument('STATS_FILE', action="store",
            help="The CSV stats file produced by LesterTheLooter")
    parser.add_argument('-w', action="store", dest="wpath", default="./",
            help='Specify a path to write the charts')
    parser.add_argument('--transparent', action="store_true", default=False,
            help='Produce charts with transparent background')

    args = parser.parse_args()

    fields = CSV2Stats(args.STATS_FILE)
    exportCharts(fields, args.wpath, args.transparent)
    print("[*] Finished")

if __name__ == '__main__':
    main()
