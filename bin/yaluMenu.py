#!/usr/bin/python
 ##############################################################################
################################################################################
####            YetAnotherLevelUp (YALU), an FVWM Configuration             ####
####               ~ Jonathan Heathcote                                     ####
####               ~ September 2009 - Present                               ####
####               ~ GNU GPLv3                                              ####
################################################################################
 ##############################################################################
#
# yaluMenu:
#   Generates dynamic menus for YALU. Syntax:
#      yaluMenu [menu name]

import sys, os, commands, re
################################################################################
# Menu Object                                                                  #
#   Is used to construct the neccesary code to make an Fvwm menu.              #
################################################################################
class Menu:
	def __init__(self, name, dynamic=True, title=None):
		self.name = name
		
		# Clean-up the menu space for this menu
		self.__addCode("DestroyMenu Recreate \"%s\""%(self.name,))
		
		# If the menu is dynamic bind the FVWM event to regenerate this menu
		if dynamic:
			self.append("DynamicPopupAction", "YaluMenu menu %s"%(self.name,))
		
		# If a title has been specified, add one
		if title:
			self.append(title, "Title")
	
	def append(self, label, command, icon = None):
		"""Add a menu item to the menu."""
		if icon != None:
			icon = "%%%s%%"%(icon,)
		else:
			icon = ""
		
		self.__addCode("AddToMenu \"%s\" \"%s%s\" %s"%(
			self.name,
			icon,
			str(label).replace("\\","\\\\"),
			command
		))
	
	def appendRaw(self, rawData):
		"""Append some raw Fvwm code into the menu"""
		self.__addCode(rawData)
	
	def appendSpacer(self):
		"""Add a spacer to the menu (appears as a line)"""
		self.append("", "Nop")
	
	def appendProgram(self, label, command):
		"""
		Add a program to the menu:
		  Add a menu item with the specifed label and use the first word of the
		  command as the icon filename.
		"""
		self.append(label, "YaluExec %s"%(command,), command.partition(" ")[0])
	
	# The command executed by the selected option in a radio button list
	selectedOptionCommand = ""
	# The command executed by the default option in a radio button list
	defaultOptionCommand = ""
	# A flag which is tripped if a selection is made
	radioButtonSelected = False
	def appendRadio(self, label, command, customValue=False):
		"""
		Adds radio buttons. A value is deemed selected if its' command is equal
		to the selectedOption variable. If customValue is true and no previous radio
		buttons have been highlighted, highlight this option.
		"""
		
		# Choose an appropriate icon
		if command == self.selectedOptionCommand \
		   or (customValue and not self.radioButtonSelected):
			icon = "radioButtonSel"
			self.radioButtonSelected = True
		else:
			icon = "radioButtonNorm"
		
		# If the option is the default, label it so
		if command == self.defaultOptionCommand:
			label = "%s (Default)"%(label,)
		
		self.append(label, command, icon)
		
	# Generated menu code is stored here in the order it is generated.
	__fvwmCode = ""
	def __addCode(self, code):
		"""Add Fvwm code to the eventual output"""
		self.__fvwmCode += code + "\n"
	
	def __str__(self):
		return self.__fvwmCode

################################################################################
# Global Shortcut Generator Object                                             #
#   A Class which will bind shortcuts if possible but if a particular          #
#   combination has more than one command assigned to it then it will generate #
#   a menu to display when the shortcut is pressed.                            #
################################################################################
class GlobalShortcuts:
	def __init__(self, modifier = "4"):
		self.modifier = modifier
		
		# Dictionary of lists of (label, command) tuples to bind to keyboard
		# shortcuts.
		self.shortcuts = {}
		
		# A dictionary of stroke pattern strings: {pattern: command}
		self.strokes = {}
	
	def __getHotkeyPosition(self, label):
		"""
		Return the charachter index of the hotkey to use given a label
		  If a hotkey has been preceded by an ampersand use that, otherwise use the
		  first charachter (as in the menus used in YALU)
		"""
		hotkeyPosition = label.find("&") + 1
		if hotkeyPosition != 0 and hotkeyPosition < len(label):
			return hotkeyPosition
		else:
			return 0
	
	def append(self, label, command = None, stroke = None):
		"""The shortcut to be used is extracted from the label as in Fvwm"""
		
		# If no command is specified simply use the label specified with any
		# ampersands removed.
		if not command:
			command = label.replace("&","")
		
		# Add the stroke to the dictionary
		if stroke:
			self.strokes[stroke] = "YaluExec %s"%(command,)
		
		hotkey = label[self.__getHotkeyPosition(label)].lower()
		
		if hotkey in self.shortcuts:
			self.shortcuts[hotkey].append((label, command))
		else:
			self.shortcuts[hotkey] = [(label, command)]
	
	def bindKey(self, hotkey, action):
		"""Binds a key and graffiti style gesture to the given action"""
		return "Key %s A %s %s\n"%(
			hotkey,
			self.modifier,
			action
		)
	
	def __str__(self):
		"""Generate the appropriate bindings/menus"""
		returnString = ""
		for hotkey in self.shortcuts:
			if len(self.shortcuts[hotkey]) == 1:
				# Directly launch the program if no collisions
				returnString += self.bindKey(hotkey, "YaluExec " + self.shortcuts[hotkey][0][1])
			else:
				# Generate hotkey menu if there are collisions
				hotkeyMenu = Menu(
					"autoYaluMenu_hotkey_%s_and_%s"%(self.modifier, hotkey),
					False,
					"Hotkey '%s' choices"%(hotkey,)
				)
				for label, command in self.shortcuts[hotkey]:
					# Find the old hotkey position
					hotkeyPosition = self.__getHotkeyPosition(label)
					
					# Try to use the next charachter
					if hotkeyPosition == 0 and len(label) > 1:
						# If no absolute hotkey, use the next char (adding ampersand)
						labelWithNewHotkey = "%s&%s"%(label[0], label[1:])
					elif hotkeyPosition < len(label) - 1:
						# If absolute, remove old ampersand and add a new one
						labelWithNewHotkey = "%s%s&%s"%(
							label[:hotkeyPosition - 1], # Keep up-to the old &
							label[hotkeyPosition], # Old char (one before new)
							label[hotkeyPosition + 1:] # Hotkey + rest of label
						)
					else:
						# Fall-back -- use first letter
						labelWithNewHotkey = label.replace("&","")
					
					hotkeyMenu.appendProgram(labelWithNewHotkey, command)
				
				# Add the generated menu and the key binding for that key
				returnString += "%s\n"%(hotkeyMenu,)
				returnString += self.bindKey(hotkey,
				                             "Menu autoYaluMenu_hotkey_%s_and_%s"%(
				                              	self.modifier, hotkey))
		# Add all strokes
		for stroke in self.strokes:
			returnString += "Stroke %s 0 A 4 %s\n"%(stroke, self.strokes[stroke])
		return returnString

################################################################################
# Menu Generator Functions                                                     #
################################################################################
def generateLauncher():
	"""
	Main Launcher for YALU. Loads data from the 'menu' file.
	  Format:
	    * Entries seperated by lines
	    * Entries can contain an ampersand to indicate a hotkey
	    * Entries can be just a command
	    * Entries can be a label and command seperated by a tab
	    * Spaces can be added with a newline charachter
	"""
	launcher = Menu("launcher", True, "YetAnotherLevelUp")
	shortcuts = GlobalShortcuts()
	
	def appendWithShortcut(label, command, stroke):
		launcher.appendProgram(label, command)
		shortcuts.append(label, command, stroke)
	
	def extractStroke(label):
		# Find the stroke pattern (if there is one) and strip it out of the label
		match = re.match("([^{]*)[\s]?[{](\d+)[}]$", label)
		if match:
			label = match.group(1)
			return match.group(1,2)
		return label, None
	
	# Add 'fixed' menu items first
	appendWithShortcut("&Terminal", os.environ["yaluTerminal"], "456")
	appendWithShortcut("&Web Browser", os.environ["yaluBrowser"], "74123")
	appendWithShortcut("&Editor", os.environ["yaluEditor"], "14789")
	launcher.appendSpacer()
	
	# Load user's menu
	for rawMenuData in open("menu","r").read().split("\n"):
		if rawMenuData == "":
			# Blank line: add a seperator
			launcher.appendSpacer()
		elif rawMenuData.find("\t") != -1:
			# Tab-separated label and command
			label, _ , command = rawMenuData.partition("\t")
			label, stroke = extractStroke(label)
			appendWithShortcut(label, command, stroke)
		else:
			# Command/Label are the same -- just strip the ampersands for the cmd
			label = rawMenuData
			label, stroke = extractStroke(label)
			command = label.replace("&","")
			appendWithShortcut(label, command, stroke)
	
	# Add a quit button
	launcher.append("Quit", "Quit", "quit")
	
	# Add shortcut codes to the menu
	launcher.appendRaw(str(shortcuts))
	return launcher

def generateExecOutput():
	"""Create Exec Output viewer menu"""
	menu = Menu("execOutput", True, "View Command Output")
	
	# A list of screen sessions started by yalu
	sessions = []
	
	# Get a list of all screen sessions started by yalu
	for line in commands.getoutput("screen -ls").split("\n"):
		# Yalu screen sessions are in the format yalu_[id]_[firstWordOfCmd]
		regex = r"\s*\d+[.]yalu_(\d+_\S+)"
		match = re.match(regex, line)
		if match:
			sessions.append(match.group(1))
	
	# Sort by ID (launch ID order)
	sessions.sort()
	
	# Add each session to the menu
	for session in sessions:
		pid, _ , name = session.partition("_")
		menu.append(
			"%s (%s)"%(name, pid),
			"Exec exec $[yaluTerminal] -e \"screen -rx 'yalu_%s'\""%(session,),
			name
		)
	return menu

def generateExecHistory():
	"""Create a menu with recently/frequently used programs"""
	menu = Menu("execHistory")
	
	# Load the program history
	try:
		rawExecHistory = open("yaluExec_history", "r").read()
	except IOError:
		# File does not exist, assume it is blank
		rawExecHistory = ""
	
	# Strip out blank lines
	execHistory = []
	for line in rawExecHistory.split("\n"):
		if line.strip() != "":
			execHistory.append(line)
	
	if os.environ["yaluExecHistoryType"] == "recent":
		# Add appropriate title
		menu.append("Recently Used Commands","Title")
		
		# Strip out contiguous repeats
		recentExecHistory = []
		lastItem = ""
		for item in execHistory:
			if item != lastItem:
				recentExecHistory.append(item)
				lastItem = item
		
		# Add the most recent 15 items to the menu
		for program in recentExecHistory[:-16:-1]:
			menu.appendProgram(program, program)
	elif os.environ["yaluExecHistoryType"] == "frequent":
		# Add the title
		menu.append("Frequently Used Commands","Title")
		
		# Only look at the most recent 100 entries
		recentExecHistory = execHistory[:-101:-1]
		
		# Count occurences
		execFrequency = [
			(x, recentExecHistory.count(x)) for x in set(recentExecHistory)
		]
		
		# Sort by occurences
		frequentExecHistory = sorted(
			execFrequency,
			key=lambda x: x[1],
			reverse=True
		)
		
		# Add the top 15 to the menu
		for program, occurences in frequentExecHistory[:15]:
			menu.appendProgram(program, program)
	
	# Add the "clear" option
	menu.appendSpacer()
	menu.append("Clear History", "clearExecHistory", "clearHistory")
	
	return menu

def generateConfigMenu(config, title=None):
	menu = Menu("%sConfig"%(config.name,), True, title)
	
	def optionCommand(value):
		"""Returns the Fvwm command used to set the value given"""
		return "YaluConfig %s \"%s\""%(config.name, value)
	
	menu.defaultOptionCommand = optionCommand(config.default)
	menu.selectedOptionCommand = optionCommand(config.value)
	
	print "#" + menu.selectedOptionCommand
	
	for value in config.values:
		if value != None:
			if len(value) == 2:
				if value[1] != None:
					# A value with a different label
					menu.appendRadio(value[0], optionCommand(value[1]))
					print "#" + optionCommand(value[1])
				else:
					# A value which shares its value and label
					menu.appendRadio(value[0], optionCommand(value[0]))
			elif len(value) == 3:
				# A 'Custom' option
				menu.appendRadio(
					value[0],
					"YaluConfigGUI %s \"%s\""%(config.name, value[2]),
					True
				)
				
		else:
			menu.appendSpacer()
	return menu

################################################################################
# Dictionary and CLI interface                                                 #
#   A dictionary containing refrences to functions which generate menus and a  #
#   basic command line interface which will run the generator functions and    #
#   return the resulting menu code.                                            #
################################################################################

# A dictionary of functions which will return a Menu object. Each element is a
# tuple containing a refrence to a function and a list of arguments
yaluMenuFunctions = {
	"launcher" : (generateLauncher, []),
	"execOutput" : (generateExecOutput, []),
	"execHistory" : (generateExecHistory, []),
}

#Add menus for all the options from yaluConfig
import yaluConfig
for option in yaluConfig.yaluOptions:
	yaluMenuFunctions[option] = (
		generateConfigMenu,
		[yaluConfig.Option(option)]
	)

if __name__ == "__main__":
	# Move into the YALU dir so that all paths from now on can be relative
	os.chdir(os.environ["LocalYALU"])
	
	if len(sys.argv) == 2:
		# Print the menu item specified as the second argument
		function, args = yaluMenuFunctions[sys.argv[1]]
		print function(*args)
	else:
		# Print all menu items
		for menu in yaluMenuFunctions:
			function, args = yaluMenuFunctions[menu]
			print function(*args)
