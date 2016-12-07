#!/usr/bin/env python

from Daemon import Daemon
from BirdHouse import BirdHouse
import json, sys, time, os

class BirdhouseDaemon(Daemon):
    def run(self):
        print "Starting Birdhouse Daemon"
        
        for cloc in os.curdir, os.path.expanduser('~'), '/etc/birdhouse/', os.environ.get('BIRDHOUSE_CONF'):
            if cloc is not None:
                try:
                    with open(os.path.join(cloc, "birdhouse.json")) as source:
                        config = json.load(source)
                        birdhouse = BirdHouse(config)
                        birdhouse.run()
                except IOError:
                    pass
            
        print "Could not locate birdhouse configuration file"

if __name__ == "__main__":
        
        sys.path.append('/usr/local/lib/python2.7/site-packages')
        
        daemon = BirdhouseDaemon('/var/run/birdhouse.pid')
        
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                    daemon.start()
                elif 'stop' == sys.argv[1]:
                    daemon.stop()
                elif 'restart' == sys.argv[1]:
                    daemon.restart()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)