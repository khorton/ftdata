#!/sw/bin/python

import sys
import os.path
import std_atm as SA
import numpy

num_header_lines = 4
alt_index = 14

temp_file = '/Users/kwh/temp/alt_fix_temp.txt'
TEMP = open(temp_file, 'w')

def fix_alts(path, alt_setting):
    if os.path.exists(path):
        IN_FILE = open(path)
    else:
        print usage
        print "Error!:", path, "does not exist"
        sys.exit()
    
    try:
        alt_setting = float(alt_setting)
    except ValueError:
        print usage
        print "Error!: altimeter_setting must be numeric!"
        sys.exit()
        
    alt_corr = SA.pressure_alt(0, alt_setting)
    if alt_corr > 0:
        corr_sign = 1
    else:
        corr_sign = -1
    # print "corr sign is:", corr_sign
    # sys.exit()
    # print alt_corr
    
    alts = []
    
    lines = IN_FILE.readlines()
    
    # write header lines
    for line in lines[:num_header_lines]:
        TEMP.write(line)
    
    # skip header lines
    lines = lines[num_header_lines:]
    for line in lines:
        items = line.split('\t')
        try:
            alts.append(float(items[alt_index]))
        except IndexError:
            print items
            sys.exit()
        except ValueError:
            # print "ValueError:", items[alt_index]
            alts.append("")
    print len(lines), len(alts)
    
    for n, line in enumerate(lines):
        try:
            alt = float(alts[n])
            ave_error = alt - numpy.average(alts[n-5:n+5])
            if corr_sign * ave_error > 1:
                # print "No correction for", alt
                pass
            else:
                alt_new = alt + alt_corr
                print alt, "to be corrected to", alt_new
        except ValueError:
            try:
                alt_new = alt
            # print "Blank alt"
            except UnboundLocalError:
                alt_new = 0
        except TypeError:
            for item in alts[n-5:n+5]:
                print item, type(item)
        items = line.split('\t')
        new_line = '\t'.join(items[:alt_index]) + '\t' + str(alt_new) + '\t' + '\t'.join(items[alt_index+1:])
        TEMP.write(new_line)

if __name__ == '__main__':
    usage = """
Usage: alt_fix.py path_to_data_file altimeter_setting

Adjusts data files with Dynon D-10A data to correct barometric altitudes to pressure altitudes
    """
    if len(sys.argv) == 3:
        fix_alts(sys.argv[1], sys.argv[2])
    else:
        print usage
