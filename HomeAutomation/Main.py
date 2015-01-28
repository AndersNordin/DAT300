#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@since: 2014-11-28 
@author: Johannes Blomquist and Anders Nordin
'''
##############################
#TODO:
# - Implement greedy algorithm 
# - Plot greedy algorithm to compare against LSF.
# - Fix GUI(menus, graphs, controls, output console) 
# - Bugfix: One thread does not terminate causing the program to crash at the end.
# - Evaluate using more test data.
##############################
# Initilize the usb stick

import datetime
from plugwise.api import Stick, Circle
import sqlite3
import sys
from threading import  Event
import threading
import time
from Settings import freezer_MAC, floorHeating_MAC, sqlAvgLastHourWithoutBG
import Settings
import matplotlib.pyplot as plt


usbStick = Stick(port=Settings.USB_PORT)

# Values in watt. Taken from analyzing plots in database.
freezerPower = 16
floorPower = 80
finishFlag = 0
funkar = -1


class BackgroundWorker(threading.Thread):
    '''
    This class represents a unit which adds background load.
    Example: Fridge, Floorheater, AC etc
    '''
    
    def __init__(self, macAddr, unitID, name, scale, eventSignal, signalEvent, minTemp, maxTemp, linearChangeOn, linearChangeOff):
        threading.Thread.__init__(self)
        # MAC Address on the circle
        self.macAddr = macAddr
        
        #unit ID used in database
        self.id = unitID  
        
        # unit name
        self.name = name
        
        #Time scale
        self.scale = scale
        
        # events
        self.eventSignal = eventSignal
        self.signalEvent = signalEvent
        
        # temperature is comfort levels in the system(threshold).
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.temp = maxTemp
        
        
        self.linearChangeOn = linearChangeOn
        self.linearChangeOff = linearChangeOff
        self.running = False
        self.slack = 0.0
        self.unit = Circle(self.macAddr, usbStick)   
    
    def run(self):
        while not finishFlag:
           
            self.slack = (self.temp - self.minTemp) / abs(self.linearChangeOff)
            if(self.slack < 0):
                self.slack = 0.0
            elif(self.temp >= self.maxTemp):
                self.slack = 99.9
                
            # Allow coordinator to proceed
            self.signalEvent.set()
            
            # wait for permission to proceed
            self.eventSignal.wait()
            
            # clear previous events
            self.eventSignal.clear()
            
            if(self.running):
                self.temp = self.temp + self.linearChangeOn
                if (self.id == 2016):
                    print "Switching " + str(self.name) + " on, temp = -" + str(self.temp)
                else:
                    print "Switching " + str(self.name) + " on, temp = " + str(self.temp)
                self.unit.switch_on()
            else:
                self.temp = self.temp + self.linearChangeOff
                if(self.id == 2016):
                    print "Switching " + str(self.name) + " off, temp = -" + str(self.temp)
                else:
                    print "Switching " + str(self.name) + " off, temp = " + str(self.temp)
                self.unit.switch_off()
#

        
class CoordinatorWorker(threading.Thread):
    '''
    Central class to coordinate the simulation
    '''
    
    def __init__(self, scale):
        threading.Thread.__init__(self)
        
        # Time scale
        self.simulationScale = scale
        
        # Date is set to starting date from database
        self.simTime = datetime.datetime(2000,1,1,0,0,0) 
#

    def run(self):       
        # Initialize events
        freezerSignal = Event()
        signalfreezer = Event()
        floorHeatingSignal = Event()
        signalFloorHeating = Event()
        
        # Create threads and start them
        freezerWorker = BackgroundWorker(freezer_MAC, 2016, "Freezer", self.simulationScale, signalfreezer, freezerSignal, 17.0, 19.0, 0.25, -1.0)
        floorHeatingWorker = BackgroundWorker(floorHeating_MAC, 2236, "Floorheater", self.simulationScale, signalFloorHeating, floorHeatingSignal, 19.0, 21.0, 2.0, -0.66)
        freezerWorker.start()
        floorHeatingWorker.start()
        
        # Used for plotting
        backgroundPower = [10,10,10,10,10,10]
        backgroundPointer = 0
        
        # Y-axis in plot(Watt)
        totalValue = []
        
        # Y-axis in plot(Watt)
        totalValueWithoutLSF = []
        
        # x-axis in plot(datetimes)
        hours = []
        
        # just an initial value for the first hour.
        avgLastHour = 30 

        # Initialize database
        con = sqlite3.connect('data/test_data.db')
        cur = con.cursor()
        
        # Initialize real-time plot
        plt.ion()
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], 'r-', label="LSF")
        self.lines2, = self.ax.plot([],[], 'b-', label="Without LSF")
        self.lines2.set_linestyle('--')
        self.ax.set_autoscaley_on(True)
        self.ax.set_xlim(0, 1440)
        self.ax.set_ylim(0, 350)
        self.ax.set_xlabel('Minutes')
        self.ax.set_ylabel('Watt')
        self.ax.grid()
        plt.legend()
        
        # X-axis in plot
        xAxisMinArray = []
        myMinute = 0
    
        while(self.simTime.day == 1):
            # This sleep decides how fast the simulation should proceed   
            time.sleep(self.simulationScale)     
            
            xAxisMinArray.append(myMinute)
            myMinute = myMinute + 10
            
            # Value used for calculating average power consumption
            prevHour = self.simTime - datetime.timedelta(hours=1)
            
            # Print current time in the loop.
            print self.simTime
            print "Threshold(avg watt): " + str(avgLastHour)

            # Calculate average value for last hour. Used as threshold
            backgroundHour = 0 
            for index in range (6):
                backgroundHour += backgroundPower[index]
            
            # Earliest year in database is 2000. Therefore 1999 is invalid.
            if (prevHour.year != 1999):
                cur.execute(sqlAvgLastHourWithoutBG.format(prevHour, self.simTime))
                avgLastHour = cur.fetchone()[0] + (backgroundHour / 6)
                
            if (prevHour.hour >= 14 and prevHour.hour <= 16):
                floorPower = 160
            else:
                floorPower = 80
                                
            # Get data from database
            cur.execute(Settings.sqlNoBg.format(self.simTime)) 
            row = cur.fetchone()
            
            # Events
            freezerSignal.wait()
            freezerSignal.clear()
            floorHeatingSignal.wait()
            floorHeatingSignal.clear()

            # standard not to runSwitching
            freezerWorker.running = False
            floorHeatingWorker.running = False
            backgroundPower[backgroundPointer] = 0
            
            
            if(freezerWorker.slack <= floorHeatingWorker.slack):
                if((avgLastHour > float(row[0]) or freezerWorker.slack == 0) and freezerWorker.slack != 99.9):
                    freezerWorker.running = True
                    backgroundPower[backgroundPointer] += freezerPower
                    if(((avgLastHour + freezerPower) > float(row[0]) or floorHeatingWorker.slack == 0) and floorHeatingWorker.slack != 99.9):
                        floorHeatingWorker.running = True
                        backgroundPower[backgroundPointer] += floorPower
            else:
                if(avgLastHour > float(row[0]) or floorHeatingWorker.slack == 0):
                    floorHeatingWorker.running = True
                    backgroundPower[backgroundPointer] += floorPower
                    if(((avgLastHour + floorPower) > float(row[0])) and freezerWorker.slack != 99.9):
                        freezerWorker.running = True
                        backgroundPower[backgroundPointer] += freezerPower
            
            # Trigger events
            signalfreezer.set()
            signalFloorHeating.set()            
            
            # Add total consumption for this lap in the simulation
            totalValue.append(row[0] + backgroundPower[backgroundPointer])
            print "Total consumption: " + str(row[0] + backgroundPower[backgroundPointer]) + " Watt"

            # add to x-axis 
            hours.append(self.simTime)

            # Query database
            cur.execute(Settings.sqlAll.format(self.simTime)) 
            row2 = cur.fetchone()
            
            # Compare-value 
            totalValueWithoutLSF.append(row2[0])

            # Plot dynamically
            self.on_running(xAxisMinArray, totalValue, totalValueWithoutLSF)


            backgroundPointer = (backgroundPointer + 1) % 6
            
            # Grab next 10 minutes from test data
            self.simTime += datetime.timedelta(minutes=10)
            
            # Just for nicer debugging
            print "\n"  
            
        # Close connection to database
        con.close()     
    
        # Draw final plot(not used anymore)   
        self.drawPlot(hours, totalValue)
        
        # Finish threads
        finishFlag = 1          
        
        # wait for background worker to finish
        freezerWorker.join()  
#

    def on_running(self, xdata, ydata, y2data):
        # Update data (with the new _and_ the old points)
        self.lines.set_xdata(xdata)
        self.lines.set_ydata(ydata)
        self.lines2.set_xdata(xdata)
        self.lines2.set_ydata(y2data)
        # Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        # We need to draw *and* flush        
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
#

    def drawPlot(self, minutesArray, powerArray):
        '''
        Draw final simulation plot. (Not used anymore)
        '''
        plt.plot(minutesArray, powerArray)
        plt.ylabel('Watt')
        plt.xlabel('Hours')
        plt.show()  
# 

# How fast will the simulation go 
simulationScale = 1

# This section handles input from user. Set the simulation scale accordinly
if len(sys.argv) > 1:
    if sys.argv[1]:
        if float(sys.argv[1]) > 0:
            print "Program simulation will run with speed 1 h = {} seconds".format(float(sys.argv[1]))
            simulationScale = float(sys.argv[1])
        elif float(sys.argv[1]) <= 0:
            print "Time cannot be negative."
            sys.exit(1)
    else:
        print "Argument must be a positive number."
else:
    print "Program simulation will be set to default(1 h = 0.1 seconds)."
    
    
# Start simulation 
coordinatorWorker = CoordinatorWorker(simulationScale)
coordinatorWorker.start()
coordinatorWorker.join()

print 'Program Exit' 
