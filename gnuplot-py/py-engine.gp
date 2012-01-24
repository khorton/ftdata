# template to plot climb data from sdl.pl in multiple plots per page

# Notes:  1. This file was manually tweaked to work with the data created by
#            merge_ftdata.py.  A new script must be created to create gunplot
#            files.  The items that needed to be adjusted were:
#              column numbers to plot (e.g. plot 'file' using 1:22)
#              yrange

reset


#####################################################################
# preamble of gnuplot file


set terminal postscript portrait 9 enhanced colour blacktext solid
set output '1-engine.ps'

set nokey; # turn off key in top right corner
set lmargin 10; # needed to force fixed margin between edge of plot surface and axis.  Otherwise the y axis won't line up
set rmargin 3

set xdata time
# set timefmt "%d/%m/%Y %H:%M:%S"
set timefmt "%H:%M:%S"
set format x "%H:%M:%S"
set xrange ["10:02:35":"10:03:15"]
set xtics 5
set mxtics 5
set xlabel "time (H:M:S)"
  
set label 1 "RV-8 C-GNHK Flight 10 31 Mar 2006" at screen .05,1 front
set label 2 "Engine Data" at screen 1,1 center front
set label 4 "One division = 1 second" at screen .05,-0.01 front

set grid xtics mxtics ytics mxtics lw 2, lw 1

# if dots are wanted, instead of lines, replace "with lines" with "with lines"
# set pointsize 0.2

#####################################################################
# page 1
set label 3 "Page 1 of 5" at screen 1,-.01 right front
set multiplot;
set size 1.05,0.2
# there is an offset of two in the columns between the data and how gnuplot parses them.

set origin 0.0,0.8;  set ylabel "Baro Altitude (ft)"
set yrange [-500:500]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:15 with lines lt -1

set origin 0.0,0.6;  set ylabel "IAS (kt)"
set yrange [-10:20]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:14 with lines lt -1

set origin 0.0,0.4;  set ylabel "OAT ({/Symbol °}C)"
set yrange [-30:-25]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:22 with lines lt -1

set origin 0.0,0.2;  set ylabel "RPM (n/mn)"
set yrange [-50:50]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:20 with lines lt -1

set origin 0.0,5.55111512312578e-17;  set ylabel "Manifold Pressure (in HG)"
set yrange [25:35]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:21 with lines lt -1

unset multiplot

#####################################################################
# page 2
set label 3 "Page 2 of 5" at screen 1,-.01 right front
set multiplot;
set size 1.05,0.2
# there is an offset of two in the columns between the data and how gnuplot parses them.

set origin 0.0,0.8;  set ylabel "CHT ({/Symbol °}C)"
set key bottom
set yrange [0:10]
plot '' using 1:25 with lines lt 7 title 'CHT 1',\
      '' using 1:26 with lines lt 1 title 'CHT 2',\
      '' using 1:27 with lines lt 2 title 'CHT 3',\
      '' using 1:28 with lines lt 3 title 'CHT 4';
unset key

set origin 0.0,0.6;  set ylabel "CHT 1 ({/Symbol °}C)"
set yrange [0:10]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:25 with lines lt -1

set origin 0.0,0.4;  set ylabel "CHT 2 ({/Symbol °}C)"
set yrange [0:10]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:26 with lines lt -1

set origin 0.0,0.2;  set ylabel "CHT 3 ({/Symbol °}C)"
set yrange [0:10]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:27 with lines lt -1

set origin 0.0,5.55111512312578e-17;  set ylabel "CHT 4 ({/Symbol °}C)"
set yrange [0:10]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:28 with lines lt -1

unset multiplot

#####################################################################
# page 3
set label 3 "Page 3 of 5" at screen 1,-.01 right front
set multiplot;
set size 1.05,0.2
# there is an offset of two in the columns between the data and how gnuplot parses them.

set origin 0.0,0.8;  set ylabel "EGT ({/Symbol °}C)"
set key bottom
set yrange [5:15]
plot '' using 1:29 with lines lt 7 title 'EGT 1',\
      '' using 1:30 with lines lt 1 title 'EGT 2',\
      '' using 1:31 with lines lt 2 title 'EGT 3',\
      '' using 1:32 with lines lt 3 title 'EGT 4';
unset key

set origin 0.0,0.6;  set ylabel "EGT 1 ({/Symbol °}C)"
set yrange [0:20]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:29 with lines lt -1

set origin 0.0,0.4;  set ylabel "EGT 2 ({/Symbol °}C)"
set yrange [0:20]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:30 with lines lt -1

set origin 0.0,0.2;  set ylabel "EGT 3 ({/Symbol °}C)"
set yrange [0:20]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:31 with lines lt -1

set origin 0.0,5.55111512312578e-17;  set ylabel "EGT 4 ({/Symbol °}C)"
set yrange [0:20]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:32 with lines lt -1

unset multiplot

#####################################################################
# page 4
set label 3 "Page 4 of 5" at screen 1,-.01 right front
set multiplot;
set size 1.05,0.2
# there is an offset of two in the columns between the data and how gnuplot parses them.

set origin 0.0,0.8;  set ylabel "Fuel Flow (USG/hr)"
set yrange [-2:3]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:29 with lines lt -1

set origin 0.0,0.6;  set ylabel "Fuel Remaining (USG)"
set yrange [-4:6]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:38 with lines lt -1

set origin 0.0,0.4;  set ylabel "Ess Bus Voltage (volt)"
set yrange [11:13]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:28 with lines lt -1

set origin 0.0,0.2;  set ylabel "Alternator Load (amp)"
set yrange [45:55]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:48 with lines lt -1

set origin 0.0,5.55111512312578e-17;  set ylabel "EIS Internal Temperature ({/Symbol °}C)"
set yrange [16:21]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:30 with lines lt -1

unset multiplot

#####################################################################
# page 5
set label 3 "Page 5 of 5" at screen 1,-.01 right front
set multiplot;
set size 1.05,0.2
# there is an offset of two in the columns between the data and how gnuplot parses them.

set origin 0.0,0.8;  set ylabel "Oil Temperature ({/Symbol °}C)"
set yrange [13:23]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:34 with lines lt -1

set origin 0.0,0.6;  set ylabel "Oil Pressure (lb/in^2)"
set yrange [-5:5]
plot '/Users/kwh/ftdata/python/POC/sample_data_files/RV-8_Data_2006-03-31-0958.txt' using 1:35 with lines lt -1

unset multiplot


  
