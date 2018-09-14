'''
  Input and output using a SenseHat from the Apama correlator

  Copyright (c) 2018 John Heath

'''

from sense_hat import SenseHat, ACTION_RELEASED
from apama.eplplugin import EPLAction, EPLPluginBase, Correlator, Event
import time
import sys
from threading import Thread, Lock

#constants and globals

o = (0, 0, 0) # off
r = (255, 0, 0) # red
g = (0, 255, 0) # green 
b = (0, 0, 255) # blue


screen_mutex = Lock()

# wait cursor animation
waitcursor = [
    [[o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,g,g,o,o,o],
     [o,o,o,r,r,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o]],
    
    [[o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,r,g,o,o,o],
     [o,o,o,r,g,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o]],
    
    [[o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,r,r,o,o,o],
     [o,o,o,g,g,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o]],
    
    [[o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,g,r,o,o,o],
     [o,o,o,g,r,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o],
     [o,o,o,o,o,o,o,o]]
    
    ]

#Core Sense Hat elements including joystick call backs 
sense = SenseHat()

def doWaitCursor(repeat):
    screen_mutex.acquire()
    try:
        index = 0
        for index in range(repeat):
            sense.set_pixels(sum(waitcursor[index%4],[]))
            time.sleep(0.25)
    finally:
        screen_mutex.release()

def pushed_up(event):
    if event.action == ACTION_RELEASED:
        joyevt = Event(
            'Control', {"controlType": 1})
        Correlator.sendTo("monitor_messages", joyevt)

def pushed_down(event):
    if event.action == ACTION_RELEASED:
        joyevt = Event(
            'Control', {"controlType": 2})
        Correlator.sendTo("monitor_messages", joyevt)

def pushed_left(event):
    if event.action == ACTION_RELEASED:
        joyevt = Event(
            'Control', {"controlType": 3})
        Correlator.sendTo("monitor_messages", joyevt)

def pushed_right(event):
    if event.action == ACTION_RELEASED:
        joyevt = Event(
            'Control', {"controlType": 4})
        Correlator.sendTo("monitor_messages", joyevt)

def pushed_in(event):
    if event.action == ACTION_RELEASED:
        showTemp()
  

def showTemp():
    screen_mutex.acquire()
    try:
        sense.show_message(str(round(sense.temp,1)),0.05,b)
    finally:
        screen_mutex.release()
    
def showSystemStatus(plugin):
    screen_mutex.acquire()
    try:
        if plugin.systemStatus is True:
            sense.show_letter('1',g)
        else:
            sense.show_letter('0',r)

    finally:
        screen_mutex.release()

#event driven functions 
sense.stick.direction_up = pushed_up
sense.stick.direction_down = pushed_down
sense.stick.direction_left = pushed_left
sense.stick.direction_right = pushed_right
sense.stick.direction_middle = pushed_in


def poll(plugin, interval):
    while (True):
        try:
            doWaitCursor(8) #2 secs
            plugin.getLogger().info("TemperatureMonitor Thread triggers every " + str(interval) + " secs")
            evt = Event('Temperature', {"reading": sense.temp})
            Correlator.sendTo("monitor_messages", evt)
            showTemp()
            doWaitCursor(8) #2 secs
            showSystemStatus(plugin)

        except:
            plugin.getLogger().error(
                "Poll Thread Exception: %s", sys.exc_info()[1])

        time.sleep(interval)


class SenseHatTemperatureMonitorClass(EPLPluginBase):

    # Initialisation is simply a a case of reading in the config
    # and
    #
    def __init__(self, params):
        super(SenseHatTemperatureMonitorClass, self).__init__(params)
        self.systemStatus = False
        self.override = False
        self.monitorTemperature()
        self.getLogger().info("TemperatureMonitor initialised")

    @EPLAction("action<string>")
    def show_message(self, message):
        screen_mutex.acquire()
        try:
            sense.show_message(message)
        finally:
            screen_mutex.release()
    
    @EPLAction("action<boolean>")
    def setSystemStatus(self, status):
        self.systemStatus = status

    @EPLAction("action<boolean>")
    def setOverride(flag):
        self.override = flag

    # The lazy connection that triggers behaviour
    @EPLAction("action<> returns boolean")
    def monitorTemperature(self):
            try:
                self.thread = Thread(target=poll, args=(
                    self, 30), name='Apama Temperature polling thread')
                self.thread.start()
                self.getLogger().info("TemperatureMonitor Thread started")
                return True
            except:
                self.getLogger().error(
                    "Failed to start monitor polling thread : %s", sys.exc_info()[1])
                return False
