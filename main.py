# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:48:26 2022

@author: vedanth.meleveetil
"""

import can
import time
import os

bInit = True

while True:
    if bool(bInit):
        system("sudo /sbin/ip link set can0 down")
        print('\n\rReset CAN Link')
        print('\n\rBring up CAN0....')
        os.system("sudo /sbin/ip link set can0 up type can bitrate 500000")
        time.sleep(0.1)	
        try:
        	bus = can.interface.Bus(channel='can0', bustype='socketcan')
        except OSError:
        	print('Cannot find PiCAN board.')
        	exit()
        print('Ready')
        bInit= False

try:
	while True:
		message = bus.recv()	# Wait until a message is received.
		
		c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
		s=''
		for i in range(message.dlc ):
			s +=  '{0:x} '.format(message.data[i])
			  
		print(' {}'.format(c+s))
	