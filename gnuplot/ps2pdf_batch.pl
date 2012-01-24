#!/usr/bin/perl
# batch convert ps to pdf
#
# Useage: ps2pdf_batch.pl file1.ps file2.ps ...
#         or, ps2pdf_batch.pl *.ps

use warnings;
use strict;

if ($#ARGV >= 0) {
  foreach (@ARGV) {
#    print "$_\n";
  system ( "ps2pdf $_" );
  $_ =~ s/ps/pdf/;
  system ( "open $_" );  
  }
} else {
  print "Useage: ps2pdf_batch.pl file1.ps file2.ps, \nor ps2pdf_batch.pl *.ps\n";
}