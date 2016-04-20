#!/usr/bin/python
"""
This file contains various commands used by the main liquid thermal shock test
GUI to move the stepper motors.

Written by: M. Payne
Last revised: 2016-02-19

"""

# import required modules
import piplates.MOTORplate as motor
from time import sleep


def motorsOff():
    """Stop and cut power to all motors"""

    motor.stepperSTOP(0, 'A')
    motor.stepperSTOP(0, 'B')
    motor.stepperOFF(0, 'A')
    motor.stepperOFF(0, 'B')


def moveMotor(direction, resolution, numSteps):
    """Move a rail in the specified direction for a given number of steps

    Keyword arguements:

    direction -- the direction of motion (up/down/right/left)
    resolution -- step resolution full/half/quarter micro/half micro (0/1/2/3)
    numSteps -- the integer number of steps
    """

    # set controller parameters according to chosen direction
    if direction == 'up':
        motorName = 'B'
        motorDirection = 'CCW'
    elif direction == 'down':
        motorName = 'B'
        motorDirection = 'CW'
    elif direction == 'right':
        motorName = 'A'
        motorDirection = 'CW'
    elif direction == 'left':
        motorName = 'A'
        motorDirection = 'CCW'
    else:
        print("Invalid move direction specified")
        return

    # initialize motor controller and issue move command
    motor.stepperCONFIG(0, motorName, motorDirection, resolution, 2000, 0)
    motor.stepperMOVE(0, motorName, numSteps)

    # pause for duration of motor move plus 1 second, then power off motor
    # The power off step is necessary to ensure that only 1 motor is powered
    # up at a given time. The controller cannot support enough power to move
    # one motor while maintaining holding torque on the other

    sleep(numSteps/2000 + 1)
    #motorsOff()
    print('returning from moveMotor function')
    return 1

def findHome(direction):
    """ Move the rails to the home position.  This uses the time.sleep()
        function and is therefore no good for use with the GUI front
        end
    """

    # set motor parameters according to selected direction
    if(direction == 'up'):
        motorName = 'B'
        motorDir = 'CCW'
        sensorVal = 11
    elif(direction == 'right'):
        motorName = 'A'
        motorDir = 'CW'
        sensorVal = 14
    else:
        #print("Invalid homing direction specified")
        return 0

    # configure controller and issue move command
    motor.stepperCONFIG(0, motorName, motorDir, 3, 2000, 0)
    motor.stepperJOG(0, motorName)

    # Polling loop to check for limit switch closure
    switchStatus = motor.getSENSORS(0)
    flag = 1
    while(flag):
        # pause 0.05 seconds, then get sensor status from controller
        sleep(0.05)
        switchStatus = motor.getSENSORS(0)

        # status ==  15 means no limit are switches closed, do nothing
        if(switchStatus == 15):
            pass

        # status 11 means the up limit switch is closed
        # status 14 means the right limit switch is closed
        # if the appropriate status is detected for the current motion access,
        # then stop the motor and jog back 1000 steps the other way (the
        # jogback prevents excessive wear and tear on the limit switches 
        # since they will not be activated on every normal test cycle iteration
        elif(switchStatus == sensorVal):
            motor.stepperSTOP(0, motorName)
            sleep(0.25)
            if(motorDir == 'CCW'):
                motorDir = 'CW'
            else:
                motorDir = 'CCW'

            motor.stepperCONFIG(0, motorName, motorDir, 3, 2000, 0)
            motor.stepperMOVE(0, motorName, 1000)
            sleep(1)
            motorsOff()
            flag = 0
            #print(direction.capitalize() + ' home position reached.')
            return 1

        # if any unexpected sensor status is detected, all motors will stop
        # and a value of 0 will be returned, which will allow the test program
        # to exit gracefully
        else:
            motorsOff()
            #print('Limit switch error. Cannot find home position.')
            #print('Motors shutting down')
            return 0


def jog_motor(direction):
    """Jog the selected direction"""

    if direction == 'up':
        motorName = 'B'
        motorDir = 'CCW'
    elif direction == 'down':
        motorName = 'B'
        motorDir = 'CW'
    elif direction == 'right':
        motorName = 'A'
        motorDir = 'CW'
    elif direction == 'left':
        motorName = 'A'
        motorDir = 'CCW'

    motor.stepperCONFIG(0, motorName, motorDir, 3, 2000, 0)
    motor.stepperJOG(0, motorName)


def check_switches():
    switch_status = motor.getSENSORS(0)
    if switch_status == 15:
        return 'none'
    elif switch_status == 11:
        return 'up'
    elif switch_status == 14:
        return 'right'
    else:
        return 'error'

