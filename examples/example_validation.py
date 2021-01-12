# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Example Script: Validating eye tracker accuracy


import sys
import random 

import viz
import vizact
import viztask
import vizshape
import steamvr

# Allow importing the toolbox from the default examples/ subfolder
sys.path.append('..')
import vzgazetoolbox

# Initialize Vizard
viz.setMultiSample(8)
viz.go()
viz.addChild('ground_wood.osgb')

# Initialize SteamVR HMD
hmd = steamvr.HMD()
if not hmd.getSensor():
	sys.exit('SteamVR HMD not detected!')
navigationNode = viz.addGroup()
viewLink = viz.link(navigationNode, viz.MainView)
viewLink.preMultLinkable(hmd.getSensor())

# Initialize Vive Pro Eye tracker
# Change this to your eye tracker extension if you use a different one!
VivePro = viz.add('VivePro.dle')
eyeTracker = VivePro.addEyeTracker()
if not eyeTracker:
	sys.exit('Eye tracker not detected!')

# Define validation target positions
# Note that the toolbox comes with a variety of pre-built target sets, 
# see vzgazetoolbox/data.py for details. 
targets = [ [0.0,  0.0,  6.0],
			[5.0,  0.0,  6.0],
			[0.0,  -5.0, 6.0],
			[-5.0, 0.0,  6.0],
			[0.0, 5.0,   6.0],
			[5.0, 5.0,   6.0],
			[5.0,  -5.0, 6.0],
			[-5.0, -5.0, 6.0],
			[-5.0,  5.0, 6.0] ]

def Main():

	# Run your eye tracker's default calibration method
	eyeTracker.calibrate()

	# Instantiate a sample recorder object to handle validation
	rec = vzgazetoolbox.SampleRecorder(eyeTracker, DEBUG=True)

	# This will preview a set of gaze targets without validating,
	# press SPACE to continue
	yield rec.previewTargets(targets=targets)
	yield viztask.waitTime(3)
	
	# Now run the validation routine
	# Look at each target in turn until it turns green
	yield rec.validate(targets=targets)
	
	# Print validation result (also returned by validate() directly)
	result = rec.getLastValResult()
	print(result)
	
	# Access individual measures from result
	print('Global accuracy was {:.2f} degrees!'.format(result.acc))
	yield viztask.waitTime(3)
	
	# Save validation results to file for later analysis
	result.save(file_name='val_result.json', format='json')
	
	viz.quit()


viztask.schedule(Main)
