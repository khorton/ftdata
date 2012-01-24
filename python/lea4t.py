#! /sw/bin/python2.4

"""
Connects to u-Blox Antaris LEA-4T GPS, logs all raw data to a file, extracts
the GPS time and logs it to a second file, with each GPS time block 
annotated with computer time, to facilitate time synchronization with other
devices.
"""

# TO DO: 1. 

# DONE   1. 



from __future__ import division
import time
import re
import struct
import os.path
import antaris4


block_size = 200

class LEA4T:
    device_name = 'LEA4T'
    baudrate    =  57600
    bytesize    = 'EIGHTBITS'
    parity      = 'N'
    stopbits    =  1
    timeout     =  0.1
    xonxoff     =  0
    rtscts      =  0
    data_to_record   =  {'ITOW': 1,
                         'TACC': 1,
                         'NANO': 1,
                         'YEAR': 1,
                        'MONTH': 1,
                          'DAY': 1,
                         'HOUR': 1,
                       'MINUTE': 1,
                       'SECOND': 1}
    order_label_units = [('ITOS','GPS time of week','ms'),
                         ('TACC','Time accuracy','ns'),
                         ('NANO','nanoseconds','ns'),
                         ('YEAR','Year','year'),
                         ('MONTH','Month','month'),
                         ('DAY','Day','day'),
                         ('HOUR','Hour','hour'),
                         ('MINUTE','Minute','minute'),
                         ('SECOND','Second','second')]
    scaling          =  {'ITOW': 1,
                         'TACC': 1,
                         'NANO': 1,
                         'YEAR': 1,
                        'MONTH': 1,
                          'DAY': 1,
                         'HOUR': 1,
                       'MINUTE': 1,
                       'SECOND': 1}
}

def parse_lea4t(data_block):
    """
    Parses data block from LEA-4T 
    """
    
    
# def parse_eis(data_block):
#   # unpack data and set the scaling
#   # unsigned data bytes are grabbed with 'B', one per byte
#   # it is believed that b = signed char, will give a two's
#   #   complement
#   fmt = '39B3b28B'
#   (tachh, tachl, cht1h, cht1l, cht2h, cht2l, cht3h, cht3l, \
#   cht4h, cht4l, cht5h, cht5l, cht6h, cht6l, egt1h, egt1l, \
#   egt2h, egt2l, egt3h, egt3l, egt4h, egt4l, egt5h, egt5l, \
#   egt6h, egt6l, daux1h, daux1l, daux2h, daux2l, aspdh, \
#   aspdl, alth, altl, volth, voltl, fuelfh, fuelfl, unit, \
#   carb, rocsgn, oat, oilth, oiltl, oilp, aux1h, aux1l, \
#   aux2h, aux2l, aux3h, aux3l, aux4h, aux4l, coolh, cooll, \
#   etih, etil, qtyh, qtyl, hrs, min, sec, endhrs, endmin, \
#   baroh, barol, maghdh, maghdl, spare, checksum) = \
#   struct.unpack(fmt, data_block)
#   
#   tach = tachh * 256 + tachl
#   cht1 = cht1h * 256 + cht1l
#   cht2 = cht2h * 256 + cht2l
#   cht3 = cht3h * 256 + cht3l
#   cht4 = cht4h * 256 + cht4l
#   cht5 = cht5h * 256 + cht5l
#   cht6 = cht6h * 256 + cht6l
#   egt1 = egt1h * 256 + egt1l
#   egt2 = egt2h * 256 + egt2l
#   egt3 = egt3h * 256 + egt3l
#   egt4 = egt4h * 256 + egt4l
#   egt5 = egt5h * 256 + egt5l
#   egt6 = egt6h * 256 + egt6l
#   daux1 = daux1h * 256 + daux1l
#   daux2 = daux2h * 256 + daux2l
#   aspd = aspdh * 256 + aspdl
#   alt = alth * 256 + altl
#   volt = volth * 25.6 + voltl / 10.0
#   fuelf = fuelfh * 25.6 + fuelfl / 10.0
#   rocsgn = rocsgn * 100
#   oilt = oilth * 256 + oiltl
#   aux1 = aux1h * 256 + aux1l
#   aux2 = aux2h * 256 + aux2l
#   aux3 = aux3h * 256 + aux3l
#   aux4 = aux4h * 256 + aux4l
#   cool = coolh * 256 + cooll
#   eti = etih * 25.6 + etil / 10.0
#   qty = qtyh * 25.6 + qtyl / 10.0
#   baro = baroh * 2.56 + barol / 100.0
#   maghd = maghdh * 25.6 + maghdl / 10.0
# 
#   return [tach, cht1, cht2, cht3, cht4, cht5, cht6, \
#   egt1, egt2, egt3, egt4, egt5, egt6, daux1, daux2, 
#   aspd, alt, volt, fuelf, unit, carb, rocsgn, oilt, oilp, \
#   oat, aux1, aux2, aux3, aux4, cool, eti, qty, hrs, min, sec, \
#   endhrs, endmin, baro, maghd, checksum]


def grab_lea4t_data(test_mode, data_rate, duration, serial_list, outputs):
    """
    Reads a block of data from the GPS and searches for the start of a 
    NAV-TIMEUTC data block.  If the start of a NAV-TIMEUTC data block is
    found, the computer time is noted, and another data block is read to
    ensure that a complete NAV-TIMEUTC data block is present, then all this
    data is sent to be parsed.
    
    The contents of the NAV-TIMEUTC data block, with the computer time, are
    written to a log file to facilitate syncing of post-processed GPS data
    with data from other devices.
    
    Every byte of raw data from the GPS is written to a second log file for
    post-processing.
    """
    if test_mode == '1':
        data_source = file('/Users/kwh/sw_projects/python/antaris_data/home-work-20061106.ubx', 'rU')
    else:
        data_source = serial_list['LEA4T']
        
    print 'Starting LEA4T thread.  Test mode =', test_mode, \
      'Data source is:', data_source
      
    # find the four bytes that mark the start of a NAV-TIMEUTC block, then 
    # grab the rest of the block, if it was read
    match_start_of_block = re.compile('.*\xb5\x62\x01\x21(?P<re_first_part>.{0,22})', re.DOTALL)
    
    start_time = time.time()
    data_time = start_time
    while data_time < (start_time + duration * 60):
        data_time = time.time()
        time.sleep(delay_time)
        data_count = data_time * data_rate
        block = data_source.read(block_size)
        outputs['LEA4T_raw'].write(block)
        
        # find four byte header, plus the rest of the read
        match1 = match_start_of_block.search(block)
        if match1:
            data_start = match1.group('re_first_part')
            # if $match_start is too short, grab another chunck, which 
            # has the rest of the data record.
            if len(data_start) < 22:
                block = data_source.read(block_size)
                outputs['LEA4T_raw'].write(block)
                match2 = match_end_of_block.search(block)

def grab_eis_data(test_mode, data_rate, duration, serial_list, outputs, ):
    
    
# find the rest of the data record, and save the start of the next one, in case it is needed
    match_end_of_block = re.compile('(?P<re_second_part>.{0,70})\xfe\xff\xfe(?P<re_first_part22>.{0,70})', re.DOTALL)
    
    start_time = time.time()
    raw_count = start_time * data_rate
    count = int(raw_count)
    data_time = start_time
    while data_time < (start_time + duration * 60):
        data_time = time.time()
        if test_mode == '0':
            data = data_source.read(block_size)
            time.sleep(delay_time)
        else:
            data = data_source.read(block_size)
            data += '\n'
        time.sleep(delay_time)
        
        data_count = data_time * data_rate
        if data_count >= count:
            block = data_source.read(block_size)
            
            # find three byte header, plus the rest of the read
            match1 = match_start_of_block.search(block)
            if match1:
                data_start = match1.group('re_first_part')
                # if $match_start is too short, grab another chunck, which 
                # has the rest of the data record.
                if len(data_start) < 70:
                    block = data_source.read(block_size)
                    match2 = match_end_of_block.search(block)
                                        
                    # assemble the two parts
                    if match2:
                        data_end = match2.group('re_second_part')
                        data = data_start + data_end
                    else:
                        print 'No match2 in EIS data'
                else:
                    data = data_start
                
                try:
                    (tach, cht1, cht2, cht3, cht4, cht5, cht6, \
                    egt1, egt2, egt3, egt4, egt5, egt6, daux1, daux2, 
                    aspd, alt, volt, fuelf, unit, carb, rocsgn, oilt, oilp, \
                    oat, aux1, aux2, aux3, aux4, cool, eti, qty, hrs, min, sec, \
                    endhrs, endmin, baro, maghd, checksum) = parse_eis(data)
                    
                    mp = aux1 / 10
                    
                    data_string = str(data_time) + '\t' + str(tach) + '\t'\
                    + str(mp) + '\t' + str(oat) + '\t' + str(fuelf) + '\t'\
                    + str(qty) + '\t' + str(cht1) + '\t' + str(cht2) + '\t'\
                    + str(cht3) + '\t' + str(cht4) + '\t' + str(egt1) + '\t'\
                    + str(egt2) + '\t' + str(egt3) + '\t' + str(egt4) + '\t'\
                    + str(oilt) + '\t' + str(oilp) + '\t' + str(volt) + '\t'\
                    + str(aux4) + '\t'+ str(eti) + '\t' + str(hrs) + '\t' \
                    + str(min) + '\t' + str(sec) + '\t' + str(endhrs) + '\t'\
                    + str(endmin) + '\t' + str(unit) + '\n'
                    outputs['EIS4000'].write(data_string)
                except:
                    print 'Got an error when passing to the parse_eis function.'
                    print 'Data length is:', len(data), 'It should be 70.'
            count = count + 1
                
                
        # has the main thread sent a stop flag?
        if os.path.exists('stop_recording.flag'):
            print 'EIS data recording stopping'
            outputs['LEA4T_raw'].close()
            outputs['LEA4T_time'].close()
            return
        
        # print tell tale, to let us know it is still alive.
#       print 'EIS script alive. ', 
    print 'EIS data recording shutting down'
    outputs['EIS4000'].close()

                
