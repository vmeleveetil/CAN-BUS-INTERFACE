# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:48:26 2022

@author: vedanth.meleveetil
"""
import RPi.GPIO as GPIO
import can
import time
import os
import queue
from threading import Thread
from datetime import datetime

overvoltage_fault = True 
electrical_status_flags=""
overvoltage= ""
overtemp_fault = True
overtemp = ""
thermal_status_flags=""
error = True
flag_counter = 0

GPIO.setwarnings(False)
overvoltage_flag_LED = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(overvoltage_flag_LED, GPIO.OUT)

overtemp_flag_LED = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(overtemp_flag_LED, GPIO.OUT)

error_LED = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(error_LED, GPIO.OUT)

script_running_LED = 6
GPIO.setmode(GPIO.BCM)
GPIO.setup(script_running_LED, GPIO.OUT)
GPIO.output(script_running_LED, GPIO.HIGH)

save_path = "/home/pi/CAN-BUS-INTERFACE/Fault-Log/"
date_today = datetime.now()
date = date_today.strftime("%m-%d-%Y")
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
    global overvoltage_fault
    global error
    if overvoltage == '00':
        overvoltage_fault = True
        print("\nNot Active")
        error  = False
    elif overvoltage == '01':
        overvoltage_fault = False
        print("\nWarning")
        error  = False
    elif overvoltage == '10':
        overvoltage_fault = False
        print("\nAlarm")
        error  = False
    elif overvoltage == '11':
        error = True
        overvoltage_fault = False
        print("\nERROR")
def temp_fault_check(overtemp):
    global overtemp_fault
    global error
    if overtemp == '00':
        overtemp_fault = True
        print("\nNot Active (Thermal)")
        error  = False
    elif overtemp == '01':
        overtemp_fault = False
        print("\nWarning (Thermal)")
        error  = False
    elif overtemp == '10':
        overtemp_fault = False
        print("\nAlarm (Thermal)")
        error  = False
    elif overtemp == '11':
        error  = True
        overtemp_fault = False
        print("ERROR (Thermal)")

# Main loop
try:
    while True:
        if q.empty() != True:	# Check if there is a message in queue
            message = q.get()
            now = datetime.now()
            system_time = now.strftime("%H:%M:%S")
            c = 'Timestamp: {0} {1:f} {2:x} {3:x} '.format(system_time, message.timestamp, message.arbitration_id, message.dlc)
            s=''
            id ='{0:x}'.format(message.arbitration_id)
            for i in range(message.dlc ):
                s +=  '{0:x} '.format(message.data[i])
                
            if (identify_message_type(id) == "Electrical Data"):
                electrical_status_flags = '{0:b}'.format(message.data[0])
                overvoltage = electrical_status_flags[2] + electrical_status_flags[3]
                voltage_fault_check(overvoltage)
            elif (identify_message_type(id) == "Thermal Data"):
                thermal_status_flags = '{0:b}'.format(message.data[0])
                overtemp = thermal_status_flags[4] + thermal_status_flags[5]
                temp_fault_check(overtemp)
            
            if not (overvoltage_fault):
                GPIO.output(overvoltage_flag_LED, GPIO.HIGH)
                if flag_counter == 0:
                    outfile = open(save_path + date + ' fault log.txt','w')
                else:
                    outfile = open(save_path + date + ' fault log.txt','a')
                outstr = c+s
                print(outstr,file = outfile)
                flag_counter += 1
                time.sleep(5)
            else:
                GPIO.output(overvoltage_flag_LED, GPIO.LOW)
                
            if not (overtemp_fault):
                GPIO.output(overtemp_flag_LED, GPIO.HIGH)
                if flag_counter == 0:
                    outfile = open(save_path + date + ' fault log.txt','w')
                else:
                    outfile = open(save_path + date + ' fault log.txt','a')
                outstr = c+s
                print(outstr,file = outfile)
                flag_counter += 1
                time.sleep(5)
            else:
                GPIO.output(overtemp_flag_LED, GPIO.LOW)
            
            if error:
                GPIO.output(error_LED, GPIO.HIGH)
                if flag_counter == 0:
                    outfile = open(save_path + date + ' fault log.txt','w')
                else:
                    outfile = open(save_path + date + ' fault log.txt','a')
                outstr = c+s
                print(outstr,file = outfile)
                flag_counter += 1
                time.sleep(5)
            else:
                GPIO.output(error_LED, GPIO.LOW)
            
            print('\r {}'.format((c+s)),end ='') # Print data and queue size on screen
            
except KeyboardInterrupt:
	#Catch keyboard interrupt
    GPIO.output(script_running_LED, GPIO.LOW)
    os.system("sudo /sbin/ip link set can0 down")
    print('\n\rKeyboard interrtupt')