#! /sw/bin/python2.4

# TO DO: 1. Fixed 21 Mar 06.

# DONE   1. Not a problem with this module.  Other modules fixed on 21 Mar 06,
#           SVN version 279.



import time
import re
import struct
import os.path
import Queue


block_size = 75

class EIS4000:
	device_name = 'EIS4000'
	baudrate    =  9600
	bytesize    = 'EIGHTBITS'
	parity      = 'N'
	stopbits    =  1
	timeout     =  1
	xonxoff     =  0
	rtscts      =  0
	data_to_record   =  {'TACH': 1,
                         'CHT1': 1,
                         'CHT2': 1,
                         'CHT3': 1,
                         'CHT4': 1,
                         'CHT5': 0,
                         'CHT6': 0,
                         'EGT1': 1,
                         'EGT2': 1,
                         'EGT3': 1,
                         'EGT4': 1,
                         'EGT5': 0,
                         'EGT6': 0,
                        'DAUX1': 0,
                        'DAUX2': 0,
                         'ASPD': 0,
                          'ALT': 0,
                         'VOLT': 1,
                    'FUEL_FLOW': 1,
                    'UNIT_TEMP': 1,
                         'CARB': 0,
                       'ROCSGN': 0,
                          'OAT': 1,
                         'OILT': 1,
                         'OILP': 1,
                         'AUX1': 1,
                         'AUX2': 0,
                         'AUX3': 0,
                         'AUX4': 0,
                         'COOL': 0,
                          'ETI': 1,
                          'QTY': 1,
                          'HRS': 1,
                          'MIN': 1,
                          'SEC': 1,
                       'ENDHRS': 1,
                       'ENDMIN': 1,
                         'BARO': 0,
                        'MAGHD': 0}
	order_label_units = [('TACH','RPM','RPM'),
                         ('AUX1','MP','in HG'),
                         ('OAT','OAT','deg C'),
                         ('FUEL_FLOW','Fuel Flow','USG/hr'),
                         ('QTY','Fuel Qty','USG'),
                         ('CHT1','CHT 1','deg C'),
                         ('CHT2','CHT 2','deg C'),
                         ('CHT3','CHT 3','deg C'),
                         ('CHT4','CHT 4','deg C'),
                         ('CHT5','CHT 5','deg C'),
                         ('CHT6','CHT 6','deg C'),
                         ('EGT1','EGT 1','deg C'),
                         ('EGT2','EGT 2','deg C'),
                         ('EGT3','EGT 3','deg C'),
                         ('EGT4','EGT 4','deg C'),
                         ('EGT5','EGT 5','deg C'),
                         ('EGT6','EGT 6','deg C'),
                         ('OILT','Oil Temp','deg C'),
                         ('OILP','Oil Press','psi'),
                         ('DAUX1','DAUX 1','?'),
                         ('DAUX2','DAUX 2','?'),
                         ('ASPD','Airspeed','kt'),
                         ('ALT','Altitude','ft'),
                         ('VOLT','Volt','volt'),
                         ('CARB','Carb Temp','deg C'),
                         ('ROCSGN','Rate of Climb','ft/mn'),
                         ('AUX2','Aux 2','?'),
                         ('AUX3','Aux 3','?'),
                         ('AUX4','Aux 4','?'),
                         ('COOL','Water Temp','deg C'),
                         ('ETI','Hour Meter','hr'),
                         ('HRS','Hrs','hr'),
                         ('MIN','Min','mn'),
                         ('SEC','Sec','s'),
                         ('ENDHRS','Hours End','hr'),
                         ('ENDMIN','Min End','mn'),
                         ('BARO','Altimeter','in HG'),
                         ('MAGHD','Heading','deg'),
                         ('UNIT_TEMP','Unit Temp','deg C')]
	scaling          =  {'TACH': 1,
                         'CHT1': 1,
                         'CHT2': 1,
                         'CHT3': 1,
                         'CHT4': 1,
                         'CHT5': 1,
                         'CHT6': 1,
                         'EGT1': 1,
                         'EGT2': 1,
                         'EGT3': 1,
                         'EGT4': 1,
                         'EGT5': 1,
                         'EGT6': 1,
                        'DAUX1': 1,
                        'DAUX2': 1,
                         'ASPD': 1,
                          'ALT': 1,
                         'VOLT': 0.1,
                    'FUEL_FLOW': 0.1,
                    'UNIT_TEMP': 1,
                         'CARB': 1,
                        'ROCSGN': 1,
                          'OAT': 1,
                         'OILT': 1,
                         'OILP': 1,
                         'AUX1': 0.1,
                         'AUX2': 1,
                         'AUX3': 1,
                         'AUX4': 1,
                         'COOL': 1,
                          'ETI': 0.1,
                          'QTY': 0.1,
                          'HRS': 1,
                          'MIN': 1,
                          'SEC': 1,
                       'ENDHRS': 1,
                       'ENDMIN': 1,
                         'BARO': 1,
                        'MAGHD': 1}


def parse_eis(data_block):
	# unpack data
	# unsigned data bytes are grabbed with 'B', one per byte
	# it is believed that b = signed char, will give a two's
	#   complement
	fmt = '39B3b28B'
	(tachh, tachl, cht1h, cht1l, cht2h, cht2l, cht3h, cht3l, \
	cht4h, cht4l, cht5h, cht5l, cht6h, cht6l, egt1h, egt1l, \
	egt2h, egt2l, egt3h, egt3l, egt4h, egt4l, egt5h, egt5l, \
	egt6h, egt6l, daux1h, daux1l, daux2h, daux2l, aspdh, \
	aspdl, alth, altl, volth, voltl, fuelfh, fuelfl, unit, \
	carb, rocsgn, oat, oilth, oiltl, oilp, aux1h, aux1l, \
	aux2h, aux2l, aux3h, aux3l, aux4h, aux4l, coolh, cooll, \
	etih, etil, qtyh, qtyl, hrs, min, sec, endhrs, endmin, \
	baroh, barol, maghdh, maghdl, spare, checksum) = \
	struct.unpack(fmt, data_block)
	
	tach = tachh * 256 + tachl
	cht1 = cht1h * 256 + cht1l
	cht2 = cht2h * 256 + cht2l
	cht3 = cht3h * 256 + cht3l
	cht4 = cht4h * 256 + cht4l
	cht5 = cht5h * 256 + cht5l
	cht6 = cht6h * 256 + cht6l
	egt1 = egt1h * 256 + egt1l
	egt2 = egt2h * 256 + egt2l
	egt3 = egt3h * 256 + egt3l
	egt4 = egt4h * 256 + egt4l
	egt5 = egt5h * 256 + egt5l
	egt6 = egt6h * 256 + egt6l
	daux1 = daux1h * 256 + daux1l
	daux2 = daux2h * 256 + daux2l
	aspd = aspdh * 256 + aspdl
	alt = alth * 256 + altl
	volt = volth * 25.6 + voltl / 10.0
	fuelf = fuelfh * 25.6 + fuelfl / 10.0
	rocsgn = rocsgn * 100
	oilt = oilth * 256 + oiltl
	aux1 = aux1h * 256 + aux1l
	aux2 = aux2h * 256 + aux2l
	aux3 = aux3h * 256 + aux3l
	aux4 = aux4h * 256 + aux4l
	cool = coolh * 256 + cooll
	eti = etih * 25.6 + etil / 10.0
	qty = qtyh * 25.6 + qtyl / 10.0
	baro = baroh * 2.56 + barol / 100.0
	maghd = maghdh * 25.6 + maghdl / 10.0

	return [tach, cht1, cht2, cht3, cht4, cht5, cht6, \
	egt1, egt2, egt3, egt4, egt5, egt6, daux1, daux2, 
	aspd, alt, volt, fuelf, unit, carb, rocsgn, oilt, oilp, \
	oat, aux1, aux2, aux3, aux4, cool, eti, qty, hrs, min, sec, \
	endhrs, endmin, baro, maghd, checksum]

def grab_eis_data(test_mode, data_rate, duration, serial_list, outputs, queues):
# def grab_eis_data(test_mode, data_rate, duration, serial_list, outputs, ):
	if test_mode == '1':
		data_source = file('/Users/kwh/ftdata/Tk/EIS_raw_data.dat', 'rU')
	else:
		data_source = serial_list['EIS4000']

	print 'Starting EIS thread.  Test mode =', test_mode, 'Data source is:', data_source

# find the three-byte record start indicator, then grab the rest of the block
	match_start_of_block = re.compile('.*\xfe\xff\xfe(?P<re_first_part>.{0,70})', re.DOTALL)
	
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
		else:
			data = data_source.read(block_size)
			data += '\n'
			time.sleep(0.1)
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
					+ str(eti) + '\t' + str(hrs) + '\t' + str(min) + '\t'\
					+ str(sec) + '\t' + str(endhrs) + '\t' + str(endmin) + '\t' + str(unit) + '\n'
					outputs['EIS4000'].write(data_string)
					queues['EIS4000'].put(data_string)
				except:
					print 'Got an error when passing to the parse_eis function.'
					print 'Data length is:', len(data), 'It should be 70.'
				
				
			# has the main thread sent a stop flag?
			if os.path.exists('stop_recording.flag'):
				print 'EIS data recording stopping'
				outputs['EIS4000'].close()
				return
 			
			count = count + 1
			# print tell tale, to let us know it is still alive.
			print 'EIS alive ', 

	outputs['EIS4000'].close()

				
