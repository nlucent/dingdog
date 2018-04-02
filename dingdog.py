#!/usr/bin/env python
# fitk.py
# Fatty in the kitchen

# v1
# Initial version
#
# v2
# Adding flask web interface, using image subtraction to detect blobs


from flask import Flask, jsonify, request
from time import sleep, localtime, strftime
import simplejson as json
import tempfile
import SimpleCV
import os, sys
import logging
import fitk
import savedogs

raw_base = "/home/pi/nas/kitchen/images/orig/"
blob_base = "/home/pi/nas/kitchen/images/blobs/"
doorbell = os.path.abspath(os.path.dirname(__file__)) + "doorbell.mp3"
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

def RestartApp():
	"""
	Restarts app without performing any cleanup actions

	Returns:
		Nothing
	"""

	python = sys.executable
	os.execl(python, python, * sys.argv)

def main():
	
	global raw_base, blob_base

	f = fitk.FattyInTheKitchen(log)

	threshold = fitk.__threshold__
	log.info("Running with FITK v" + fitk.__version__)
	log.info("Using movement threshold " + str(threshold))

	log.info("Intializing Camera ...")

	# Load Camera
	cam = SimpleCV.Camera()

	log.info("Starting Streaming Server")
	web = SimpleCV.JpegStreamer(hostandport="192.168.1.128:8080")
	cam.getImage().save(web)
	
	log.info("Entering video loop")

	while True:
		try:
			# Check timestamp of fitk module
			oldfitk = os.stat("fitk.py").st_mtime
			# FormatImage so we only compare area of interest
			prev = f.FormatImage(cam.getImage())
			sleep(0.1)
			curr = f.FormatImage(cam.getImage())

			# Subtract images for difference
			diff = curr - prev
			matrix = diff.getNumpy()
			mean = matrix.mean()

			if mean >= threshold:
				cur_date_dir = strftime("%m%d%Y", localtime()) + "/"
				
				raw_dir = raw_base + cur_date_dir
				blob_dir = blob_base + cur_date_dir

				if not os.path.exists(raw_dir):
					os.mkdir(raw_dir)
				if not os.path.exists(blob_dir):
					os.mkdir(blob_dir)

				dogs = f.FindDogs(curr)
				if dogs:
					dogs.image = curr
					f.save(dogs, blob_dir, raw_dir)
				curr.save(web)

			# check filetime and reload fitk module if it changes
			newfitk = os.stat("fitk.py").st_mtime

			if newfitk > oldfitk:
				log.info("File change detected, Reloading fitk module")
				try:
					reload(fitk)
					f = fitk.FattyInTheKitchen(log)
					threshold = fitk.__threshold__
					log.info("Using FITK module version " + fitk.__version__)
					log.info("Using threshold level " + str(threshold))
				except:
					log.debug("Error reloading FITK module")
		except KeyboardInterrupt:
			break

if __name__ == '__main__':
	main()
