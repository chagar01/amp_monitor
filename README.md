# amp_monitor

script to run along side any audio program or distro, such as volumio,
that will toggle a GPIO to turn on an amplifier when music is playing.

Tested running alongside volumio https://volumio.org/

# script parameters

~~~
usage: amp_monitor.py [-h] [--monitor MONITOR] [--grepon GREPON]
                      [--grepoff GREPOFF] [--pollinterval POLLINTERVAL]
                      [--hysteresis HYSTERESIS] [--pin PIN] [--inverted]
                      [--log]

optional arguments:
  -h, --help            show this help message and exit
  --monitor MONITOR     specify which file to monitor to detect sound output
                        (default: /proc/asound/card1/pcm0p/sub0/status)
  --grepon GREPON       grep for string that should match when music is
                        playing (default: RUNNING)
  --grepoff GREPOFF     grep for string that should match when music is NOT
                        playing (default: closed)
  --pollinterval POLLINTERVAL
                        milliseconds between polling intervals (default: 2000)
  --hysteresis HYSTERESIS
                        number of polling intervals to wait before turning off
                        (default: 30)
  --pin PIN             gpio PIN to which relay for amp is connected (default:
                        16)
  --inverted            is GPIO inverted? (default: False)
  --log                 log output (default: False)
~~~

# How it works

The scripts periodically checks the contents of a file. The default
periodicity is 2s, and is controlled by the --pollinterval
parameter. If any line in the file matches the expression given by the
grepon parameter, the script assumes that that music is playing. If
the file contents match the expression given by the grepoff parameter,
it is assumed that music is not playing. When music starts playing the
script will switch the GPIO on. When music stops playing the script
will wait for a number of polling intervals before switching the GPIO
off. That number is controlled by the hysteresis parameter and
defaults to 30, which amounts to a minute with the default
pollinterval value of 2s. If music playback remains stopped during the
whole polling interval then the GPIO is switched off, otherwise it
reamains on.

# Example set up

I set this up on my raspberry pi zero w which is running volumio, and
has a relay conntected to GPIO16. The relay drivers my music
amplifier. The relay logic is inverted, or active_low, so setting the
GPIO pin value to 0 turns the amp on, and a value of 1 turns the amp
off. The raspberry PI has a phatDAC on it to drive audio.

The full command line for my setup would be:

~~~
$ ./amp_monitor.py --pin 16 --monitor /proc/asound/card1/pcm0p/sub0/status --grepon RUNNIG --grepoff closed --inverted 
~~~

Due to the defaults in the script, for my setup all I really need is
the --inverted parameter.

# Setting up as service with volumio

Here are steps to create a systemd service to run the script on startup

## Step 1

Create a systemd sevice description file, I called it
amp_monitor.service with the following content

~~~
[Unit]
Description=amp monitor to switch amp on depending on audio out
After=syslog.target

[Service]
Type=simple
User=volumio
Group=volumio
EnvironmentFile=/home/volumio/code/amp_monitor/amp_monitor.conf
ExecStart=/home/volumio/code/amp_monitor/amp_monitor.py $ARG1
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
~~~

Paths in EnvironmentFile and ExecStart will need adjusting based on
where you choose to store the script and the environment file. This
file allows you to set up parameters, in my case I needed to pass the
--inverted parameter, so my amp_monitor.conf just contains the following:

~~~
ARG1=--inverted
~~~

ARG1 is then used in the ExecStart commandline. There are probably
simpler ways...

## Step 2

Enable and start the service:

~~~
$ sudo cp amp_monitor.service /lib/systemd/system/.
$ sudo systemctl daemon-reload
$ sudo systemctl enable amp_monitor
$ sudo systemctl start amp_monitor
~~~

# Todo

* not a lot of testing has been done other than on my setup
* python2 based rather than 3, wouldn't take a lot to migrate, but
  default python on volumio was 2.7


