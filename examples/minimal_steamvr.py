# -*- coding: utf-8 -*-

# vexptoolbox: Vizard Toolbox for Behavioral Experiments
# Example Script: Minimal SteamVR scene and debug overlay


import viz
import vizfx
import steamvr

# Allow importing the toolbox from the default examples/ subfolder
sys.path.append('..')
import vexptoolbox as vx

# The debug overlay is not imported together with vexptoolbox by default
# since it requires SteamVR to be present, therefore we import it explicitly.
# When using vexptoolbox.Experiment, you can also enable it directly by 
# calling Experiment.addSteamVRDebugOverlay()
from vexptoolbox.steamvr_debug import SteamVRDebugOverlay

# Initialize Vizard
viz.setMultiSample(4)
viz.go()

# Initialize SteamVR using our convenience function
# this should find and display all connected controllers
hmd, controllers = vx.steamVREasySetup()

# Add a floor to our scene
scene = vizfx.addChild('ground.osgb')

# Initialize and enable the debug overlay (F12 to toggle)
debugger = SteamVRDebugOverlay(enable=True)

