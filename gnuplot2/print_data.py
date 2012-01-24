#! /sw/bin/python2.4

# Script to create RV-8 flight test data plots.
#
# Usage - print_data.py plot_list.txt [optional list of plots]
# plot_list.txt contains a list of plots to create, with the data needed to
# create them.  An optional list of plot numbers may be specified, with the
# numbers corresponding to the order in plot_list.txt, with 1 being the first
# plot specified.
#
# The script reads a text file that contains the data file name, time slices
# data plot templates.  It inserts this data into a template to create a
# gnuplot command file.  gp2pdf can then be called, and it will create
# postscript output, which is converted to a pdf file which is passed to 
# Preview.
