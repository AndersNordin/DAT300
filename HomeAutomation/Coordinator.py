'''
Created on Sep 23, 2014

@author: anders
'''
from Tkinter import *
from plugwise import Stick
from plugwise.api import Circle
import threading
import tkMessageBox

import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np


class powerThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.fig = plt.figure()
        self.ax = plt.axes(xlim=(0, 2), ylim=(-2, 2))
        self.line, = self.ax.plot([], [], lw=2)

    def initGraph(self):
        self.line.set_data([], [])
        return self.line,
    
    # animation function.  This is called sequentially
    def animate(self,i):
        x = np.linspace(0, 2, 1000)
        y = np.sin(2 * np.pi * (x - 0.01 * i))
        self.line.set_data(x, y)
        return self.line,
        
    def run(self):
        print "Starting " + self.name
        anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.initGraph,
                               frames=200, interval=20, blit=True)        
        
        plt.show()        


class HomeAutomationApp(object):
    
    # Static variables
    CIRCLEPLUS_MAC = "000D6F0001A44DE1"
    CIRCLE1_MAC = "000D6F0001A44958"
    USB_PORT = "/dev/ttyUSB0"

    def __init__(self):
        
        # Init variables
        usbStick = Stick(port=HomeAutomationApp.USB_PORT)
        self.circlePlus = Circle(HomeAutomationApp.CIRCLEPLUS_MAC, usbStick)      
        self.circleSec = Circle(HomeAutomationApp.CIRCLE1_MAC, usbStick)
              
        self.initGUI()    
    
    
    def initGUI(self):
        # Initialize main window component
        self.mainWindow = Tk()
        self.mainWindow.wm_title("Home Automation Control")
        #self.mainWindow.minsize(width=800,height=600)
        
        # Create and setup menu
        menubar = Menu(self.mainWindow)
        filemenu = Menu(menubar, tearoff=0)        
        filemenu.add_command(label="Restart")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.mainWindow.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help")
        helpmenu.add_command(label="About...", command=self.displayAbout)
        menubar.add_cascade(label="Help", menu=helpmenu)
                
        # Declare a control variable
        self.ctrlVar = StringVar()
        self.ctrlVar.set(HomeAutomationApp.CIRCLEPLUS_MAC) # initial value
        
        # Area for manual control
        groupCtrl = LabelFrame(self.mainWindow, text="Manual Control", padx=10, pady=10)
        groupCtrl.grid(row=0, column=2)
        
        option = OptionMenu(groupCtrl, self.ctrlVar, HomeAutomationApp.CIRCLEPLUS_MAC, HomeAutomationApp.CIRCLE1_MAC)
        option.config(width=20)
        option.pack()
        
        manualOnBtn = Button(groupCtrl, text="ON",command=self.switchOn)
        manualOnBtn.pack()
        
        menualOffBtn = Button(groupCtrl, text="OFF", command=self.switchOff)
        menualOffBtn.pack()
        
        
        # Graph showing total usage
        powerGraph = Label(self.mainWindow, text="POWER USAGE GRAPH", padx=10, pady=10)
        powerGraph.grid(row=0, column=1)
        
        # Area which shows statistics       
        L1 = Label(self.mainWindow, text="Circle Plus", padx=10, pady=10)
        L1.grid(row=1, sticky=W)        
        E1 = Entry(self.mainWindow, bd =5)
        E1.grid(row=1, column=1)     
        
        L1 = Label(self.mainWindow, text="Circle Plus", padx=10, pady=10)
        L1.grid(row=2, sticky=W)        
        E1 = Entry(self.mainWindow, bd =5)
        E1.grid(row=2, column=1)     
        
        self.mainWindow.config(menu=menubar)
        
        # Output log
        #outputTextarea = Text(self.mainWindow, width=50)
        #outputTextarea.grid(row=1, column=2)      
        
        self.mainWindow.mainloop()
        
    
    def displayAbout(self):
        tkMessageBox.showinfo("About", "This app is created by Anders Nordin and Johannes Blomquist. 2014.")
                
    def switchOn(self):
        if(self.ctrlVar.get() == HomeAutomationApp.CIRCLEPLUS_MAC):
            self.circlePlus.switch_on()
        elif(self.ctrlVar.get() == HomeAutomationApp.CIRCLE1_MAC):
            self.circleSec.switch_on()
             
    def switchOff(self):
        if(self.ctrlVar.get() == HomeAutomationApp.CIRCLEPLUS_MAC):
            self.circlePlus.switch_off()
        elif(self.ctrlVar.get() == HomeAutomationApp.CIRCLE1_MAC):
            self.circleSec.switch_off() 
            
    def shutdown(self):
        pass
        
if __name__ == '__main__':    
    app = HomeAutomationApp()
    
    powerUsageWorker = powerThread(1, "AreYouThready")
    powerUsageWorker.start()
    print "Exit Thready"
    
    
    powerUsageWorker.join()
    