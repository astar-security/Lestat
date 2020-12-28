#!/usr/bin/python3

import argparse
import csv
import matplotlib.pyplot as plt
import os


def exportCharts(csvfilename, chartpath, transparency):
    """produce charts in PNG format"""
    
    # creating path to write charts if it does not exist
    if not os.path.exists(chartpath):
        os.makedirs(chartpath)

    # used to maintain the same scale between 'all accounts' and 'active accounts' cases
    max_length = 0
    max_top = 0
    max_top_p = 0
    max_charset = 0

    with open(csvfilename, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for field in reader:
        
            name = field['field']
            
            # main chart
            fig, ax = plt.subplots()
            values = [ int(field['compromised accounts']), int(field['safe accounts']) ]
            labels = [ 'compromised accounts', 'safe accounts' ]
            colors = [ '#dd0000', '#00c800' ]
            if field['unsafe accounts'] != '0' :
                values.append( int(field['unsafe accounts']) )
                labels.append( 'unsafe accounts' )
                colors.append( '#ff0000' )
            ax.pie(values, labels=labels, colors=colors, autopct=lambda p : '{:,.0f}% ({:,.0f})'.format(p,p * sum(values)/100), wedgeprops={"edgecolor":"white",'linewidth': 1, 'linestyle': 'solid', 'antialiased': True} )
            ax.set_title(f"Overall results for {name}")
            plt.tight_layout()
            plt.savefig(f"{chartpath}/main_{name}.png", bbox_inches="tight", transparent=transparency)
            
            # reason of compromise
            if 'passwords in top 10 most common' in field:
                fig, ax = plt.subplots()
                reasons = [('passwords empty', '#bb0000'), 
                    ('passwords based on username', '#bb0000'),
                    ('passwords in top 10 most common', '#bb0000'),
                    ('passwords based on company name', '#bb0000'),
                    ('passwords in top 1000 most common', '#ff0000'),
                    ('passwords as username extrapolation', '#ff0000'),
                    ('passwords related to company context', '#ff0000'),
                    ('passwords with 4 characters or less', '#ff0000'),
                    ('passwords in top 1M most common', '#ff6400'),
                    ('passwords with 6 characters or less', '#ff6400'),
                    ('passwords with 2 charsets or less', '#ff6400'),
                    ('passwords present in global wordlists', '#ffc800'),
                    ('passwords present in locale wordlists', '#ffc800'),
                    ('passwords leaked', '#ffc800'),
                    ('passwords weakness undetermined', '#ffc800')]
                values = []
                labels = []
                colors = []
                for r in reasons:
                    num = int( field[ r[0] ]) 
                    if num / (int(field['compromised accounts'])+int(field['unsafe accounts']))*100 >=1:
                        values.append( num )
                        labels.append( r[0][9:] )
                        colors.append( r[1] )
                ax.pie(values, labels=labels, colors=colors, autopct='%1i%%', wedgeprops={"edgecolor":"white",'linewidth': 1, 'linestyle': 'solid', 'antialiased': True} )
                ax.set_title(f"Reasons of weakness for {name}")
                plt.tight_layout()
                plt.savefig(f"{chartpath}/weaknesses_{name}.png", bbox_inches='tight', transparent=transparency)

            # cracked passwords by charset
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
            plt.savefig(f"{chartpath}/pass_by_charset_{name}.png", bbox_inches="tight", transparent=transparency) 

            # cracked passwords by length
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
            plt.savefig(f"{chartpath}/pass_by_length_{name}.png", bbox_inches="tight", transparent=transparency)
            
            # robustness
            if 'passwords in top 10 most common' in field:
                fig, ax = plt.subplots()
                resist = [ 'passwords resist some seconds', 
                            'passwords resist some minutes', 
                            'passwords resist some hours',
                            'passwords resist some days',
                            'passwords resist some years' ]
                f0, f1, f2, f3, f4 = int(field[resist[0]]), int(field[resist[1]]), int(field[resist[2]]), int(field[resist[3]]), int(field[resist[4]])
                start = [ 0, f0 ]
                ax.barh( [""], [ f0 ], height=0.1, color='#bb0000', label='seconds' )
                ax.barh( [""], [ f1 ], height=0.1, color='#ff0000', label='minutes', left=start[-1] )
                start.append( start[-1] + f1 )
                ax.barh( [""], [ f2 ], height=0.1, color='#ff6400', label='hours', left=start[-1] )
                start.append( start[-1] + f2 )
                ax.barh( [""], [ f3 ], height=0.1, color='#ffc800', label='days', left=start[-1] )
                start.append( start[-1] + f3 )
                ax.barh( [""], [ f4 ], height=0.1, color='#00c800', label='years', left=start[-1] )
                # the following line is juste here because this is the only way I found to not have
                # a very thick horizontal bar : if every bar is 0.1 height, they take all the place
                # shame on me
                ax.barh( [""], [0], height=0.5)
                ax.set_title(f"Password resistance against hacker ({name})")
                ax.legend(bbox_to_anchor=(0.5, -0.2), loc="lower center", ncol=5)
                for spine in plt.gca().spines.values():
                    spine.set_visible(False)
                plt.savefig(f"{chartpath}/pass_resistance_{name}.png", bbox_inches="tight", transparent=transparency)

            # most frequent passwords
            fig, ax = plt.subplots()
            values = []
            labels = []
            for i in range(10):
                values.append(int(field[f"{i+1}th frequent password"].split(':',1)[0]))
                labels.append(field[f"{i+1}th frequent password"].split(':',1)[1])
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
            plt.savefig(f"{chartpath}/top_passwords_{name}.png", bbox_inches="tight", transparent=transparency)
            
            # most frequent patterns
            fig, ax = plt.subplots()
            values = []
            labels = []
            for i in range(10):
                values.append(int(field[f"{i+1}th frequent pattern"].split(':',1)[0]))
                labels.append(field[f"{i+1}th frequent pattern"].split(':',1)[1])
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
            plt.savefig(f"{chartpath}/top_patterns_{name}.png", bbox_inches="tight", transparent=transparency)

def main():
    parser = argparse.ArgumentParser(description='Produce charts from passwords stats', add_help=True)
    parser.add_argument('STATS_FILE', action="store",
            help="The CSV stats file produced by LesterTheLooter")
    parser.add_argument('-w', action="store", dest="wpath", default="./",
            help='Specify a path to write the charts')
    parser.add_argument('--transparent', action="store_true", default=False,
            help='Produce charts with transparent background')

    args = parser.parse_args()

    exportCharts(args.STATS_FILE, args.wpath, args.transparent)

if __name__ == '__main__':
    main()
