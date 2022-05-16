# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:48:26 2022

@author: vedanth.meleveetil
"""

import can
import time
import os
import queue
from threading import Thread

os.system("sudo /sbin/ip link set can0 down")
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

# CAN receive thread
def can_rx_task():
	while True:
		message = bus.recv()
		q.put(message)			# Put message into queue

q = queue.Queue()	
t = Thread(target = can_rx_task)	# Start receive thread
t.start()

# Main loop
try:
	while True:
		if q.empty() != True:	# Check if there is a message in queue
			message = q.get()
			c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
			s=''
			for i in range(message.dlc ):
				s +=  '{0:x} '.format(message.data[i])

			print('\r {} qsize:{}       '.format((c+s),q.qsize()),end ='') # Print data and queue size on screen
			
	
except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrtupt')	
