#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import numpy
from numpy.random.mtrand import np
from plugwise.api import Stick, Circle
import sqlite3
import sys
from threading import  Event
import threading
import time

from Settings import freezer_MAC, floorHeating_MAC, sqlAvgLastHourWithoutBG
import Settings
import matplotlib.animation as animation
import matplotlib.pyplot as plt


usbStick = Stick(port=Settings.USB_PORT)
finishFlag = 0
freezerPower = 16
floorPower = 80
funkar = -1

class BackgroundWorker(threading.Thread):
    def __init__(self, macAddr, unitID, name, scale, eventSignal, signalEvent, minTemp, maxTemp, linearChangeOn, linearChangeOff):
        threading.Thread.__init__(self)
        self.macAddr = macAddr
        self.id = unitID  
        self.name = name
        self.scale = scale
        self.eventSignal = eventSignal
        self.signalEvent = signalEvent
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.temp = maxTemp
        self.linearChangeOn = linearChangeOn
        self.linearChangeOff = linearChangeOff
        self.running = False
        self.slack = 0.0
    
    def run(self):
        unit = Circle(self.macAddr, usbStick)         
        
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
            self.eventSignal.clear()
            
            if(self.running):
                self.temp = self.temp + self.linearChangeOn
                if (self.id == 2016):
                    print "Switching " + str(self.name) + " on, temp = -" + str(self.temp)
                else:
                    print "Switching " + str(self.name) + " on, temp = " + str(self.temp)
                unit.switch_on()
            else:
                self.temp = self.temp + self.linearChangeOff
                if(self.id == 2016):
                    print "Switching " + str(self.name) + " off, temp = -" + str(self.temp)
                else:
                    print "Switching " + str(self.name) + " off, temp = " + str(self.temp)
                unit.switch_off()
  

        
class CoordinatorWorker(threading.Thread):
    def __init__(self, scale):
        threading.Thread.__init__(self)
        self.simulationScale = scale
        self.simTime = datetime.datetime(2000,1,1,0,0,0) # according database
#
    
    def run(self):       
        freezerSignal = Event()
        signalfreezer = Event()
        floorHeatingSignal = Event()
        signalFloorHeating = Event()
                        
        freezerWorker = BackgroundWorker(freezer_MAC, 2016, "Freezer", self.simulationScale, signalfreezer, freezerSignal, 17.0, 19.0, 0.25, -1.0)
        floorHeatingWorker = BackgroundWorker(floorHeating_MAC, 2236, "Floorheater", self.simulationScale, signalFloorHeating, floorHeatingSignal, 19.0, 21.0, 2.0, -0.66)
        freezerWorker.start()
        floorHeatingWorker.start()
        
        # Used for plotting
        backgroundPower = [10,10,10,10,10,10]
        backgroundPointer = 0
        totalValue = []
        totalValueWithoutLSF = []
        hours = []
        
        avgLastHour = 30 # just an initial value for the first hour.

        con = sqlite3.connect('data/energimynd_one_day.db')
        cur = con.cursor()
        
        plt.ion()
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], 'r-', label="LSF")
        self.lines2, = self.ax.plot([],[], 'b-', label="Without LSF")
        self.ax.set_autoscaley_on(True)
        self.ax.set_xlim(0, 1440)
        self.ax.set_ylim(0, 350)
        self.ax.set_xlabel('Minutes')
        self.ax.set_ylabel('Watt')
        
        self.ax.grid()
        plt.legend()
        
        xAxisMinArray = []
        myMinute = 0
    
        while(self.simTime.day == 1):   
            time.sleep(self.simulationScale)     
            
            
            xAxisMinArray.append(myMinute)
            myMinute = myMinute + 10
            
            prevHour = self.simTime - datetime.timedelta(hours=1)
            
            print self.simTime
            print "Threshold(avg watt): " + str(avgLastHour)

            # Calculate average value for last hour
            backgroundHour = 0 
            for index in range (6):
                backgroundHour += backgroundPower[index]
            
            if (prevHour.year != 1999):
                cur.execute(sqlAvgLastHourWithoutBG.format(prevHour, self.simTime))
                avgLastHour = cur.fetchone()[0] + (backgroundHour / 6)
                
            if (prevHour.hour >= 14 and prevHour.hour <= 16):
                floorPower = 160
            else:
                floorPower = 80
                                
            cur.execute(Settings.sqlNoBg.format(self.simTime)) 
            row = cur.fetchone()
            
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
            
            signalfreezer.set()
            signalFloorHeating.set()            
            
            totalValue.append(row[0] + backgroundPower[backgroundPointer]) 
            hours.append(self.simTime)
            print "Total consumption: " + str(row[0] + backgroundPower[backgroundPointer]) + " Watt"

            cur.execute(Settings.sqlAll.format(self.simTime)) 
            row2 = cur.fetchone()
            totalValueWithoutLSF.append(row2[0])

            self.on_running(xAxisMinArray, totalValue, totalValueWithoutLSF)

            backgroundPointer = (backgroundPointer + 1) % 6
        
            self.simTime += datetime.timedelta(minutes=10)
            print "\n"  
            
        con.close()        
        self.drawPlot(hours, totalValue)
        finishFlag = 1          
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

    def drawPlot(self, minutesArray, powerArray):
        plt.plot(minutesArray, powerArray)
        plt.ylabel('Watt')
        plt.xlabel('Hours')
        plt.show()  
# 

# How fast will the simulation go 
simulationScale = 0.1

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

coordinatorWorker = CoordinatorWorker(simulationScale)
coordinatorWorker.start()
coordinatorWorker.join()

print 'Program Exit' 
