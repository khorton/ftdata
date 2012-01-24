#!/usr/bin/perl
#
# Script to create RV-8 flight test data plots.
#   Works with the data format from Mike Kettleman.
#
# Usage - print_data.pl plot_list.txt [optional list of plots]
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

# TO DO 1. Add code to run gnuplot and ps2pdf.
#
#       2. Add a label to identify the mxtics interval on the plot.


use strict;
use warnings;
use diagnostics;
use Statistics::Descriptive;
use Switch;
use Text::Template;
my $template;

my $plot_list;
my @plot_nums_to_create;  # optional list of plot numbers to create 
my @lines;
my $date;
my $flt;
my $datafile;
my $col_max = "61";       # highest possible column number in the data
my $row_max;              # highest row number in data
my @plots;
my $plotnum = '0';
my %data;
my @numeric_flag;         # indicates which columns have numeric data
my $template_file;
my $OUTPUT_FILE;
my $file_num;
my $ps_file_name;
my $output;
our @testdata;            # array that holds all data from datafile
my $startline;            # line number in data that is greater than start of time slice.
my $endline;              # line number in data that is greater than end of time slice.
my %labels;               # label from data file that identifies data column
#my @stat;
my @min;                  # minimum value of data column in the time slice
my @max;                  # maximum value of data column in the time slice
my @mean;                 # mean value of data column in the time slice
my $time_diff;            # length of time slice in seconds
my ($format_x,$xlabel,$increment,$mxtics,$division_label); # x-axis settings

# get the plot_list from the command line switch.
if ($#ARGV >= 0) {
  $plot_list = $ARGV[0];
  if ($#ARGV >=1) {
    # command line also has a list of plot numbers
    for (my $i = 1; $i <= $#ARGV; $i++) {
      push @plot_nums_to_create, $ARGV[$i] - 1; 
    }
#     foreach (@plot_nums_to_create) {
#       print "Create plot $_\n";
#     }
#     exit;
  }
} else {
  die "Useage: print_data.pl plot_list.txt [optional list of plots]\n
  e.g. print_data.pl plot_list.txt 1 3\n
  plot_list.txt contains a list of plots to create, with the data needed to
  create them.  An optional list of plot numbers may be specified, with the
  numbers corresponding to the order in plot_list.txt, with 1 being the first
  plot specified in plot_list.txt.\n";
}


#create data for template.  Later, this data will be pulled from a text file.

# common data for all plots
# my $datafile = '/Users/kwh/ftdata/Tk/0510231059.csv';

# read data config file, and set parametres
open (PLOT_LIST , '<' , "$plot_list");


# if the plot_list is present, but not readable, alert the user.
if (-e $plot_list) {
  if (-r $plot_list != "1") {
    die "The plot list exists, but it is not readable.  Check the file permissions.\n";
  }
} else {
  die "The specified plot list does not exist.\n";
}

# get all the lines in the plot_list
@lines=<PLOT_LIST>;

foreach my $line (@lines) {
  if ($line !~ /^[#\s]/) {
    if ($line =~ /^date\s+\=\s+(.+)$/) {
      $date = $1;
    }
    
    if ($line =~ /^flt\s+\=\s+(.+)$/) {
      $flt = $1;
    }

    if ($line =~ /^datafile\s+\=\s+(.+)$/) {
      $datafile = $1;
    }

    if ($line =~ /^plot/) {
      if ($line =~ /^plot\s+(\w+)\s+["']([^"']+)["']\s+["']([^"']+)["']/) {
#        my $temp = "$1" . " Data";
        $plots[$plotnum] = ({ datafile => $datafile,
                                  date => $date,
                                   flt => $flt,
                              template => $1,
                                 start => $2,
                                   end => $3, });
      }
      
      if ($line =~ /^plot\s+(\w+)\s+["']([^"']+)["']\s+["']([^"']+)["']\s+label=["']([^"']+)["']/) {
        $plots[$plotnum] = ({ datafile => $datafile,
                                  date => $date,
                                   flt => $flt,
                              template => $1,
                                 start => $2,
                                   end => $3,
                            plot_label => $4 });
      }
      
    $plotnum ++;

    }
  }
}
#exit;
###############################################################################
#
# Read the flight test data into an array of arrays, so the min, max and median
# for each column can be pulled out.
#
# access data with $testdata[$row][$column]
# rows start at 1.  Column A is 0, B is 1, etc.
# The first row with real data is row 3 (in a complete data file).
#  print "In sub smart_autoscale\n";
  open(DATAFILE, "<$datafile"); # open for input
  @lines = <DATAFILE>;         # read file into list
  foreach my $line (@lines) {
    push @testdata, [ split (/,/, $line) ];
  }
# print "Element 20,50 is $testdata[20][50]\n";
# print "Element 1,1 is $testdata[1][1]\n";
# print "Element 5,0 is $testdata[5][0]\n";
  close(DATAFILE);
  
# load labels from data file into @labels
for (my $i = 0; $i <= $col_max; $i++) {
  # remove double quote characters from the label strings
  $testdata[0][$i] =~ s/\"//g;
  $labels{$testdata[0][$i]} = $i;
}

# determine highest row number, for later use
$row_max = $#testdata;

check_numeric();

###############################################################################

# process the templates
if ($#plot_nums_to_create == -1) {
  # There were no plot nums specified on the command line, so we do them all
  @plot_nums_to_create = ( 0 .. $#plots );
}

#for my $i ( 0 .. $#plots ) {
for my $i (@plot_nums_to_create ) {
  $file_num = $i + 1;
  $OUTPUT_FILE = "$file_num" . "-" . "$plots[$i]{template}.gp";
  open (OUTPUT , '>' , "$OUTPUT_FILE")
  or die "Can't open output file: $!";

  $template_file = "$plots[$i]{template}" . "." . "template"; 

  $template = new Text::Template (SOURCE => $template_file)
    or die "Couldn't construct template with file $template_file: $Text::Template::ERROR";
  #############################################################################
  # determine x-axis settings, based on the difference between start and end
  # times
  $time_diff = get_time_diff($plots[$i]{start},$plots[$i]{end}); 
  
  switch ($time_diff) {
    case {$time_diff <= 10} {
      $format_x = "%H:%M:%S";
      $xlabel = "time (H:M:S)";
      $increment = "1";
      $mxtics = "2";
      $division_label = "0.5 seconds";
    }
    case {$time_diff <= 20} {
      $format_x = "%H:%M:%S";
      $xlabel = "time (H:M:S)";
      $increment = "5";
      $mxtics = "5";
      $division_label = "1 second";
    }
    case {$time_diff <= 45} {
      $format_x = "%H:%M:%S";
      $xlabel = "time (H:M:S)";
      $increment = "5";
      $mxtics = "5";
      $division_label = "1 second";
    }
    case {$time_diff <= 90} {
      $format_x = "%H:%M:%S";
      $xlabel = "time (H:M:S)";
      $increment = "10";
      $mxtics = "5";
      $division_label = "2 seconds";
    }
    case {$time_diff <= 180} {
      $format_x = "%H:%M:%S";
      $xlabel = "time (H:M:S)";
      $increment = "20";
      $mxtics = "10";
      $division_label = "2 seconds";
    }
    case {$time_diff <= 240} {
      $format_x = "%H:%M:%S";
      $xlabel = "time (H:M:S)";
      $increment = "30";
      $mxtics = "6";
      $division_label = "5 seconds";
    }
    case {$time_diff <= 720} {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "60";
      $mxtics = "6";
      $division_label = "10 seconds";
    }
    case {$time_diff <= 1440} {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "120";
      $mxtics = "4";
      $division_label = "30 seconds";
    }
    case {$time_diff <= 3600} {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "300";
      $mxtics = "5";
      $division_label = "1 minute";
    }
    case {$time_diff <= 7200} {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "600";
      $mxtics = "5";
      $division_label = "2 minutes";
    }
    case {$time_diff <= 10800} {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "900";
      $mxtics = "3";
      $division_label = "5 minutes";
    }
    case {$time_diff <= 21600} {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "1800";
      $mxtics = "3";
      $division_label = "10 minutes";
    }
    else {
      $format_x = "%H:%M";
      $xlabel = "time (H:M)";
      $increment = "3600";
      $mxtics = "4";
      $division_label = "15 minutes";
    }
  }
  
  #############################################################################
  $ps_file_name = "$file_num" . "-" . "$plots[$i]{template}";
  %data = (   output => $ps_file_name,
            datafile => $datafile,
                date => $date,
                 flt => $flt,
            template => $plots[$i]{template},
               start => $plots[$i]{start},
                 end => $plots[$i]{end},
          plot_label => $plots[$i]{plot_label},
              labels => \%labels,
                 min => \@min,
                 max => \@max,
                mean => \@mean,
           increment => "$increment",
            format_x => "$format_x",
              xlabel => "$xlabel",
              mxtics => "$mxtics",
      division_label => $division_label,);
                  
  smart_autoscale();
  my $result = $template->fill_in(HASH => \%data, OUTPUT => \*OUTPUT );

  if (defined $result) { print $result }
    else { die "Couldn't fill in template: $Text::Template::ERROR" }
}

exit;

###############################################################################
sub smart_autoscale {
# subroutine to take a time slice and determine the required gnuplot yranges.
# This subroutine should be run once for each template.  It will populate an
# array of yranges to pass to the template.  (or maybe a hash is better.  Use
# column names rather than column numbers.)

  
# The following test passes, once the data time is more than one second
# greater than the start time.  This is close enough to determine scaling,
# as the extreme values should never be the first or last elements in the 
# time slice.
    
  # find line that matches start time slice
  for my $i (1 .. $row_max) {
    if ($testdata[$i][0] lt $data{'start'}) {
      $startline = $i;
    }
  }
#  print "Start line = $startline\n";
    
  # find line that matches end time slice
  for my $i (1 .. $row_max) {
    if ($testdata[$i][0] lt $data{'end'}) {
      $endline = $i;
#      print "Not there yet - line = $i\n";
    }
  }
#  print "End line = $endline\n";

  for my $column (2 .. $col_max) {
    if ($numeric_flag[$column] == "1") {
      my $stat = Statistics::Descriptive::Sparse->new();
      for my $i ($startline .. $endline) {
        $stat->add_data($testdata[$i][$column]);
      }
      
      $min[$column] = $stat->min();
      $max[$column] = $stat->max();
      $mean[$column] = $stat->mean();
    }
    
#    print "The range of $testdata[1][$column] is $min[$column]:$max[$column]\n";
  }
}

###############################################################################
sub check_numeric {
#
# determine which data columns have numeric data, and create an array of flags
# so nonnumeric data won't be used for statistics.

use Test::Numeric tests => 62;
  my $temp;
  for (my $i = 0; $i <= $col_max; $i++) {
    $temp = $testdata[$row_max][$i];
    $temp =~ s/\s//g;
    if (is_number $temp, "") {
      $numeric_flag[$i] = "1";
    }
  }
}

###############################################################################
sub get_time_diff {
  # split up start and end time in format from data file, and find the 
  # difference in seconds
  
  use Time::Local;
  my ($day,$month,$year,$hour,$minute,$second,$sec_start,$sec_end,$time_diff);

  $_[0] =~ /(\d+)\/(\d+)\/(\d+)\s(\d+):(\d+):(\d+)/;
    $month = $1;
    $day = $2;
    $year = $3;
    $hour = $4;
    $minute = $5;
    $second = $6;

  $sec_start = timelocal($second,$minute,$hour,$day,$month,$year);
  
  $_[1] =~ /(\d+)\/(\d+)\/(\d+)\s(\d+):(\d+):(\d+)/;
    $month = $1;
    $day = $2;
    $year = $3;
    $hour = $4;
    $minute = $5;
    $second = $6;
  
  $sec_end = timelocal($second,$minute,$hour,$day,$month,$year);
  
  $time_diff = $sec_end - $sec_start;
}


