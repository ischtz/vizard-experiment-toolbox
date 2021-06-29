# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# 3D Eyeball model class

import os
import viz
import vizshape

from .vrutil import addRayPrimitive

_module_path = os.path.split(os.path.abspath(__file__))[0]

class Eyeball(viz.VizNode):
    """ Simple eyeball object to visually indicate gaze direction """
    
    def __init__(self, radius=0.024, eyecolor='blue', pointer=False, gaze_length=1000, visible=True):
        """ Initialize a new Eyeball node
        
        Args:
            radius (float): Eyeball radius in m
            eyecolor (str, 3-tuple): Iris color for this eye (see setEyeColor)
            pointer (bool): if True, start out the gaze pointer visible
            gaze_length (float): length of gaze pointer in m
            visible (bool): if False, Eyeball node starts out invisible
        """

        self.eyecolors = {'brown': [0.387, 0.305, 0.203],
                          'blue':  [0.179, 0.324, 0.433],
                          'green': [0.109, 0.469, 0.277],
                          'grey':  [0.285, 0.461, 0.395]}
        
        eye = viz.addChild(os.path.join(_module_path, 'models', 'unit_eye.gltf'))
        eye.visible(visible)
        viz.VizNode.__init__(self, eye.id)
        
        # Add gaze direction pointer (invisible by default)
        self.pointer = addRayPrimitive(origin=[0,0,0], direction=[0,0,1], length=gaze_length, parent=eye, linewidth=5, alpha=0.8)
        if not pointer:
            self.pointer.visible(viz.OFF)

        # Set a specific eye color (e.g. for disambiguation)
        eye.setScale([radius / 2.0,] * 3)
        self.setEyeColor(eyecolor)
        
        
    def setEyeColor(self, color):
        """ Set iris color of this eyeball object
        
        Args:
            color : RGB 3-tuple, or one of 'brown', 'blue', 'green', 'grey'
        """
        if type(color) == str:
            ec = self.eyecolors[color]
        else:
            ec = color

        self.getChild('Iris').color(ec)
        self.pointer.color(ec)


    def setGazePointer(self, visible=True):
        """ Show or hide the gaze pointer on the eye's Z axis
        
        Args:
            visible (bool): if True, draw gaze direction pointer
        """
        self.pointer.visible(visible)

