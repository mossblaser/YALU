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
#   space, emulating some tiling WM behaviours. Usage:
#
#   Before using, initialise a tempoary file (and its address is stored as
#   yaluInteliTileID in the environment variables)
#       yaluInteliTile init [screenWidth] [screenHeight]
#
#   For each window which is not going to be moved run this:
#       yaluInteliTile add [yaluInteliTileID] [x] [y] [width] [height]
#
#   FEATURES:
#   To maximise a window into a free space
#       yaluInteliTile place [yaluInteliTileID] [x] [y] [width] [height]
#   To maximise a window into a free space but keeping existing width
#       yaluInteliTile tallPlace [yaluInteliTileID] [x] [y] [width] [height]
#   To maximise a window into a free space but keeping existing height
#       yaluInteliTile widePlace [yaluInteliTileID] [x] [y] [width] [height]
#
#   The space-finding algorithm used in this script was originally devised by
#   Tom Nixon and the implementation shown is loosely based on his refrence
#   implementation.

import sys, os, tempfile

################################################################################
# Secure a tempoary file in memory                                             #
################################################################################
def setInitialInteliTileID(screenWidth, screenHeight):
	# Get a tempoary file 
	fileObj, filename = tempfile.mkstemp(prefix="yaluInteliTile",dir="/dev/shm")
	
	# Add the width/height of the screen as the initial data
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

class Point:
	"""A minimal representation of a point in 2D"""
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
	def __add__(a, b):
		return Point(a.x + b.x, a.y + b.y)
	
	def __sub__(a, b):
		return Point(a.x - b.x, a.y - b.y)

class Rectangle:
	"""A minimal representation of a rectangle"""
	def __init__(self, topLeft, btmRight):
		self.topLeft = topLeft
		self.btmRight = btmRight
	
	# Edge positions
	@property
	def top(self):
		return self.topLeft.y
	@property
	def btm(self):
		return self.btmRight.y
	@property
	def left(self):
		return self.topLeft.x
	@property
	def right(self):
		return self.btmRight.x
	
	# Extra corners
	@property
	def topRight(self):
		return Point(self.right, self.top)
	@property
	def btmLeft(self):
		return Point(self.left, self.btm)
	
	# Size properties
	@property
	def width(self):
		return self.right - self.left
	@property
	def height(self):
		return self.btm - self.top
	@property
	def area(self):
		return self.width * self.height
	
	def intersects(self, other):
		return (other.left < self.right and
		        other.top < self.btm and
		        other.right > self.left and
		        other.btm > self.top)
	
	# Alow use of `rect1 in rect2'
	__contains__ = intersects
	
	def isValid(self):
		"""Check if this rectangle has physically possible dimensions"""
		return (self.left < self.right and
		        self.top < self.btm)
	
	def __str__(self):
		return "R(%ix%i+%i+%i)"%(self.width, self.height, self.left, self.top)
	__repr__ = __str__

def partitionSpace(space, window):
	"""
	Splits up a rectangle (space) such that the resulting collection of spaces
	does not cover the rectangle defined by window.
	"""
	partitionedSpace = []
	
	# Left
	partitionedSpace.append(Rectangle(space.topLeft,
	                                Point(window.left, space.btm)))
	# Top
	partitionedSpace.append(Rectangle(space.topLeft,
	                                Point(space.right, window.top)))
	# Right
	partitionedSpace.append(Rectangle(Point(window.right, space.top),
	                                space.btmRight))
	# Bottom
	partitionedSpace.append(Rectangle(Point(space.left, window.btm),
	                                space.btmRight))
	
	return filter(Rectangle.isValid, partitionedSpace)

def findSpaces(screen, windows):
	### Find spaces on screen ###
	# This algorithm was designed by Tom Nixon (and it is absolute genius). It
	# will find all empty rectangles of space inside a given area. In effect, the
	# algorithm is a process of elimination:
	#   1) Start by assuming the whole screen is empty
	#   2) For each window:
	#     a) For each assumed empty space, if it intersects with the window then
	#        cut the space up so that it does not include the place where that
	#        window occupies.
	#'    b) If it doesn't intersect, then this space should be left un-modified.
	#   3) That's basically it -- now you have a list of empty rectangles :)
	
	emptySpaces = [screen]
	for window in windows:
		# A list which will be filled with the new list of emptySpaces for this
		# iteration.
		updatedEmptySpaces = []
		for space in emptySpaces:
			if window not in space:
				updatedEmptySpaces.append(space)
			else:
				updatedEmptySpaces.extend(partitionSpace(space, window))
		emptySpaces = updatedEmptySpaces
	return emptySpaces

def loadScreenAndWindows(tempFile):
	### Extract information from tempoary file ###
	fileObj = open(tempFile, "r")
	rawData = fileObj.read().strip().split("\n")
	
	# The top line of the file is the screen size
	screen = Rectangle(Point(0,0),
	                   Point(*[int(x) for x in rawData[0].split(" ")[:2]]))
	
	# For each line, extract the window x,y,width,height (split by spaces) and
	# represent as a rectangle
	windows = [ Rectangle(Point(int(x), int(y)),
	                      Point(int(x)+int(w), int(y)+int(h)))
		for x,y,w,h in [line.split(" ") for line in rawData[1:]]
	]
	
	# Delete the file afterwards
	os.remove(tempFile)
	
	return screen, windows

def loadTarget(targetX, targetY, targetWidth, targetHeight):
	return Rectangle(Point(int(targetX), int(targetY)),
	                 Point(int(targetX) + int(targetWidth),
	                       int(targetY) + int(targetHeight)))

def setWindowSizeAndPosition(width, height, x, y):
	print "Maximize %ip %ip"%(width, height)
	print "ThisWindow (Maximized) Move %ip %ip"%(x, y)

def placeWindow(tempFile, *targetWindow):
	emptySpaces = findSpaces(*loadScreenAndWindows(tempFile))
	targetWindow = loadTarget(*targetWindow)
	
	largestSpace = max(emptySpaces, key=(lambda rect : rect.area))
	
	if largestSpace:
		setWindowSizeAndPosition(largestSpace.width, largestSpace.height,
		                         largestSpace.left, largestSpace.top)

def tallPlaceWindow(tempFile, *targetWindow):
	emptySpaces = findSpaces(*loadScreenAndWindows(tempFile))
	targetWindow = loadTarget(*targetWindow)
	
	# Remove any spaces that are too narrow
	emptySpaces = filter((lambda rect: rect.width >= targetWindow.width),
	                     emptySpaces)
	
	# Sort spaces from left-to-right (so that if there are any equally sized
	# maximum spaces then the left-most one will be chosen).
	emptySpaces = sorted(emptySpaces, key=(lambda rect : rect.left))
	
	largestSpace = max(emptySpaces, key=(lambda rect : rect.height))
	
	if largestSpace:
		setWindowSizeAndPosition(targetWindow.width, largestSpace.height,
		                         largestSpace.left, largestSpace.top)

def widePlaceWindow(tempFile, *targetWindow):
	emptySpaces = findSpaces(*loadScreenAndWindows(tempFile))
	targetWindow = loadTarget(*targetWindow)
	
	# Remove any spaces that are too narrow
	emptySpaces = filter((lambda rect: rect.height >= targetWindow.height),
	                     emptySpaces)
	
	# Sort spaces from top-to-bottom (so that if there are any equally sized
	# maximum spaces then the left-most one will be chosen).
	emptySpaces = sorted(emptySpaces, key=(lambda rect : rect.top))
	
	largestSpace = max(emptySpaces, key=(lambda rect : rect.width))
	
	if largestSpace:
		setWindowSizeAndPosition(largestSpace.width, targetWindow.height,
		                         largestSpace.left, largestSpace.top)


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
		elif sys.argv[1] == "tallPlace" and len(sys.argv) == 7:
			tallPlaceWindow(*sys.argv[2:])
		elif sys.argv[1] == "widePlace" and len(sys.argv) == 7:
			widePlaceWindow(*sys.argv[2:])
		else:
			sys.stderr.write("Wrong number of arguments\n")

