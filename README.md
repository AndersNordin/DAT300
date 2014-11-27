Home Automation System with Least Slack First Algorithm.
======
This project is a part of the course ICT Support for Adaptiveness and (Cyber)security in the Smart Grid(DAT300) at Chalmers University of Technology.

### Prerequisite ###
1. You need Plugwise hardware for the whole simulation to work. 

2. (LINUX USERS ONLY) Change permission on the port you have connected the USB stick for it to communicate on the serial bus. 

3. Third-party Library is required, it is included in this repository. Can also be found here: https://bitbucket.org/hadara/python-plugwise/wiki/Home

### Description ###
This is a small scale project for home automation of devices. The idea is based on the paper by Barker et al SmartCap: Flattening Peak Electricity Demand in Smart Homes. 

The project runs in Python together with off-the-shelf system called Plugwise. We have used test data in a SQLite database format from a unknown household in Sweden. The database is included.

The project is built for demonstrating the concept and does not scale that easily. Feel free to fork and improve it! :)
