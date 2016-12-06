from picamera import PiCamera
from picamera.array import PiRGBArray

import pigpio
import DHT22
import time
import imutils
import cv2
import datetime

class BirdHouse:
    
    def __init__(self, config):
        self.config = config
        self.camera = PiCamera()
        self.camera.resolution = tuple(config['camera']['resolution'])
        self.camera.framerate = config['camera']['fps']
        self.pi = pigpio.pi()
        self.dht22 = DHT22.sensor(self.pi, config['dht22']['gpio'], None, power=config['dht22']['power'])
     
    def processWeather(self, humidity, temperature):
        print "Humdity {}%, Temperature {}F".format(humidity, temperature)
    
    def processMotion(self):
        return
      
    def run(self):
        rawCapture = PiRGBArray(self.camera, size=tuple(self.config['camera']["resolution"]))
        next_dht_reading = int(time.time())
        avg = None
        
        for f in self.camera.capture_continuous(rawCapture, format="bgr", use_video_port = True):
            frame = f.array
            timestamp = datetime.datetime.now()
            
            if int(time.time()) > next_dht_reading:
                self.dht22.trigger()
                next_dht_reading += 5
                
                if (self.dht22.humidity() > 0) and (self.dht22.temperature() > 0) and not self.dht22.bad_checksum():
                    self.processWeather(self.dht22.humidity(), self.dht22.temperatureF())
                
            frame = imutils.resize(frame, width = 500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if avg is None:
                avg = gray.copy().astype("float")
                rawCapture.truncate(0)
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
                self.processMotion()
                
            
            frame = imutils.rotate(frame, angle = self.config['camera']['rotate'])
            
            ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
            cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            
            if self.config['show_video']:
                cv2.imshow("Birdhouse Feed", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                
            rawCapture.truncate(0) 