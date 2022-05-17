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

overvoltage_fault = False
electrical_status_flags=""
overvoltage= ""
overtemp_fault = False
overtemp = ""
thermal_status_flags=""

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

#Identify thermal or electrical data
def identify_message_type(str):
    if str[4] == '1':
        return "Electrical Data"
    elif str[4] == '2':
        return "Thermal Data"
#Raise Faults
def voltage_fault_check(overvoltage):
    if overvoltage == '00':
        overvoltage_fault = False
    elif overvoltage == '01':
        overvoltage_fault = True
    elif overvoltage == '10':
        overvoltage_fault = True
    elif overvoltage == '11':
        print("ERROR")
def temp_fault_check(overtemp):
    if overtemp == '00':
        overtemp_fault = False
    elif overtemp == '01':
        overtemp_fault = True
    elif overtemp == '10':
        overtemp_fault = True
    elif overtemp == '11':
        print("ERROR")

# Main loop
try:
    while True:
        if q.empty() != True:	# Check if there is a message in queue
            message = q.get()
            c = '{0:f} {1:x} {2:x} '.format(message.timestamp, message.arbitration_id, message.dlc)
            s=''
            id ='{0:x}'.format(message.arbitration_id)
            if (identify_message_type(id) == "Electrical Data"):
                electrical_status_flags = '{0:b}'.format(message.data[0])
                overvoltage = electrical_status_flags[2] + electrical_status_flags[3]
            elif (identify_message_type(id) == "Thermal Data"):
                thermal_status_flags = '{0:b}'.format(message.data[0])
                overtemp = thermal_status_flags[4] + thermal_status_flags[5]
            voltage_fault_check(overvoltage)
            temp_fault_check(overtemp)
            for i in range(message.dlc ):
                s +=  '{0:x} '.format(message.data[i])
            
            #print('\n {} Data:{}       '.format((c+s),identify_message_type(id)),end ='') # Print data and queue size on screen
            print(electrical_status_flags+" "+thermal_status_flags)
            print(overvoltage + " " +overtemp)
except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrtupt')	
