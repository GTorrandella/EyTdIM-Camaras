# import the necessary packages
from imutils import build_montages
from datetime import datetime
import numpy as np
import imagezmq
import argparse
import imutils
import cv2
 
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-mW", "--montageW", required=True, type=int,
	help="montage frame width")
ap.add_argument("-mH", "--montageH", required=True, type=int,
	help="montage frame height")
args = vars(ap.parse_args())

# initialize the ImageHub object
imageHub = imagezmq.ImageHub(open_port='tcp://*:5555')

frameDict = {}

# initialize the dictionary which will contain  information regarding
# when a device was last active, then store the last time the check
# was made was now
lastActive = {}
lastActiveCheck = datetime.now()
 
# stores the estimated number of Pis, active checking period, and
# calculates the duration seconds to wait before making a check to
# see if a device was active
ESTIMATED_NUM_PIS = 4
ACTIVE_CHECK_PERIOD = 10
ACTIVE_CHECK_SECONDS = ESTIMATED_NUM_PIS * ACTIVE_CHECK_PERIOD

# assign montage width and height so we can view all incoming frames
# in a single "dashboard"
mW = args["montageW"]
mH = args["montageH"]

# defines the array for video storage and storage time
dictFramesToStorage = {}
storageTime = 60 # 10 min
lastStorage = datetime.now()
contadorFrameRecibidos = {}
# start looping over all the frames
while True:
	# receive RPi name and frame from the RPi and acknowledge
	# the receipt
	(clientName, frame) = imageHub.recv_image()
	imageHub.send_reply(b'OK')
	print(clientName)
 
	# if a device is not in the last active dictionary then it means
	# that its a newly connected device
	if clientName not in lastActive.keys():
		print("[INFO] receiving data from {}...".format(clientName))
		dictFramesToStorage[clientName] = []
		contadorFrameRecibidos[clientName] = 0
 
	# record the last active time for the device from which we just
	# received a frame
	lastActive[clientName] = datetime.now()

    # resize the frame to have a maximum width of 400 pixels, then
	# grab the frame dimensions and construct a blob
	frame = imutils.resize(frame, width=400)
	(h, w) = frame.shape[:2]
 
    # update the new frame in the frame dictionary
	frameDict[clientName] = frame
 
	# build a montage using images in the frame dictionary
	montages = build_montages(frameDict.values(), (w, h), (mW, mH))
 
	# display the montage(s) on the screen
	for (i, montage) in enumerate(montages):
		cv2.imshow("Home pet location monitor ({})".format(i),
			montage)
 
	# detect any kepresses
	key = cv2.waitKey(1) & 0xFF

	# if current time *minus* last time when the active device check
	# was made is greater than the threshold set then do a check
	if (datetime.now() - lastActiveCheck).seconds > ACTIVE_CHECK_SECONDS:
		# loop over all previously active devices
		for (clientName, ts) in list(lastActive.items()):
			# remove the RPi from the last active and frame
			# dictionaries if the device hasn't been active recently
			if (datetime.now() - ts).seconds > ACTIVE_CHECK_SECONDS:
				print("[INFO] lost connection to {}".format(clientName))
				lastActive.pop(clientName)
				frameDict.pop(clientName)

		# set the last active check time as current time
		lastActiveCheck = datetime.now()

	# if storageTime has passed sin the last storage, saves the video
	if(datetime.now() - lastStorage).seconds > storageTime:
		for key in dictFramesToStorage.keys():
			fps=max(contadorFrameRecibidos[key]/storageTime,15)
			print("Guardando Video de " + str(key))
			out = cv2.VideoWriter(str(key)+'-'+str(datetime.now())+'.avi', cv2.VideoWriter_fourcc('M','J','P','G'), fps, (w, h))
			for f in dictFramesToStorage[key]:
				out.write(f)
			out.release()
			print("Video de "+str(key)+"guardado")
			dictFramesToStorage[key] = []
			contadorFrameRecibidos[clientName] = 0
			lastStorage = datetime.now()
	else:
		dictFramesToStorage[clientName].append(frame)
		contadorFrameRecibidos[clientName] += 1

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

# do a bit of cleanup
cv2.destroyAllWindows()