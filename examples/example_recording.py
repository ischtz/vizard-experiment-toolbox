# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Example Script: Recording gaze data
# 
# Press the space bar to toggle gaze cursor on and off


import sys
import random 

import viz
import vizact
import viztask
import vizshape
import steamvr

# Allow importing the toolbox from the default examples/ subfolder
sys.path.append('..')
import vexptoolbox

# Initialize Vizard
viz.setMultiSample(8)
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

# Set up a simple scene containing a few random cubes
viz.addChild('ground_wood.osgb')
viz.MainView.getHeadLight().disable()
viz.addLight(euler=(30, 0, 0), color=viz.WHITE)
viz.addLight(euler=(-30, 0, 0), color=viz.WHITE)
for c in range(0, 15):
    size = random.random() * 1.0
    pos = [(random.random() - 0.5) * 10,
            float(size) / 2,
            (random.random() * 10) + 2.0]
    color = [random.random(), random.random(), random.random()]
    
    cube = vizshape.addCube(size=size)
    cube.setPosition(pos)
    cube.color(color)



def Main():

    # Run your eye tracker's default calibration method
    eyeTracker.calibrate()

    # Instantiate a sample recorder object that will record in the background
    rec = vexptoolbox.SampleRecorder(eyeTracker, DEBUG=True)
    
    # Set up a key callback to show/hide the gaze cursor in debug mode
    vizact.onkeydown(' ', rec.showGazeCursor, viz.TOGGLE)
    rec.showGazeCursor(True)
    
    # Record gaze data for 30 seconds
    yield rec.startRecording()
    yield viztask.waitTime(30)
    yield rec.stopRecording()
    
    # Save recorded gaze samples and events to CSV files
    yield rec.saveRecording('samples.csv', 'events.csv')

    viz.quit()


viztask.schedule(Main)
