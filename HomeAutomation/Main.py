#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Sep 23, 2014

@author: anders
'''
from Tkconstants import *
from Tkinter import BOTH, LabelFrame, Tk, Menu, Button, Label, Text
import datetime
import matplotlib.pyplot
from plugwise.api import Stick, Circle
import tkMessageBox
from ttk import Frame, Style

from Example import Plotter
import Settings


usbStick = Stick(port=Settings.USB_PORT)
circlePlus = Circle(Settings.CIRCLEPLUS_MAC, usbStick)      
circleSec = Circle(Settings.CIRCLE1_MAC, usbStick)

class HomeAutomationApp(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
         
        self.parent = parent        
        self.initUI()
        
    def initUI(self):
      
        self.parent.title("Home Automation Control Board")
        self.style = Style()
        self.style.theme_use("default")        
        
        self.pack(fill=BOTH, expand=1)
                
        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)        
        filemenu.add_command(label="Restart")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)             
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help")
        helpmenu.add_command(label="About...", command=self.displayAbout)
        menubar.add_cascade(label="Help", menu=helpmenu)         
        self.parent.config(menu=menubar)        
        
        
        groupCtrl = LabelFrame(self, text="Manual Control", width=320)
        groupCtrl.pack(fill=Y, side=LEFT)
        
        groupCtrl2 = LabelFrame(self, text="Statistics", width=320)
        groupCtrl2.pack(fill=Y, side=LEFT)
        
        self.T = Text(self)
        self.T.pack(side=LEFT, fill=Y)
        message = "Starting program..."
        self.writeMessageToOutput(message)

        
        l1 = Label(groupCtrl , text="Circle Plus")
        l1.pack()                
        manualOnBtn = Button(groupCtrl, text="ON", width=10, command=lambda: self.powerON(circlePlus))
        manualOnBtn.pack()               
        manualOffBtn = Button(groupCtrl, text="OFF",width=10, command=lambda: self.powerOff(circlePlus))
        manualOffBtn.pack()
        
        l2 =  Label(groupCtrl , text="Circle Secondary")
        l2.pack()
        manualOnBtn2 = Button(groupCtrl, text="ON", width=10, command=lambda: self.powerON(circleSec))
        manualOnBtn2.pack()               
        manualOffBtn2 = Button(groupCtrl, text="OFF",width=10, command=lambda: self.powerOff(circleSec))
        manualOffBtn2.pack()
        
        l3Title =  Label(groupCtrl2, text="Circle Plus (Watts)" )
        l3Title.pack()
        self.l3 =  Label(groupCtrl2)
        self.l3.pack()
        self.l3.after(200, self.displayPowerUsagePlus)
        
        l4Title =  Label(groupCtrl2, text="Circle Sec (Watts)" )
        l4Title.pack()
        self.l4 =  Label(groupCtrl2 )
        self.l4.pack()
        self.l4.after(200, self.displayPowerUsageSec)
        
    def powerON(self, unit):
        unit.switch_on()
        self.writeMessageToOutput("Switching on: " + unit.mac)
    
    def powerOff(self, unit):
        unit.switch_off()
        self.writeMessageToOutput("Switching off: " + unit.mac)
        

    def displayPowerUsagePlus(self):
        try:
            self.l3.config(text=str(circlePlus.get_power_usage()))
        except ValueError:
            self.l3.config(text="Value Error")

        self.l3.after(200, self.displayPowerUsagePlus)
        
    def displayPowerUsageSec(self):
        try:
            self.l4.config(text=str(circleSec.get_power_usage()))
        except ValueError:
            self.l4.config(text="Value Error")
        
        self.l4.after(200, self.displayPowerUsageSec)
        
    def writeMessageToOutput(self, msg):
        myPrompt = datetime.datetime.now().strftime('%H:%M:%S') + '> '
    
        
        self.T.config(state=NORMAL)
        
        self.T.insert(END, myPrompt + msg + '\n')
        self.T.config(state=DISABLED)
        self.T.see(END)
        
    def displayAbout(self):
        tkMessageBox.showinfo("About", "This app is created by Anders Nordin \
and Johannes Blomquist. 2014.")  

def main():  
    root = Tk()
    HomeAutomationApp(root)
    root.geometry("640x480")
    
    fig = matplotlib.pyplot.figure()
    Plotter(fig)
    
    fig.canvas.draw()
    fig.gca().clear()
    fig.gca().plot([1,2,3],[4,5,6])
    
    root.mainloop()  

if __name__ == '__main__':
    main()  

     
# option = OptionMenu(groupCtrl, CIRCLEPLUS_MAC, CIRCLE1_MAC)
# option.config(width=20)
# option.pack()        
# 
# powerUpgrade = StringVar()
# powerLabel = Label(root, textvariable = powerUpgrade)
# powerLabel.pack()
