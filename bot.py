import time
import thread
import threading
import atexit
import sys
import termios
import contextlib

import imutils
import RPi.GPIO as GPIO
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor

### User Parameters ###

MOTOR_X_REVERSED = False
MOTOR_Y_REVERSED = False

MAX_STEPS_X = 30
MAX_STEPS_Y = 15

RELAY_PIN = 22

#######################

@contextlib.contextmanager
def raw_mode(file):
    """
    Magic function that allows key presses.
    :param file:
    :return:
    """
    old_attrs = termios.tcgetattr(file.fileno())
    new_attrs = old_attrs[:]
    new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
    try:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
        yield
    finally:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)

class Turret(object):
    """
    Class used for turret control.
    """
    def __init__(self, friendly_mode=True):
        self.friendly_mode = friendly_mode

        # create a default object, no changes to I2C address or frequency
        self.mh = Adafruit_MotorHAT()
        atexit.register(self.__turn_off_motors)

        # Stepper motor 1
        self.sm_x = self.mh.getStepper(200, 1)      # 200 steps/rev, motor port #1
        self.sm_x.setSpeed(5)                       # 5 RPM
        self.current_x_steps = 0

        # Stepper motor 2
        self.sm_y = self.mh.getStepper(200, 2)      # 200 steps/rev, motor port #2
        self.sm_y.setSpeed(5)                       # 5 RPM
        self.current_y_steps = 0

        # Relay
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        GPIO.output(RELAY_PIN, GPIO.LOW)

    def interactive(self):
        """
        Starts an interactive session. Key presses determine movement.
        :return:
        """

        Turret.move_forward(self.sm_x, 1)
        Turret.move_forward(self.sm_y, 1)

        print 'Commands: Pivot with (a) and (d). Tilt with (w) and (s). Exit with (q)\n'
        with raw_mode(sys.stdin):
            try:
                while True:
                    ch = sys.stdin.read(1)
                    if not ch or ch == "q":
                        break

                    if ch == "w":
                        if MOTOR_Y_REVERSED:
                            Turret.move_forward(self.sm_y, 5)
                        else:
                            Turret.move_backward(self.sm_y, 5)
                    elif ch == "s":
                        if MOTOR_Y_REVERSED:
                            Turret.move_backward(self.sm_y, 5)
                        else:
                            Turret.move_forward(self.sm_y, 5)
                    elif ch == "a":
                        if MOTOR_X_REVERSED:
                            Turret.move_backward(self.sm_x, 5)
                        else:
                            Turret.move_forward(self.sm_x, 5)
                    elif ch == "d":
                        if MOTOR_X_REVERSED:
                            Turret.move_forward(self.sm_x, 5)
                        else:
                            Turret.move_backward(self.sm_x, 5)
                    elif ch == "\n":
                        Turret.fire()

            except (KeyboardInterrupt, EOFError):
                pass

    @staticmethod
    def fire():
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(RELAY_PIN, GPIO.LOW)

    @staticmethod
    def move_forward(motor, steps):
        """
        Moves the stepper motor forward the specified number of steps.
        :param motor:
        :param steps:
        :return:
        """
        motor.step(steps, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.INTERLEAVE)

    @staticmethod
    def move_backward(motor, steps):
        """
        Moves the stepper motor backward the specified number of steps
        :param motor:
        :param steps:
        :return:
        """
        motor.step(steps, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.INTERLEAVE)

    def __turn_off_motors(self):
        """
        Recommended for auto-disabling motors on shutdown!
        :return:
        """
        self.mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
        self.mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

if __name__ == "__main__":
    t = Turret(friendly_mode=False)

    user_input = raw_input("Choose an input mode: (1) Motion Detection - Disabled, (2) Interactive\n")
    if user_input == "2":
        if raw_input("Live video? (y, n)\n").lower() == "y":
            thread.start_new_thread(VideoUtils.live_video, ())
        t.interactive()
    else:
        print "Unknown input mode. Please choose (2)"