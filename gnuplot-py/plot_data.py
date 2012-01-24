#! /sw/bin/python

# test script to plot flight test data using gnuplot, controlled via python

import Gnuplot, Gnuplot.funcutils

data_file = '/Users/kwh/ftdata/Tk/0510251651.csv'

g = Gnuplot.Gnuplot(debug=1)
g('set terminal x11 title "RV-8 Flight Test Data" persist')
g.title('RV-8 Flight Test Data') # (optional)
# g('set data style linespoints') # give gnuplot an arbitrary command
g('set size 1,15')

g('set nokey')


g('set xdata time')
g('set timefmt "%d/%m/%Y %H:%M:%S"')

g('set format x "%H:%M"')
g('set xrange ["09/26/2005 16:51:12.233":"09/26/2005 16:55:27.072"]')
g('set xlabel "time (H:M)"')


# g('set multiplot; set size 1.05,0.2;set origin 0.0,0.8')


g('set ylabel "Baro Altitude (ft)"')
f = Gnuplot.File(data_file, using='1:8', with='lines lt -1')
g.plot(f)

