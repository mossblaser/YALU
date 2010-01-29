#!/usr/bin/python
 ##############################################################################
################################################################################
####            YetAnotherLevelUp (YALU), an FVWM Configuration             ####
####               ~ Jonathan Heathcote                                     ####
####               ~ September 2009 - Present                               ####
####               ~ GNU GPLv3                                              ####
################################################################################
 ##############################################################################
# yaluInteliTile:
#   Inteligently maximise a window into the largest and most appropriate free
#   space. Usage:
#      yaluInteliTile init [screenWidth] [screenHeight]
#   For all windows on the screen:
#      yaluInteliTile add [yaluInteliTileID] [x] [y] [width] [height]
#   For the window you wish to move
#      yaluInteliTile place [yaluInteliTileID] [x] [y] [width] [height]

import sys, os, tempfile

################################################################################
# Secure a tempoary file in memory                                             #
################################################################################
def setInitialInteliTileID(screenWidth, screenHeight):
	# Get a tempoary file 
	fileObj, filename = tempfile.mkstemp(prefix="yaluInteliTile",dir="/dev/shm")
	open(filename, "w").write("%s %s\n"%(screenWidth, screenHeight))
	print "SetEnv yaluInteliTileID \"%s\""%(filename)

################################################################################
# Store a window's information in the tempoary file                            #
################################################################################
def storeWindowInfo(tempFile, *windowInfo):
	fileObj = open(tempFile, "a")
	fileObj.write(" ".join(windowInfo) + "\n")

################################################################################
# Find the optimal position for the window                                     #
################################################################################
def placeWindow(tempFile, targetX, targetY, targetWidth, targetHeight):
	fileObj = open(tempFile, "r")
	rawData = fileObj.read().strip().split("\n")
	
	# The top line of the file is the screen size
	screenWidth, screenHeight = rawData[0].split(" ")[:2]
	
	# For each line, extract the window x,y,width,height (split by spaces)
	windows = [
		((x,y),(w,h)) for x,y,w,h in [
			line.split(" ") for line in rawData[1:]
		]
	]
	
	# For debugging purposes: prints the found info
	sys.stderr.write(tempFile + "\n")
	sys.stderr.write(str(screenWidth) + " " + str(screenHeight) + "\n")
	sys.stderr.write(str(windows) + "\n")

################################################################################
# Commandline behaviour.                                                       #
################################################################################

if __name__ == "__main__":
	# Move into the YALU dir so that all paths from now on can be relative
	os.chdir(os.environ["LocalYALU"])
	
	if len(sys.argv) >= 2:
		if sys.argv[1] == "init" and len(sys.argv) == 4:
			setInitialInteliTileID(*sys.argv[2:])
		elif sys.argv[1] == "add" and len(sys.argv) == 7:
			storeWindowInfo(*sys.argv[2:])
		elif sys.argv[1] == "place" and len(sys.argv) == 7:
			placeWindow(*sys.argv[2:])
		else:
			sys.stderr.write("Wrong number of arguments\n")

