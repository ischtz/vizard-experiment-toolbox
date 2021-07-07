# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Example Script: Dwell time selection and fixation check
# 
# Press the space bar to toggle gaze cursor on and off,
# Press Q to quit the demo


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
viz.setMultiSample(4)
viz.go()

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

# Set up a simple scene
viz.addChild('ground_wood.osgb')
viz.MainView.getHeadLight().disable()
viz.addLight(euler=(30, 0, 0), color=viz.WHITE)
viz.addLight(euler=(-30, 0, 0), color=viz.WHITE)


def Main():

    # Run your eye tracker's default calibration method
    eyeTracker.calibrate()

    # Instantiate a recorder object to continuously sample gaze
    rec = vzgazetoolbox.SampleRecorder(eyeTracker, DEBUG=True)
        
    # Set up key callbacks to show/hide the gaze cursor and exit the demo
    vizact.onkeydown(' ', rec.showGazeCursor, viz.TOGGLE)
    vizact.onkeydown('q', viz.quit)

    # Fixation check: 
    # Wait until the user fixates the sphere before showing selection targets
    yield vzgazetoolbox.showVRText('Please look at the orange sphere to begin!', duration=1.5)
    fixation = vizshape.addSphere(radius=0.05, color=viz.YELLOW_ORANGE, pos=(0.0, 2.0, 4.0))
    
    yield rec.waitGazeNearTarget(fixation.getPosition())
    fixation.visible(False)
    yield viztask.waitTime(0.5)

    # Add some target cubes
    cubes = {'1': vizshape.addCube(size=1.0, color=viz.GRAY, pos=(-1.5, 0.5, 5.0), euler=(-30, 0, 0)),
             '2': vizshape.addCube(size=1.0, color=viz.GRAY, pos=(0.0, 0.5, 5.0)),
             '3': vizshape.addCube(size=1.0, color=viz.GRAY, pos=(1.5, 0.5, 5.0), euler=(-30, 0, 0))}

    # Dwell time selection:
    # Look at a cube for 1 s to select it
    rec.showGazeCursor(True)
    while True:
        object = yield rec.waitGazeSelectionFeedback(cubes, dwell=1.0, highlight_color=viz.BLUE, select_color=viz.BLUE)
        for cube in cubes.keys():
            if cubes[cube] == object:
                print('Selected cube #{:s}!'.format(cube))

viztask.schedule(Main)
