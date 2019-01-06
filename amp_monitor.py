#!/usr/bin/python -u

# MIT License

# Copyright (c) 2019 Charles Garcia-Tobin

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from time import sleep
import argparse
import re
import os

class AmpService:
    Off = 0                 # 0 sound not playing,
    On = 1                  # 1 sound playing,
    Hysteresis = 2          # 2 hysteresis (sound now playing but waitng until completes before swiching GPIO off)

    def  __init__(self):
        self.state = AmpService.Off
        self.hyst_count = 0

        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument("--monitor",
                            help = "specify which file to monitor to detect sound output",
                            default = "/proc/asound/card1/pcm0p/sub0/status")

        parser.add_argument("--grepon",
                            help = "grep for string that should match when music is playing",
                            default = "RUNNING")

        parser.add_argument("--grepoff",
                            help = "grep for string that should match when music is NOT playing",
                            default = "closed")
        
        parser.add_argument("--pollinterval",
                            help = "milliseconds between polling intervals", type = int, 
                            default = 2000)

        parser.add_argument("--hysteresis",
                            help = "number of polling intervals to wait before turning off", type = int, 
                            default = 30)

        parser.add_argument("--pin",
                            help = "gpio PIN to which relay for amp is connected", type = int, 
                            default = 16)

        parser.add_argument("--inverted",
                            help = "is GPIO inverted?", dest='inverted', action='store_true')

        parser.add_argument("--log",
                            help = "log output", dest='log', action='store_true')

        self.args = parser.parse_args()
        self.initGPIO()
        

    def dogrep(self,fname, expression):
        found = False
        fh = open(fname, "r")
        for line in fh:
            if re.search(expression, line):
                found = True
            break
        return found    

    def initGPIO(self):
        # check if GPIO file already exists
        dname = '/sys/class/gpio/gpio'+str(self.args.pin)

        if not os.path.exists(dname):
            os.system('echo '+str(self.args.pin)+' > /sys/class/gpio/export')
            sleep(1)

        # we should have GPIO now
        # set as inverted if needed
        if (self.args.inverted):
            os.system('echo 1 > /sys/class/gpio/gpio'+str(self.args.pin)+'/active_low')
        else:
            os.system('echo 0 > /sys/class/gpio/gpio'+str(self.args.pin)+'/active_low')

        # set as output
        os.system('echo \'out\' > /sys/class/gpio/gpio'+str(self.args.pin)+'/direction')

        # turn off
        os.system('echo 0 > /sys/class/gpio/gpio'+str(self.args.pin)+'/value')

     
    def switch(self,on):
        if self.args.log: print "Switching: ",on
        if on:
            # turn on
            os.system('echo 1 > /sys/class/gpio/gpio'+str(self.args.pin)+'/value')
        else:
            # turn off
            os.system('echo 0 > /sys/class/gpio/gpio'+str(self.args.pin)+'/value')


    def run(self):        
        while True:
            sleep(float(self.args.pollinterval)/1000.0)

            if self.state == AmpService.Off:
                # check if sound is now playing if so transition to state 1 (ON)
                if self.dogrep(self.args.monitor,self.args.grepon):
                    # sound is playing, traansition to ON
                    self.state = AmpService.On
                    self.switch(True) # swtch amp on
                    continue

            if self.state == AmpService.On:
                # check if sound has stopped playing, if so transition to state hysterisis state
                # with count of 0
                if self.dogrep(self.args.monitor,self.args.grepoff):
                    # sound has stopped playing
                    self.state = AmpService.Hysteresis
                    self.hyst_count = 0
                    continue

            if self.state == AmpService.Hysteresis:
                # check if sound is still not playing, if so increase hyst count, if that exceeds
                # threshold then turn GPIO off
                # if sound starts playing transition back to ON
                if self.dogrep(self.args.monitor,self.args.grepoff):
                    # sound has stopped playing
                    self.hyst_count += 1
                    if self.hyst_count > self.args.hysteresis:
                        self.state = AmpService.Off
                        self.switch(False) # swtch amp off

                elif self.dogrep(self.args.monitor,self.args.grepon):
                    self.state = AmpService.On
                    continue

            if self.args.log: print 'state:', self.state, 'hyst_count:', self.hyst_count    
            
        
if __name__ == '__main__':
    amp = AmpService()
    amp.run()
        
