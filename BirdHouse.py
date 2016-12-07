from picamera import PiCamera
from picamera.array import PiRGBArray

import pigpio
import DHT22
import time
import imutils
import cv2
import datetime
import sqlite3
import cronex
import logging

class BirdHouse:
    
    def __init__(self, config):
        self.config = config
        self.camera = PiCamera()
        self.camera.resolution = tuple(config['camera']['resolution'])
        self.camera.framerate = config['camera']['fps']
        self.pi = pigpio.pi()
        self.dht22 = DHT22.sensor(self.pi, config['dht22']['gpio'], None, power=config['dht22']['power'])
        self.sqlite = sqlite3.connect(config['sqlite_db'], 
                                      detect_types = sqlite3.PARSE_DECLTYPES,
                                      isolation_level = None)
        
        logging_level = getattr(logging, self.config['loglevel'].upper(), None)
        
        if not isinstance(logging_level, int):
            raise ValueError('Invalid Log Level: %s' % self.config['loglevel'])
        
        logging.basicConfig(level = logging_level, 
                            filename = self.config['logfile'],
                            format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        logging.info("Initializing Birdhouse")
        
        c = self.sqlite.cursor()
        
        logging.debug("Creating Tables to store birdhouse data if they don't previously exist")
        
        c.execute('''CREATE TABLE IF NOT EXISTS outlets (outlet_id INT, name TEXT, schedule TEXT, override_until timestamp, last_ran timestamp, initial_state INT, schedule_active INT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS weather (recorded_at timestamp, humidity REAL, temperature REAL)''')
        c.execute('PRAGMA journal_mode=WAL')
        
    def processWeather(self, humidity, temperature):
        c = self.sqlite.cursor()
        previousHistoryCut = datetime.datetime.now() - datetime.timedelta(days = self.config['dht22']['history_days'])
        
        logging.debug("Deleting historic weather data older than %s" % previousHistoryCut)
        
        c.execute("DELETE FROM weather WHERE recorded_at <= :history_cutoff", { 'history_cutoff' : previousHistoryCut })
        c.execute("INSERT INTO weather VALUES(?, ?, ?)", (datetime.datetime.now(), humidity, temperature))
    
    def processMotion(self):
        override_until = datetime.datetime.now() + datetime.timedelta(minutes = self.config['motion_timeout'])
        
        c = self.sqlite.cursor()
        c.execute('UPDATE outlets set override_until = :override_until', {'override_until' : override_until})
        results = c.execute('SELECT * FROM outlets')
        
        logging.debug("Motion Detected, overriding outlets to ON state until %s" % override_until)
        
        for outlet in results:
            self.pi.write(outlet[0], 1)
    
    def processSchedule(self):
        c = self.sqlite.cursor()
        results = c.execute('SELECT * FROM outlets')
        
        if c.rowcount ==  0:
            logging.warning("No outlets defined in database. Please define outlets!")
            
        for outlet in results:
            
            if not outlet[6]:
                logging.debug("Ignoring outlet %d becuse schedule is disabled" % outlet[0])
                continue
            
            # Scheduling hints: https://github.com/ericpruitt/cronex
            job = cronex.CronExpression(outlet[2].encode('ascii', 'ignore'))
            
            logging.debug("Applying schedule '%s' to outlet %d (now: %s)" % (outlet[2], outlet[0], datetime.datetime.now()))
            
            if job.check_trigger(time.localtime(time.time())[:5]):
            
                logging.debug("Cron job for outlet %d triggered" % outlet[0])
                    
                c2 = self.sqlite.cursor()
                c2.execute("SELECT * FROM outlets WHERE outlet_id = :outlet_id LIMIT 1", {'outlet_id' : outlet[0]})
                    
                currentOutlet = c2.fetchone()

                if currentOutlet[3] is not None:
                    if currentOutlet[3] > datetime.datetime.now():
                        logging.debug("Override for outlet %d enabled" % outlet[0])
                        continue
                
                if currentOutlet[4] is None:
                    logging.debug("Last ran not provided for outlet %d" % outlet[0])
                    secondsSinceExecution = 61
                else:
                    secondsSinceExecution = (datetime.datetime.now() - currentOutlet[4]).total_seconds()
                    logging.debug("Outlet %d was last ran %s" % (outlet[0], secondsSinceExecution))
                
                if secondsSinceExecution > 60:
                    
                    logging.debug("Updating outlet %d last run time to %s" % (outlet[0], datetime.datetime.now()))
                    
                    c2.execute("UPDATE outlets SET last_ran = ? WHERE outlet_id = ?", (datetime.datetime.now(), outlet[0]))
                    
                    if self.pi.read(outlet[0]):
                        logging.info("Outlet %i between switched to OFF per schedule %s" % (outlet[0], outlet[2].encode('ascii', 'ignore')))
                        self.pi.write(outlet[0], 0)
                    else:
                        logging.info("Outlet %i between switched to ON per schedule %s" % (outlet[0], outlet[2].encode('ascii', 'ignore')))
                        self.pi.write(outlet[0], 1)
                        
    
    def run(self):
        rawCapture = PiRGBArray(self.camera, size=tuple(self.config['camera']["resolution"]))
        next_dht_reading = int(time.time())
        avg = None
        
        logging.info("Setting initial schedule state")
        
        c = self.sqlite.cursor()
        
        outlets = c.execute("SELECT * FROM outlets")
        
        for outlet in outlets:
            if outlet[6]:
                logging.debug("Initializing Outlet %d to %d" % (outlet[0], outlet[5]))
                self.pi.write(outlet[0], outlet[5])
            else:
                logging.debug("Skipping Initialization of Outlet %d - inactive schedule" % outlet[0])
                self.pi.write(outlet[0], outlet[5])
        
        logging.info("Initializing Motion Capture")
        
        for f in self.camera.capture_continuous(rawCapture, format="bgr", use_video_port = True):
            frame = f.array
            timestamp = datetime.datetime.now()
            
            if int(time.time()) > next_dht_reading:
                self.dht22.trigger()
                next_dht_reading += 5
                
                if (self.dht22.humidity() > 0) and (self.dht22.temperature() > 0) and not self.dht22.bad_checksum():
                    self.processWeather(self.dht22.humidity(), self.dht22.temperatureF())
                else:
                    logging.warning("Failed to capture weather data!")
                    
            frame = imutils.resize(frame, width = 500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if avg is None:
                avg = gray.copy().astype("float")
                rawCapture.truncate(0)
                logging.info("No average background data available, creating from scratch based on current background")
                continue
            
            cv2.accumulateWeighted(gray, avg, 0.5)
            
            frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
            
            threshold = cv2.threshold(frameDelta, self.config['camera']['threshold'], 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations = 2)
            (_, cnts, _) = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for c in cnts:
                if cv2.contourArea(c) < self.config['camera']['min_area']:
                    continue
                
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
                logging.info("Motion detected")
                self.processMotion()
                
            
            frame = imutils.rotate(frame, angle = self.config['camera']['rotate'])
            
            ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
            cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            
            if self.config['show_video']:
                cv2.imshow("Birdhouse Feed", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
            
            self.processSchedule()
            
            rawCapture.truncate(0)
             
