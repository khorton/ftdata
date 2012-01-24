#!/usr/bin/perl
# batch convert ps to pdf
#
# Useage: ps2pdf_batch.pl file1.ps file2.ps ...
#         or, ps2pdf_batch.pl *.ps

use warnings;
use strict;
my $argnum;

if ($#ARGV >= 0) {
  foreach (@ARGV) {
    system ( "ps2pdf $_" );
    $_ =~ s/ps/pdf/;
    if (-d "/Applications/Preview.app/") {
      system ( "open $_" );
    }
  }
  unless (-d "/Applications/Preview.app/") {
    foreach $argnum (0 .. $#ARGV) {
      system ( "evince $ARGV[$argnum]&");
    }
  } 
} else {
  print "Useage: ps2pdf_batch.pl file1.ps file2.ps, \nor ps2pdf_batch.pl *.ps\n";
}
