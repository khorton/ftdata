#!/usr/bin/perl
#
use warnings;
use strict;
use Device::SerialPort;

  my $PortObj = new Device::SerialPort ("/dev/tty.USA49W1b1P1.1")
       || die "Can't open /dev/tty.USA49W1b1P1.1: $!\n";

  # similar
  $PortObj->baudrate(9600);
  $PortObj->parity("odd");
  $PortObj->databits(8);
  $PortObj->stopbits(1);
  my $HOME = "/Users/kwh";
  $PortObj->save("$HOME/.ftdata/EIS.config")
       || warn "Can't save Configuration File: $!\n";
exit;       
