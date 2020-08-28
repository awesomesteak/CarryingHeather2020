# import curses
from gpiozero import Motor, Servo
from time import sleep
xMotor = Motor(forward=7, backward=0)
# yMotor = Motor(forward=2, backward=3)
# triggerServo = Servo(1)

while True:
  xMotor.forward()
  sleep(5)
  xMotor.backward()
  sleep(5)