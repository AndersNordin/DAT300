#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on Oct 16, 2014

@author: anders
'''

floorHeating_MAC = "000D6F0001A44DE1"
freezer_MAC = "000D6F0001A44958"
USB_PORT = "/dev/ttyUSB0"

sqlAll = "SELECT sum(CorrectedEnergy) FROM energimynd_one_day WHERE PointInTime='{}'"
sqlNofreezer = "SELECT sum(CorrectedEnergy) FROM energimynd_one_day WHERE PointInTime='{}' AND Notype != 2016"
sqlNoFloorHeating = "SELECT sum(CorrectedEnergy) FROM energimynd_one_day WHERE PointInTime='{}' AND Notype != 2236"
sqlNoBg = "SELECT sum(CorrectedEnergy) FROM energimynd_one_day WHERE PointInTime='{}' AND Notype != 2016 AND Notype != 2236"
sqlAvgLastHour = "SELECT avg(NULLIF(CorrectedEnergy,0)) FROM energimynd_one_day WHERE PointInTime BETWEEN '{0}' AND '{1}'"
sqlAvgLastHourWithoutBG = "SELECT avg(NULLIF(CorrectedEnergy,0)) FROM energimynd_one_day WHERE PointInTime BETWEEN '{0}' AND '{1}' AND Notype != 2016 AND Notype != 2236"

#Coffee machine 1    2050
#Computer site 1    2080
#FloorHeating 1    2236
#Freezer 1    2016
#Hi-fi 1    2099
#Microwave 1    2113
#Not Followed    2445