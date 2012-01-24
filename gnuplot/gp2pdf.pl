#!/usr/bin/perl
# batch convert gnuplot files to ps to pdf
#
# Useage: gp2pdf.pl file1.gp file2.gp ...
#         or, gp2pdf *.gp

# Incomplete - look at having it move the gnuplot file to a temp directory,
#              run it, then convert all .ps in the temp to pdf, then copy them back.

use warnings;
use strict;
use Cwd;

my $TEMP_DIR = "~/temp/gp";

my $SCRIPT_HOME = &Cwd::cwd();

system ( "rm -fr $TEMP_DIR/*" );

if ($#ARGV >= 0) {
  foreach (@ARGV) {
    print "file is $_\n";
    system ( "cp $_ $TEMP_DIR/$_" );
  }
} else {
  print "Useage: gp2pdf.pl file1.gp file2.gp, \nor gp2pdf.pl *.gp\n";
  exit;
}
    system ( "cd $TEMP_DIR; gnuplot *.gp" );
    system ( "cd $TEMP_DIR; $SCRIPT_HOME/ps2pdf_batch.pl *.ps" );
    system ( "cd $TEMP_DIR; cp *.pdf $SCRIPT_HOME" );
