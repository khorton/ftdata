#! /sw/bin/python2.6
##!/usr/bin/env python
"""
Working on - how to make edit plot list window stay on top?


Flight test data review application

usage - Flt_Test_Data_Review.py [datafile] [plotlist]

Bugs:   1 - 4. Fixed.
           
        5. Y axis limits to not change if the time slice changes.
        
        6 - 14. Fixed
        

Fixed
Bugs

        1. Save function does not remember the file name.
        
        2. Check event marker move code for whole slice.  At first glance, 
           with 2 hr data block, it does not seem to be moving as expected.
           
        3. For times in start and end displays, add leading zero for single 
           digit minutes and seconds.

        4. Edit plot list - add code to ask if user wants to save edited 
           list if he tries to close the window.
           
        6. Time slice times are not shown when the app is started.  Only
           after the time slice is moved.
           
        7. If the flight number is not entered, the cursor should go to that
           field after the error is flagged via the missing flight number
           dialog.
           
        8. If Plot button is clicked without previously saving the plot 
           file, program fails.  Need to check for valid savefile before 
           trying to assemble the command for print_data.pl.
           
        9. If Save button is clicked before entering the flight number,
           program fails.
           
       10. If editting plot list, and try to close window, the edit plot 
           list window is pushed behind the main window, which makes it 
           invisible.  Need to pull it back to the front.
       
       11. Dialog box for trying to close an editted plot list needs to
           be fleshed out.
           
       12. If Edit plots is selected with no flight number, get an error.

       13. If editting a plot list, clicking Cancel closes the window
           without asking the user if he wants to save the edit or not.

       14. If program is started without specifying a data file on the
           command line, it fails with an error.
                   
           

###############################################################################
To Do:  1 - 4. Done
        
        5. Add data file date and time in window title.
        
        6. Add code to pull test type names from template files and insert 
           them in combobox_test_type.
           
        7 - 10. Done
           
       11. Rework new data file function to allow changing data files 
           without quiting the program.
       
       12 - 13. Done
       
       14. Add help file.

       15 - 17. Done
              
       18. Add code for custom plot sets.
       
       19. Someday - look at plotting in a separate window, using pygist.  
           Reportedly much faster than matplotlib, but can't plot in GTK 
           window.

       20. Done
       
       21. Add code to review the list of plots.  Left and right arrow to 
           cycle through the list, with the graphs moving to show each item.

       22. Done
       
       23. Should by default make a new directory for each flight, to avoid
           graph files overwriting each other.
           
Done:   1. rework data_load function to be tolerant of data lines with 
           missing items.
           
        2. Add code to extract the time from column 1 of data and display it
           for start and end.
           
        3. Add code to snap to event markers.
           
        4. Add code to change y-axis limits, automatically, or manually.  
           Moved to bugs list.
        
        7. Add dialog for flt number not input.

        8. Add code to automatically put flt date in box.

        9. Add code to allow manual entry of time slice times.

       10. Add selectable list of plots to show in matplotlib subplots.  
           The idea is to not have to show all plots, to improve speed.

       12. Rework save function to remember the file name - moved to bugs 
           list.
       
       13. Add edit plot list file function.
       
       15. Check event marker move code for whole slice.  At first glance, 
           with 2 hr data block, it does not seem to be moving as expected.  
           Moved to bugs list.
           
       16. Add command line switch for GTK backend, to be used for remote 
           access.

       17. Rework format for GPS data plot labels - center multiline labels.
           Gave up.  Shortened labels instead.

       20. Parse filenames on the command line, converting ones like 
           '../../file' to the full path.  Relative paths choke gnuplot.
       
       22. For times in start and end displays, add leading zero for single 
           digit minutes and seconds.  Moved to bugs list.
           
Notes:  1. Tried using a SpinButton to control axis values.  Way too slow, 
           using the changed signal.

        2. Resetting plots, with check boxes at left - how to clear old 
           plots?  Use cla(self)?  NO - clear().  Or delaxes?
"""

# import sys
from __future__ import division
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
import bisect
import gtk
import gtk.glade
from matplotlib.axes import Subplot
from matplotlib.figure import Figure
from matplotlib.numerix import arange, sin, pi, cos, tan
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg, FigureCanvasGTK
import pylab
from optparse import OptionParser
import os
from platform import node
# import re
import time as time_module

def process_data_file(datafile, skip_lines = 5):
    """
    Reads datafile, processes it to make it acceptable to pylab, saves it
    to a temp file, and passes the temp file name back.
    """
    RAW_DATA = open(datafile)
    TEMP_DATA = open('/Users/kwh/temp/tempdata.txt', 'w+')
    
    columns = 58 # number of desired columns

    # pass header rows through without any processing
    for n in range(skip_lines):
        line = RAW_DATA.readline()
        TEMP_DATA.write(line)
    
    GPS_data_cache = []
    raw_data = RAW_DATA.readlines()
    for line in raw_data:
        # make all lines the correct length
        items = line.split('\t')
        if items[-1] == '\n':
            items[-1] = ''
        if items[-1][-1:] == '\n':
            items[-1] = items[-1][:-1]
        while len(items) > columns:
            items.pop()
        while len(items) < columns:
            items.append('0')
        for n,item in enumerate(items):
            if item == '':
                items[n] = '0'
        
        # process GPS data
        for n in range(15):
            GPS_data_cache.append('0')
        
        if items[43] == '0':
            # no GPS time, so this is blank record.  Use the last good data
            for n, item in enumerate(items[43:]):
                items[n + 43] = GPS_data_cache[n]
        else:
            for n, item in enumerate(items[43:]):
                # this is a good record, so load it into the cache
                GPS_data_cache[n] = item    
        
        TEMP_DATA.write('\t'.join(items) + '\n')
    
    return TEMP_DATA


def load_data(data_file = ''):
    """
    Loads flight test data from data file into array, and prepares to draw plots.
    """
    global DATA, start_time, time, pitch, bank, hdg, ias, alt, rpm, mp,\
    oil_temp, oil_press, cht1, cht2, cht3, cht4, egt1, egt2, egt3, egt4,\
    oat, fuel_flow, fuel_qty, volt, alternator_load, gps_gs, gps_tk, \
    gps_alt, gps_lat, gps_long, gps_dtk, gps_xtk, gps_wpt_dist, \
    gps_wpt_brg, gps_mag_var, gps_dest_dist, gps_nav_status, nz, ny,\
    yaw_rate

    if data_file == '': 
        app.data_file_name = app.get_data_file_name(app)
    else:
        app.data_file_name = data_file

    try: 
        DATA.close()
        print 'Closing old data file'
    except:
        ValueError
    
    skip_lines = 5
    DATA = process_data_file(app.data_file_name, skip_lines)
    DATA.seek(0)
    line = DATA.readline()
    items = line.split()
    date = ' '.join((items[-3], items[-2], items[-1]))
    app.entry_flt_date.set_text(date)
    title = 'Flight Test Data Review - ' + date
    app.MainWindow.set_title(title)

    # get start time from first full record
    for i in range(skip_lines):
        # skip first lines
        DATA.readline()

    line = DATA.readline()
    items = line.split('\t')
    hour, min, sec = items[0].split(':')
    start_time = ((( float(hour) * 60. ) + float(min) ) * 60. + float(sec))

    def col1(item):
        """
        Returns seconds since midnight, given in input of:
        'hour:miin:sec'
        """
        secs = txt_string2sec(item) - start_time
        return secs

    def gps_alt(item):
        """
        Returns -10000 if the GPS altitude is '-----', which is how invalid
        altitudes are sent by the GNS430.
        """
        if item == '-----':
            return 0.
        else:
            return float(item)

    converter_funcs = {0:col1, 46:gps_alt}
                       
    # skip GPS Wpt. column
    columns = range(51)
    columns.extend([52,53,54,55,56])

    data = pylab.load(DATA, converters = converter_funcs, skiprows = skip_lines, usecols=columns)

    time = data[:, 0]
    pitch = data[:, 10]
    bank = data[:, 11]
    hdg = data[:, 12]
    ias = data[:, 13]
    alt = data[:, 14]
    yaw_rate = data[:, 15]
    ny = data[:, 16]
    nz = data[:, 17]
    eis_time = data[:, 18]
    rpm = data[:, 19]
    mp = data[:, 20]
    oat = data[:, 21]
    fuel_flow = data[:, 22]
    fuel_qty = data[:, 23]
    cht1 = data[:, 24]
    cht2 = data[:, 25]
    cht3 = data[:, 26]
    cht4 = data[:, 27]
    egt1 = data[:, 28]
    egt2 = data[:, 29]
    egt3 = data[:, 30]
    egt4 = data[:, 31]
    oil_temp = data[:, 32]
    oil_press = data[:, 33]
    volt = data[:, 34]
    alternator_load = data[:, 35]
    unit_temp = data[:, 42]
    gps_gs = data[:, 44]
    gps_tk = data[:, 45]
    gps_alt = data[:, 46]
    gps_lat = data[:, 47]
    gps_long = data[:, 48]
    gps_dtk = data[:, 49]
    gps_xtk = data[:, 50]
    gps_wpt_dist = data[:, 51]
    gps_wpt_brg = data[:, 52]
    gps_mag_var = data[:, 53]
    gps_dest_dist = data[:, 54]
    gps_nav_status = data[:, 55]

def find_event_markers():
    """
    Builds a list of event markers and times.
    """
    global em_list
    # find EM column
    DATA.seek(0)
    while 1:
        line = DATA.readline()
        items = line.split('\t')
        if items[0] == 'Time':
            break
        
    for em_col, item in enumerate(items):
        if item == 'Event Marker':
            # read unit row to get it out of the way
            DATA.readline()
            break

    # Read data from EM column, and populate list of times.
    # If the event marker spans several consecutive data records, only the 
    # time of the first record is recorded.
    em_list = []
    while 1:
        line = DATA.readline()
        em = check_em(line)

        if em == 1:
            items = line.split('\t')
            em_secs = txt_string2sec(items[0]) - start_time
            em_list.append(em_secs)
            while 1:
                # ignore following lines with event marker set
                line = DATA.readline()
                em = check_em(line)
                if em == 0:
                    break
                elif em == -1:
                    break       
        elif em == -1:
            break
    
def check_em(line):
    """
    Parses a data line, and determines if the event marker is set.  Returns
    1 if event marker set, 0 if it is not set, and -1 if the line is blank or incomplete.
    """
    items = line.split('\t')
    try:
        em = items[4]
    except IndexError:
        return -1

    if em == '1':
        return 1
    else:
        return 0

def setup_canvas(remote):
    """
    Setup the canvas, for use by the other functions that popluate it with
    plots.
    """
    global f, canvas, degreeChar, num_plots
    degreeChar = u'\N{DEGREE SIGN}'
    num_plots = 38
    plot_height = 200
    
    f = Figure(dpi=100)
    f.hold(False)
    if remote == True:
        canvas = FigureCanvasGTK(f)  # a gtk.DrawingArea
    else:
        canvas = FigureCanvasGTKAgg(f)  # a gtk.DrawingArea
    
    # the size request sets the size of the area for the plots.  Second number is the height
    canvas.set_size_request(800, num_plots * plot_height)
    app.viewport_matplotlib.add(canvas)
    canvas.show()

def create_basic_plots(plots):
    """
    Create 7 basic plots using matplotlib.
    These are the default plots.
    """
    global plot1, plots_n
    
    plots_n = 1
    tup = (num_plots, 1, plots_n)
    plot1 = f.add_subplot(*tup)
    plot1.set_ylabel('Altitude (ft)')
    plot1.grid(True)
    plot1.plot(time, alt)
    axprops = {}
    axprops['sharex'] = plot1
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot2 = f.add_subplot(*tup, **axprops)
    plot2.set_ylabel('IAS (kt)')
    plot2.grid(True)
    plot2.plot(time, ias)
    plots_n += 1

    if (plots & 1 == 1) & (plots & 2 != 2) & (plots & 4 != 4):
        # basic plots ON and flt plots OFF and engine plots OFF
        tup = (num_plots, 1, plots_n)
        plot3 = f.add_subplot(*tup, **axprops)
        plot3.set_ylabel('Pitch (' + degreeChar + ')')
        plot3.grid(True)
        plot3.plot(time, pitch)
        plot3 = f.add_subplot(*tup, **axprops)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot4 = f.add_subplot(*tup, **axprops)
        plot4.set_ylabel('Bank (' + degreeChar + ')')
        plot4.grid(True)
        plot4.plot(time, bank)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot5 = f.add_subplot(*tup, **axprops)
        plot5.set_ylabel('Hdg (' + degreeChar + ')')
        plot5.grid(True)
        plot5.plot(time, hdg)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot6 = f.add_subplot(*tup, **axprops)
        plot6.set_ylabel('RPM')
        plot6.grid(True)
        plot6.plot(time, rpm)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot7 = f.add_subplot(*tup, **axprops)
        plot7.set_ylabel('MP (" HG)')
        plot7.grid(True)
        plot7.plot(time, mp)
        plots_n += 1
    elif (plots & 3 == 3) & (plots & 4 != 4):
        # basic plots ON and flt plots ON, engine plots OFF
        tup = (num_plots, 1, plots_n)
        plot6 = f.add_subplot(*tup, **axprops)
        plot6.set_ylabel('RPM')
        plot6.grid(True)
        plot6.plot(time, rpm)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot7 = f.add_subplot(*tup, **axprops)
        plot7.set_ylabel('MP (" HG)')
        plot7.grid(True)
        plot7.plot(time, mp)
        plots_n += 1
    elif (plots & 5 == 5) & (plots & 2 != 2):
        # basic plots ON and engine plots ON, flt plots OFF
        tup = (num_plots, 1, plots_n)
        plot3 = f.add_subplot(*tup, **axprops)
        plot3.set_ylabel('Pitch (' + degreeChar + ')')
        plot3.grid(True)
        plot3.plot(time, pitch)
        plot3 = f.add_subplot(*tup, **axprops)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot4 = f.add_subplot(*tup, **axprops)
        plot4.set_ylabel('Bank (' + degreeChar + ')')
        plot4.grid(True)
        plot4.plot(time, bank)
        plots_n += 1
    
        tup = (num_plots, 1, plots_n)
        plot5 = f.add_subplot(*tup, **axprops)
        plot5.set_ylabel('Hdg (' + degreeChar + ')')
        plot5.grid(True)
        plot5.plot(time, hdg)
        plots_n += 1

def create_flt_plots(plots):
    """
    Creates a set of 6 flight data plots.
    """
    global plots_n

    if plots & 2 != 2:
        # flt plots not selected
        return

    axprops = {}
    axprops['sharex'] = plot1

    tup = (num_plots, 1, plots_n)
    plot23 = f.add_subplot(*tup, **axprops)
    plot23.set_ylabel('Pitch (' + degreeChar + ')')
    plot23.grid(True)
    plot23.plot(time, pitch)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot24 = f.add_subplot(*tup, **axprops)
    plot24.set_ylabel('Bank (' + degreeChar + ')')
    plot24.grid(True)
    plot24.plot(time, bank)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot25 = f.add_subplot(*tup, **axprops)
    plot25.set_ylabel('Hdg (' + degreeChar + ')')
    plot25.grid(True)
    plot25.plot(time, hdg)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot26 = f.add_subplot(*tup, **axprops)
    plot26.clear()
    plot26.set_ylabel('Nz (g)')
    plot26.grid(True)
    plot26.plot(time, nz)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot27 = f.add_subplot(*tup, **axprops)
    plot27.set_ylabel('Ny (g)')
    plot27.grid(True)
    plot27.plot(time, ny)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot28 = f.add_subplot(*tup, **axprops)
    plot28.set_ylabel('Yaw Rate (' + degreeChar + '/s)')
    plot28.grid(True)
    plot28.plot(time, yaw_rate)
    plots_n += 1

def create_engine_plots(plots):
    """
    Creates a set of 11 engine data plots.
    """
    global plots_n

    if plots & 4 != 4:
        # engine plots not selected
        return

    axprops = {}
    axprops['sharex'] = plot1
    tup = (num_plots, 1, plots_n)
    plot41 = f.add_subplot(*tup, **axprops)
    plot41.set_ylabel('RPM')
    plot41.grid(True)
    plot41.plot(time, rpm)
    axprops = {}
    axprops['sharex'] = plot1
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot42 = f.add_subplot(*tup, **axprops)
    plot42.set_ylabel('MP (" HG)')
    plot42.grid(True)
    plot42.plot(time, mp)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot43 = f.add_subplot(*tup, **axprops)
    plot43.set_ylabel('CHT (' + degreeChar + 'C)')
    plot43.grid(True)
    plot43.plot(time, cht1, 'k', label = 'CHT 1')
    plot43.plot(time, cht2, 'b', label = 'CHT 2')
    plot43.plot(time, cht3, 'r', label = 'CHT 3')
    plot43.plot(time, cht4, 'g', label = 'CHT 4')
    plot43.legend()
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot44 = f.add_subplot(*tup, **axprops)
    plot44.set_ylabel('EGT (' + degreeChar + 'C)')
    plot44.grid(True)
    plot44.plot(time, egt1, time, egt2, time, egt3, time, egt4)
    plot44.legend(('EGT 1', 'EGT 2', 'EGT 3', 'EGT 4'))
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot45 = f.add_subplot(*tup, **axprops)
    plot45.set_ylabel('Oil Temp (' + degreeChar + 'C)')
    plot45.grid(True)
    plot45.plot(time, oil_temp)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot46 = f.add_subplot(*tup, **axprops)
    plot46.set_ylabel('Oil Press (psi)')
    plot46.grid(True)
    plot46.plot(time, oil_press)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot47 = f.add_subplot(*tup, **axprops)
    plot47.set_ylabel('Fuel Flow (USG/Hr)')
    plot47.grid(True)
    plot47.plot(time, fuel_flow)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot48 = f.add_subplot(*tup, **axprops)
    plot48.set_ylabel('Fuel Qty. (USG)')
    plot48.grid(True)
    plot48.plot(time, fuel_qty)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot49 = f.add_subplot(*tup, **axprops)
    plot49.set_ylabel('OAT (' + degreeChar + 'C)')
    plot49.grid(True)
    plot49.plot(time, oat)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot50 = f.add_subplot(*tup, **axprops)
    plot50.set_ylabel('Ess. Bus Voltage (V)')
    plot50.grid(True)
    plot50.plot(time, volt)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot51 = f.add_subplot(*tup, **axprops)
    plot51.set_ylabel('Alternator Load (A)')
    plot51.grid(True)
    plot51.plot(time, oat)
    plots_n += 1

def create_gps_plots(plots):
    """
    Creates a set of all GPS data plots.
    """
    global plots_n

    if plots & 8 != 8:
        # gps plots not selected
        return

    axprops = {}
    axprops['sharex'] = plot1
    tup = (num_plots, 1, plots_n)
    plot61 = f.add_subplot(*tup, **axprops)
    plot61.set_ylabel('Grd Speed (kt)')
    plot61.grid(True)
    plot61.plot(time, gps_gs)
    axprops = {}
    axprops['sharex'] = plot1
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot62 = f.add_subplot(*tup, **axprops)
    plot62.set_ylabel('Track (' + degreeChar + ' Mag)')
    plot62.grid(True)
    plot62.plot(time, gps_tk)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot63 = f.add_subplot(*tup, **axprops)
    plot63.set_ylabel('Desired Tk. (' + degreeChar + ' Mag)')
    plot63.grid(True)
    plot63.plot(time, gps_dtk)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot64 = f.add_subplot(*tup, **axprops)
    plot64.set_ylabel('Cross Tk. Error (nm)')
    plot64.grid(True)
    plot64.plot(time, gps_xtk)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot65 = f.add_subplot(*tup, **axprops)
    plot65.set_ylabel('Wpt. Dist. (nm)')
    plot65.grid(True)
    plot65.plot(time, gps_wpt_dist)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot66 = f.add_subplot(*tup, **axprops)
    plot66.set_ylabel('Wpt. Brg (' + degreeChar + ' Mag)')
    plot66.grid(True)
    plot66.plot(time, gps_wpt_brg)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot67 = f.add_subplot(*tup, **axprops)
    plot67.set_ylabel('Mag. Var (' + degreeChar + ' E)')
    plot67.grid(True)
    plot67.plot(time, gps_mag_var)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot68 = f.add_subplot(*tup, **axprops)
    plot68.set_ylabel('Latitude (' + degreeChar + ' N)')
    plot68.grid(True)
    plot68.plot(time, gps_lat)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot69 = f.add_subplot(*tup, **axprops)
    plot69.set_ylabel('Longitude (' + degreeChar + ' W)')
    plot69.grid(True)
    plot69.plot(time, gps_long)
    plots_n += 1

    tup = (num_plots, 1, plots_n)
    plot70 = f.add_subplot(*tup, **axprops)
    plot70.set_ylabel('GPS Alt. (ft)')
    plot70.grid(True)
    plot70.plot(time, gps_alt)
    plots_n += 1

def txt_string2sec(time_string):
    """
    Returns the number of seconds since the epoch for the given time in text format.
    """
    
    time_bits = time_string.split(':')
    if len(time_bits) < 3:
        time_bits.append(0)
    hr, mn, s = time_bits[0], time_bits[1], time_bits[2]
    seconds = float(hr) * 3600 + float(mn) * 60 + float(s)

    return seconds


class Flt_Test_Data_Review_App_GTK:
    """
    Main class for flt test data review application
    """
    def __init__(self):
        #Set the Glade file
        self.gladefile = "Flt_Test_Data_Review.glade"  
        self.wTree = gtk.glade.XML(self.gladefile, "MainWindow") 

        self.inc_minor= .1
        self.inc_major = .5
        #Signals, and the handlers that are called
        dic = { "on_menu_new_data_activate" : self.get_data_file_name,
            "on_help_activate" : self.help_file,
            "on_cb_plots_basic_toggled" : self.plots_toggled,
            "on_cb_plots_engine_toggled" : self.plots_toggled,
            "on_cb_plots_flt_toggled" : self.plots_toggled,
            "on_cb_plots_gps_toggled" : self.plots_toggled,
            "on_button_dec_start_clicked" : (self.move_slice, 1, self.inc_minor, -1),
            "on_button_inc_start_clicked" : (self.move_slice, 1, self.inc_minor, 1),
            "on_button_dec2_start_clicked" : (self.move_slice, 1, self.inc_major, -1),
            "on_button_inc2_start_clicked" : (self.move_slice, 1, self.inc_major, 1),
            "on_button_minus_one_start_clicked" : (self.move_slice, 1, 1, -1),
            "on_button_minus_ten_start_clicked" : (self.move_slice, 1, 10, -1),
            "on_button_plus_ten_start_clicked" : (self.move_slice, 1, 10, 1),
            "on_button_plus_one_start_clicked" : (self.move_slice, 1, 1, 1),
            "on_button_dec_mid_clicked" : (self.move_slice, 2, self.inc_major, -1),
            "on_button_inc_mid_clicked" : (self.move_slice, 2, self.inc_major, 1),
            "on_button_dec_end_clicked" : (self.move_slice, 3, self.inc_minor, -1),
            "on_button_inc_end_clicked" : (self.move_slice, 3, self.inc_minor, 1),
            "on_button_dec2_end_clicked" : (self.move_slice, 3, self.inc_major, -1),
            "on_button_inc2_end_clicked" : (self.move_slice, 3, self.inc_major, 1),
            "on_button_minus_one_end_clicked" : (self.move_slice, 3, 1, -1),
            "on_button_minus_ten_end_clicked" : (self.move_slice, 3, 10, -1),
            "on_button_plus_ten_end_clicked" : (self.move_slice, 3, 10, 1),
            "on_button_plus_one_end_clicked" : (self.move_slice, 3, 1, 1),
            "on_button_prev_EM_start_clicked" : (self.event_marker_clicked, 1, -1),
            "on_button_next_EM_start_clicked" : (self.event_marker_clicked, 1, 1),
            "on_button_prev_EM_whole_clicked" : (self.event_marker_clicked, 2, -1),
            "on_button_next_EM_whole_clicked" : (self.event_marker_clicked, 2, 1),
            "on_button_prev_EM_end_clicked" : (self.event_marker_clicked, 3, -1),
            "on_button_next_EM_end_clicked" : (self.event_marker_clicked, 3, 1),
            "on_button_save_tp_clicked" : self.save_test_point,
            "on_button_save_plot_list_clicked" : self.save_plot_list,
            "on_update_time_slices_activate" : self.update_plot_times,
            "on_button_plot_clicked" : self.make_plots,
            "on_button_edit_clicked" : self.make_edit_plot_view,
            "on_button_cancel_edit_clicked" : self.cancel_edit,
            "on_MainWindow_destroy" : gtk.main_quit,
            "on_quit1_activate" : gtk.main_quit }
        self.wTree.signal_autoconnect(dic)

        # from http://www.async.com.br/faq/pygtk/index.py?req=edit&file=faq22.004.htp
        for w in self.wTree.get_widget_prefix(''):
            name = w.get_name()
            # make sure we don't clobber existing attributes
            assert not hasattr(self, name)
            setattr(self, name, w)
        
        self.plot_list_lines = []

    def help_file(self, widget):
        """
        Opens the help file.
        """
        help_path = os.path.abspath('help/help.xml')
        cmd = 'yelp ' + help_path + ' &'
#       os.system('yelp help/help.html')
        os.system(cmd)

    def plots_toggled(self, widget):
        """
        Called when the user toggles one of the plot selections.
        """
        # get current settings
        xlow, xhigh, ylow, yhigh = plot1.axis()

        # clear plots
        f.clf()
        plots = 0
        if app.cb_plots_basic.get_active():
            basic_plots = True
            plots = 1

        if app.cb_plots_flt.get_active():
            flt_plots = True
            plots += 2
        
        if app.cb_plots_engine.get_active():
            engine_plots = True
            plots += 4

        if app.cb_plots_gps.get_active():
            flt_plots = True
            plots += 8

        create_basic_plots(plots)
        create_flt_plots(plots)
        create_engine_plots(plots)      
        create_gps_plots(plots)

        self.redraw_plots(xlow, xhigh)
    
    def move_slice(self, widget, part_to_move, amount, dir):
        """
        Moves time slice and redraws it.
        
        part_to_move is 1, 2, or 3 to identify the start, mid or end 
        respectively.
        amount is 1 or 2 to identify minor or major movement.
        
        dir is 1 or -1 for increase or decrease.
        """
        # get current settings
        xlow, xhigh, ylow, yhigh = plot1.axis()
        
        if part_to_move == 1:
            if dir == 1:
                if abs(amount) < 1:
                    xlow = min(int(xhigh - (1 - amount) * (xhigh - xlow)), xhigh - 1)
                else:
                    xlow = min(int(xlow + amount), xhigh -1)
            elif dir == -1:
                if abs(amount) < 1:
                    xlow = int(xhigh - (xhigh - xlow) / (1 - amount))
                else:
                    xlow = int(xlow - amount)
            else:
                raise ValueError, 'Invalid value for direction'
        elif part_to_move == 2:
            inc = int(amount * (xhigh - xlow))
            xlow = xlow + inc * dir
            xhigh = xhigh + inc * dir
        elif part_to_move == 3:
            if dir == 1:
                if abs(amount) < 1:
                    xhigh = int(xlow + (xhigh - xlow) / (1 - amount))
                else:
                    xhigh = int(xhigh + amount)
            elif dir == -1:
                if abs(amount) < 1:
                    xhigh = max(int(xlow + (1 - amount) * (xhigh - xlow)), xlow + 1)
                else:
                    xhigh = max(int(xhigh - amount), xlow + 1)
            else:
                raise ValueError, 'Invalid value for direction'
        else:
            raise ValueError, 'Invalid value for part to move'
        plot1.axis(xmin = xlow, xmax = xhigh)

        self.redraw_plots(xlow, xhigh)
        
        return

    def redraw_plots(self, xlow, xhigh):
        """
        Redraws the plots, and updates the values in the time boxes.
        """
        plot1.axis(xmin = xlow, xmax = xhigh)
#       plot1.set_autoscale_on(False)
#       plot1.set_autoscale_on(True)
        f.canvas.draw()
        app.start_time.set_text(app.sec2txt(xlow, start_time))
        width = xhigh - xlow
        if width <= 60:
            text = str(int(width)) + ' s'
        elif width <= 3600:
            text = str(int(width / 60)) + ' mn ' + str(int(width % 60)) + ' s'
        else:
            text = str(int(width / 3600)) + ' hr ' + str(int((width % 3600) / 60)) + ' mn'
        app.mid_time.set_text(text)
        app.end_time.set_text(app.sec2txt(xhigh, start_time))
        return
        
    def get_event_marker(self, time, direction):
        """
        Returns the time of the next event marker, given the time to start
        the search, and the direction of the search (1 = search forward,
        -1 = search backwards).
        """
        # get where the current time fits in the event marker list
        em_slot = bisect.bisect(em_list, time)
    
        if direction == 1:
            return em_list[em_slot]
        elif direction == -1:
            new_time = em_list[em_slot - 1]
            if new_time == time:
                new_time = em_list[max(em_slot - 2, 0)]
            return new_time         
        else:
            raise ValueError, 'Invalid direction.'

    def event_marker_clicked(self, widget, slice, direction):
        """
        Called when the user clicks on a button to snap to the next event
        marker.
        
        slice = 1 - start time
                2 - scroll whole slice
                3 - end time
                 
        direction = 1 - search later
                   -1 - search earlier
        """
        # get current settings
        xlow, xhigh, ylow, yhigh = plot1.axis()
        
        if slice == 1:
            xlow = app.get_event_marker(xlow, direction)
        elif slice == 2:
            xlow = app.get_event_marker(xlow, direction)
            xhigh = app.get_event_marker(xhigh, direction)
        elif slice == 3:
            xhigh = app.get_event_marker(xhigh, direction)
        else:
            raise ValueError, 'Invalid slice'

        self.redraw_plots(xlow, max(xhigh, xlow + 1))
    
    def sec2txt(self, sec, start_time):
        """
        Returns the start time in data file format, given the number of
        seconds since the start, and the number of seconds for the first
        point in the data.
        """
        sec = sec + start_time

        time_str = time_module.strftime('%H:%M:%S', time_module.gmtime(sec))
        return time_str

    def get_data_file_name(self, widget):
        """
        Called when the user requests to select a new data file.
        """
        # Create the dialog, show it, and store the results
        self.gladefile = "Flt_Test_Data_Review.glade"
        self.wTree = gtk.glade.XML(self.gladefile, "filechooser_dialog_data") 
        self.dlg = self.wTree.get_widget("filechooser_dialog_data")
        response = self.dlg.run()
        if response == gtk.RESPONSE_OK:
            data_file = self.dlg.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            pass
        self.dlg.destroy()

        return data_file

    def get_plot_list_name(self, widget):
        """
        Calls the Save file dialog to get the desired plot list name.
        """
        # Create the dialog, show it, and store the results
        self.gladefile = "Flt_Test_Data_Review.glade"
        self.wTree = gtk.glade.XML(self.gladefile, "filechooser_dialog_save") 
        self.dlg = self.wTree.get_widget("filechooser_dialog_save")
        response = self.dlg.run()
        if response == gtk.RESPONSE_OK:
            save_file = self.dlg.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            pass
        self.dlg.destroy()

        try:
            return save_file
        except UnboundLocalError:
            return ''

    def make_dialog_no_test(self, widget):
        """
        Called when the user tries to save a data point without selecting
        the type of test.
        """
        # Create the dialog, show it, and store the results
        no_test_dlg = No_Test_Dialog();     
        result = no_test_dlg.run()

    def make_dialog_no_flt_num(self, widget):
        """
        Called when the user tries to save a data point without entering
        the flt number.
        """
        # Create the dialog, show it, and store the results
        no_flt_num_dlg = No_Flt_Num_Dialog();       
        result = no_flt_num_dlg.run()
        self.entry_flt_num.grab_focus()

    def save_test_point(self, widget):
        """
        Pulls the test point data and saves it to a list.
        """
        xlow, xhigh, ylow, yhigh = plot1.axis()
        start = app.sec2txt(xlow, start_time)
        end = app.sec2txt(xhigh, start_time)
        
        test_type = app.combobox_test_type.get_active_text()
        if test_type == None:
            self.make_dialog_no_test(widget)
            return

        tp_label = app.entry_tp_label.get_text()

        tp_line = 'plot ' + test_type + ' "' + start + '" "' + end + '"'
        if tp_label != '':
            tp_line += ' label="' + tp_label + '"'
        
        self.plot_list_lines.append(tp_line)
    
    def update_plot_times(self, widget):
        # get current settings
        xlow, xhigh, ylow, yhigh = plot1.axis()
        new_start_text = app.start_time.get_text()
        new_end_text = app.end_time.get_text()
        new_xlow = txt_string2sec(new_start_text) - start_time
        new_xhigh = txt_string2sec(new_end_text) - start_time
        if new_xhigh <= new_xlow + 1:
            new_xhigh = new_xlow + 1
        app.redraw_plots(new_xlow, new_xhigh)

    def make_plot_list(self, widget):
        """
        Saves the list of test points to a string.
        """
        # get flt date
        flt_date = app.entry_flt_date.get_text()
        
        # get flt number
        flt_num = self.entry_flt_num.get_text()
        if flt_num == "":
            self.make_dialog_no_flt_num(widget)
            return
        plot_list_string = ''

        # file header
        plot_list_string += '#' * 80
        plot_list_string += "\n# list of plots to create for Kevin Horton's RV-8\n"
        plot_list_string += '# required elements are date, flt, datafile, and a list of plots\n#\n'
        plot_list_string += 'date = ' + flt_date + '\n'
        plot_list_string += 'flt = ' + flt_num + '\n'
        plot_list_string += 'datafile = ' + app.data_file_name + '\n#\n'
        plot_list_string += '## start of plot list ##\n'
        # test points
        lines = '\n'.join(app.plot_list_lines)
        plot_list_string += lines
                
        return plot_list_string

    def make_edit_plot_view(self, widget):
        """
        Creates the window with a TextView widget to edit the plot list.
        """
        self.edit_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.edit_window.set_transient_for(self.MainWindow)
        self.edit_window.connect("delete_event", self.destroy_edit_win)
        self.edit_window.set_border_width(10)
        self.edit_window.set_default_size(400, 400)
        self.edit_window.set_title('Edit Plot List')

        # parametres are homogenous and spacing
        vbox101 = gtk.VBox(False, 0)
        self.edit_window.add(vbox101)
        vbox101.show()

        edit_scrolled_window = gtk.ScrolledWindow()
        edit_scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        edit_scrolled_window.show()
        vbox101.pack_start(edit_scrolled_window, True, True, 5)
        
        self.edit_textview = gtk.TextView()
        edit_scrolled_window.add(self.edit_textview)
        self.edit_buffer = self.edit_textview.get_buffer()
        try:
            self.edit_buffer.set_text(self.make_plot_list(self))
        except TypeError:
            print 'No plots yet created'
            self.edit_window.destroy()
            return
        self.edit_buffer.set_modified(False)
        self.edit_textview.show()
        
        hbox_pl_button = gtk.HBox(False, 0)
        hbox_pl_button.show()
        vbox101.pack_start(hbox_pl_button, False, False, 0)
        
        edit_plot_list_save_button = gtk.Button(stock = gtk.STOCK_SAVE)
        edit_plot_list_save_button.connect("clicked", self.save_edit)
        edit_plot_list_save_button.show()
        hbox_pl_button.pack_end(edit_plot_list_save_button, False, False, 5)
        
        edit_plot_list_cancel_button = gtk.Button(stock = gtk.STOCK_CANCEL)
        edit_plot_list_cancel_button.connect("clicked", self.cancel_edit)
        edit_plot_list_cancel_button.show()
        hbox_pl_button.pack_end(edit_plot_list_cancel_button, False, False, 5)
        
        # show the whole window, after it is completely built
        self.edit_window.show()

    def destroy_edit_win(self, widget, *args):
        """
        Called when the user tries to destroy the edit window.
        """
#\      print 'User wants to close the edit plot list window.'
        # check to see if the text has been editted
        mod_status = self.edit_buffer.get_modified()
        if mod_status == True:
#           print 'Trying to catch destroy_event'
            dialog = gtk.Dialog("Abandon Edit?",
                     self.edit_window,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_DELETE, gtk.RESPONSE_DELETE_EVENT,
                      gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
            label = gtk.Label()
            label.set_markup('<span size="x-large">\nSave changes to the plot list?\n</span>')
            dialog.vbox.pack_start(label, True, True, 0)
            label.show()
            dialog.show()
            # responses, Cancel = -2, Save = -3, Delete = -4
            response = dialog.run()

            if response == -2:
                # Do not close the edit window
#               print 'Plot list edited, but user cancelled the close.'
                dialog.destroy()
                return True
            
            elif response == -3:
                # Save the edit, then close the window
                dialog.destroy()
                self.save_edit(widget)
                return False
            elif response == -4:
                # Delete the edit window and do not save the edit
                dialog.destroy()
                return False
        else:
#           print 'No mods, closing edit window'
            return False

    def cancel_edit(self, widget):
        """
        Cancel editing the plot list.  Return the plot list to its previous state.
        """
        mod_status = self.edit_buffer.get_modified()
        if mod_status == True:
#           print 'Trying to cancel an edit'
            dialog = gtk.Dialog("Abandon Edit?",
                     self.edit_window,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_DELETE, gtk.RESPONSE_DELETE_EVENT,
                      gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
            label = gtk.Label()
            label.set_markup('<span size="x-large">\nSave changes to the plot list?\n</span>')
            dialog.vbox.pack_start(label, True, True, 0)
            label.show()
            dialog.show()
            # responses, Cancel = -2, Save = -3, Delete = -4
            response = dialog.run()

            if response == -2:
                # Do not close the edit window
#               print 'Plot list edited, but user cancelled the close.'
                dialog.destroy()
                return
            
            elif response == -3:
                # Save the edit, then close the window
                dialog.destroy()
                self.save_edit(widget)
                self.edit_window.destroy()
                return
            elif response == -4:
                # Delete the edit window and do not save the edit
                dialog.destroy()
                self.edit_window.destroy()
                return
        else:
#           print 'No mods, closing edit window'
            self.edit_window.destroy()
            return


    def save_edit(self, widget):
        """
        Save the editted plot list.
        """
        text_start, text_end = self.edit_buffer.get_bounds()
        new_plot_list = self.edit_buffer.get_text(text_start, text_end)
        
        # separate header from list of plots
        self.plot_list_lines = []
        lines = new_plot_list.split('\n')
        for line in lines:
            if line[0:5] == 'plot ':
                self.plot_list_lines.append(line)
        self.save_plot_list(widget)
                
        self.edit_window.destroy()

    def save_plot_list(self, widget):
        """
        Saves the list of test points to a file.
        """
        plot_list = app.make_plot_list(widget)
#       print 'Plot list is:', plot_list
        if plot_list == None:
            # blank plot list because the flight number needs to be entered
            return

        # save file not yet defined
        if self.savefile == '':
            self.savefile = app.get_plot_list_name(self)
            
        OUT = open(self.savefile, 'w')

        OUT.write(plot_list)

    def make_plots(self, widget):
        """
        Takes saved plot list, and feeds it to a set of scripts to create
        pdf files with data plots.
        """
        if self.savefile == '':
            self.savefile = app.get_plot_list_name(self)
        
        cmd = 'cd /Users/kwh/ftdata/gnuplot2; print_data.pl ' + self.savefile
#       print 'gnuplot command is:', cmd
        os.system(cmd)
        cmd = 'cd /Users/kwh/ftdata/gnuplot2; gp2pdf.pl *.gp'
        os.system(cmd)


class No_Test_Dialog:
    """
    This class is used to show dialog_no_test
    """
    
    def __init__(self):
        #setup the glade file
        self.gladefile = "Flt_Test_Data_Review.glade"
        
    def run(self):
        """
        This function will show dlg_no_test
        """ 
        
        #load the dialog from the glade file      
        self.wTree = gtk.glade.XML(self.gladefile, "dialog_no_test") 
        #Get the actual dialog widget
        self.dlg = self.wTree.get_widget("dialog_no_test")
    
        #run the dialog and store the response      
        self.result = self.dlg.run()
        
        #we are done with the dialog, destory it
        self.dlg.destroy()
        
        #return the result
        return self.result
        

class No_Flt_Num_Dialog:
    """
    This class is used to show dialog_no_flt_num
    """ 
    def __init__(self):
        #setup the glade file
        self.gladefile = "Flt_Test_Data_Review.glade"
        
    def run(self):
        """
        This function will show dlg_no_flt_num
        """ 
        #load the dialog from the glade file      
        self.wTree = gtk.glade.XML(self.gladefile, "dialog_no_flt_num") 
        #Get the actual dialog widget
        self.dlg = self.wTree.get_widget("dialog_no_flt_num")
    
        #run the dialog and store the response      
        self.result = self.dlg.run()
        
        #we are done with the dialog, destory it
        self.dlg.destroy()
        
        #return the result
        return self.result


def parse_options():
    """
    Parse the command line options
    """
    global datafile, remote
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage=usage)
    parser.set_defaults(remote=False, datafile='', savefile = '')
    parser.add_option("-r", "--remote",
                      action="store_true", dest="remote",
                      help="remote mode, using GTK backend for faster plotting")
    parser.add_option("-f", "--file", dest="datafile",
                      help="read data from DATAFILE")
    parser.add_option("-s", "--save", dest="savefile",
                      help="save plot list to SAVEFILE")
    (options, args) = parser.parse_args()

    datafile = os.path.abspath(options.datafile)

    if options.savefile == '':
        app.savefile = ''
    else:
        app.savefile = os.path.abspath(options.savefile)
    remote = options.remote


if __name__ == "__main__":
#   global plot_list_name, savefile
    global savefile
    app = Flt_Test_Data_Review_App_GTK()
    datafile = ''

    parse_options()
    try:
        load_data(datafile)
    except IOError:
        data_file = app.get_data_file_name(app)
        load_data(data_file)
    find_event_markers()
    setup_canvas(remote)
    create_basic_plots(1)

    # plots are redraw to force the time slice times to be input in the entry boxes.
    xlow, xhigh, ylow, yhigh = plot1.axis()
    app.redraw_plots(xlow, xhigh)

    gtk.main()

