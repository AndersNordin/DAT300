#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
from plugwise.api import Stick, Circle
import sqlite3
import sys
from threading import Thread, Event
import threading
from time import sleep
import time

from Settings import freezer_MAC, floorHeating_MAC, sqlAvgLastHour,\
    sqlAvgLastHourWithoutBG
import Settings
import matplotlib.pyplot as plt

#####
# Ta bort frysen från vår algoritm bg
#
#
#####

#usbStick = Stick(port=Settings.USB_PORT)
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
        #unit = Circle(self.macAddr, usbStick)         
        
        while not finishFlag:
            #sleep(0.001) #just so the while loop doesnt just run without any work.
            
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
                #unit.switch_on()
            else:
                self.temp = self.temp + self.linearChangeOff
                if(self.id == 2016):
                    print "Switching " + str(self.name) + " off, temp = -" + str(self.temp)
                else:
                    print "Switching " + str(self.name) + " off, temp = " + str(self.temp)
                #unit.switch_off()
            
            
            

        
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
        hours = []
        
        avgLastHour = 30 # just an initial value for the first hour.

        con = sqlite3.connect('data/energimynd_one_day.db')
        cur = con.cursor()

        
        while(self.simTime.day == 1):
            time.sleep(self.simulationScale)     
            
            prevHour = self.simTime - datetime.timedelta(hours=1)
            
            print self.simTime
            print "Avg: " + str(avgLastHour)

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

            print "Freezer slack: " + str(freezerWorker.slack)
            print "FloorHeating slack: " + str(floorHeatingWorker.slack)
            
            # standard not to run
            freezerWorker.running = False
            floorHeatingWorker.running = False
            backgroundPower[backgroundPointer] = 0
            
            if(freezerWorker.slack <= floorHeatingWorker.slack):
                if((avgLastHour > float(row[0]) or freezerWorker.slack == 0) and freezerWorker.slack != 99.9):
                    freezerWorker.running = True
                    backgroundPower[backgroundPointer] += freezerPower
                    print "adding freezer first IF"
                    if(((avgLastHour + freezerPower) > float(row[0]) or floorHeatingWorker.slack == 0) and floorHeatingWorker.slack != 99.9):
                        floorHeatingWorker.running = True
                        backgroundPower[backgroundPointer] += floorPower
                        print "adding floor first IF"
            else:
                if(avgLastHour > float(row[0]) or floorHeatingWorker.slack == 0):
                    floorHeatingWorker.running = True
                    backgroundPower[backgroundPointer] += floorPower
                    print "adding floor second IF"
                    if(((avgLastHour + floorPower) > float(row[0])) and freezerWorker.slack != 99.9):
                        freezerWorker.running = True
                        backgroundPower[backgroundPointer] += freezerPower
                        print "adding freezer second IF"
            
            signalfreezer.set()
            signalFloorHeating.set()            
            
            print "backgroundPower = " + str(backgroundPower)
            print "this backgroundPower = " + str(backgroundPower[backgroundPointer])    
            totalValue.append(row[0] + backgroundPower[backgroundPointer]) 
            hours.append(self.simTime)
            print "Total consumption: " + str(row[0] + backgroundPower[backgroundPointer])
            
            backgroundPointer = (backgroundPointer + 1) % 6
            
#             if avgLastHour > float(row[0]): 
#                 print "Total consumption: " + str(row[0]) + " [OK]"    
#                 nextExec = Settings.sqlAll      
#             else:
#                 print "Total consumption: " + str(row[0]) + " [PEAK]"
#                 nextExec = Settings.sqlNoBg
#             
            self.simTime += datetime.timedelta(minutes=10)
            print "\n"  

        con.close()        
        self.drawPlot(hours, totalValue)
        finishFlag = 1          
        freezerWorker.join()  
#
        
    def drawPlot(self, minutesArray, powerArray):
        plt.plot(minutesArray, powerArray)
        plt.ylabel('Watts')
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