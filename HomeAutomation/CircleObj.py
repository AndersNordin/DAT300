#!/usr/bin/python
'''
Created on Sep 29, 2014

@author: anders
'''
from plugwise import Stick
from plugwise.api import Circle

class CircleObj:
    '''
    This class represent a given device which can be controlled
    and manipulated through several methods.
    '''
    CIRCLEPLUS_MAC = "000D6F0001A44DE1"
    CIRCLE1_MAC = "000D6F0001A44958"
    USB_PORT = "/dev/ttyUSB0"

    def __init__(self, mac):
        usbStick = Stick(port=CircleObj.USB_PORT)
        self.device = Circle(mac, usbStick)       
        
    def switchOn(self):
        self.device.switch_on()
             
    def switchOff(self):
        self.device.switch_off()    