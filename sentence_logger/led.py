import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
from time import sleep # Import the sleep function from the time module
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
ACTIVE = True
def startWorkingBlink():
    global ACTIVE
    ACTIVE=True
    while ACTIVE: # Run forever
        GPIO.output(22, GPIO.HIGH) # Turn on
        sleep(.3) # Sleep for 1 second
        GPIO.output(22, GPIO.LOW) # Turn off
        sleep(.3) # Sleep for 1 second
def stopWorkingBlink():
    global ACTIVE
    ACTIVE =False