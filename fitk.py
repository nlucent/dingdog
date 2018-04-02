# Fatty in the kitchen
import os
import SimpleCV
from time import strftime, localtime

__threshold__ = 2.0
__version__ = "A22"			# Defaults
blob_minsize = 1000     	# 1000
min_blob_area = 4500    	# 4500
max_blob_area = 15000   	# 15000
max_hue_peak = 21       	# 15
min_hue_area = .019  		# 0.019
max_hue_area = .09 			# .09
min_cropped_size = (60,60) 	# (60,60)
max_pic_axis = 240
min_pic_axis = 60
circle_tolerance = .4
extension = ".jpg"
ref_image = SimpleCV.Image(os.path.abspath(os.path.dirname(__file__)) + "/pics/bare_floor.jpg")

class FattyInTheKitchen:

	def __init__(self, log):
		if log is None:
			import logging
			logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
			self.log = logging.getLogger(__name__)
		else:
			self.log = log

	def save(self, dogs, raw_dir, blob_dir):
		"""
			Saves images to raw_dir and blob_dir
		"""
		self.log.info("Dog detected!")
		filename = strftime("%H%M%S", localtime())

		# Save Image
		self.log.info("Saving " + filename + extension)
		dogs.image.save(raw_dir + filename + extension)

		# Save Blob Image
		img = dogs.image
		for dog in dogs:
			dog.drawOutline(color=SimpleCV.Color.RED, width=3)
			self.log.info("Saving dog " + filename + extension)
			img.crop(dog).save(blob_dir + filename + "C" + extension)
			img.save(blob_dir + filename + extension)

	def FindDogs(self, pic, countonly=False):
		"""
		Detects or counts dog like blobs

		Args:
			pic: (Precropped) Image to search

		Returns:
			List of blobs or count if countonly
		"""
		dogs = SimpleCV.FeatureSet()
		blobs = (ref_image - pic).findBlobs(minsize=blob_minsize)
		blobs.reverse()
		for b in blobs:
			fname = pic.filename
			b.image = pic
			crop = pic.crop(b)
			bimage = b.blobImage()
			peaks = bimage.huePeaks()
			
			if peaks is not None and len(peaks) > 1:
				peaks = peaks[0]

			# Check cropped blob image size is within reasonable bounds
			if crop.size() < min_cropped_size:
				self.log.debug (fname + ": Crop size too small - " + str(crop.size()))	            
				continue
			if crop.size() > (max_pic_axis, min_pic_axis) or crop.size() > (min_pic_axis, max_pic_axis):
				self.log.debug(fname + ": Crop size too big -  NOT IMPLEMENTED" + str(crop.size()))
				pass # Change log message once implemented

			# Check blob area is in bounds
			if b.area() < min_blob_area: 
				self.log.debug(fname + ": Blob area() too small -  " + str(b.area()))
				continue
			if b.area() > max_blob_area:
				self.log.debug(fname + ": Blob area() too big -  " + str(b.area()))
				continue

			# Check hue color and area is in bounds
			if peaks[0] > max_hue_peak:
				self.log.debug(fname + ": HuePeaks too high - " + str(peaks[0]))
				continue

			#import pdb; pdb.set_trace()			
			if peaks[1] < min_hue_area: # or peaks[0][1] > max_hue_area:
				self.log.debug(fname + ": Hue area too small - " + str(peaks[1]))
				continue

			if peaks[1] > max_hue_area:
				self.log.debug(fname + ": Hue area too large - " + str(peaks[1]))
				continue

			#print("Count:" + str(count) + " - " + "Cropped Size: " + str(crop.size()))
			#print("Cropped Size: " + str(crop.size()))
			#print("Circle: " + str(b.isCircle(tolerance=0.5)))
			#print("Hue: " + str(peaks[0][0]))
			#print("BlobArea: " + str(b.area()) + " BlobImage: " + str(peaks))
			dogs.append(b)

		# Add additional checking of the blobs here


		if countonly:
			return len(dogs) or 0
		return dogs or None

	def DrawDog(self, pic, color=SimpleCV.Color.RED, width=3):
		"""
		Draws dog blobs

		Args:
			Precropped pic
			SimpleCV.Color
			width

		Returns:
			Modified pic
		"""
		newpic = pic.copy()
		blobs = self.FindDogs(pic)
		if blobs:
			blobs.image = newpic
			for b in blobs:
				#b.image = newpic
				b.drawOutline(color=color, width=width)
				x,y = b.coordinates()
				b.image.drawText(str(b.area()), int(x), int(y), color=SimpleCV.Color.YELLOW, fontsize=30)
			return newpic
		else:
			return None

	def CropDog(self, pic):
		"""
		Crops dog blob from pic

		Args:
			Preformatted Image

		Returns:
			Cropped Image of blob
		"""
		dogs = []
		blobs = self.FindDogs(pic)
		for b in blobs:
			dogs.append(pic.crop(b))
		return dogs

	def FormatImage(self, pic):
		"""
		Formats SimpleCV image to exclude kitchen counters

		Args: Image to format

		Returns:
			Cropped and Warped image object
		"""
		# Crop image so we only see the floor
		cropped = pic.crop((210, 30, 260, pic.height))

		# Warp image so we dont see the counters anymore
		# warp assigns new points for existing image corners - (TL),(TR),(BR),(BL)
		remove_kitchen_counters = ((-90,0),(485,0),(cropped.width,cropped.height),(0,cropped.height))
		return cropped.warp(remove_kitchen_counters)

