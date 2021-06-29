# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# VR helper functions

import os
import glob

import viz
import vizfx
import vizact
import viztask


class ObjectCollection(dict):
    """ Holds multiple node objects, similar to a Unity tag. 
    Each node can belong to more than one ObjectCollection. """
    def __init__(self, _src=None):
        self._o = {}
        if _src is not None:
            self._o = _src.copy()
        self._next_idx = 0


    def __getitem__(self, key):
        return self._o[key]


    def __setitem__(self, key, value):
        if not isinstance(value, viz.VizNode):
            raise TypeError('Can only assign Vizard node objects directly!')
        else:
            self._o[key] = value


    def __getattr__(self, name):
        return self._o[name]


    def __len__(self):
        return len(self._o)
    
    
    def __iter__(self):
        """ Iterates over all node objects in collection.
        
        This enables code like:
        for node in collection:
            print(node.getPosition())
        
        """
        return iter(self._o.values())


    def __contains__(self, node):
        """ Checks if a given node object is part of this collection. 
        This does NOT compare keys as would be the case for a dict! """
        if node in self._o.values():
            return True
        else:
            return False


    def __repr__(self):
        return repr(self._o)
    
    
    def add(self, node, key=None):
        """ Add a node object to the collection. If no key is specified, 
        the next available numeric key is used instead

        Args:
            node: Vizard node3d object """
        if key is None:
            # Find a free numerical key
            key = self._next_idx
            while key in self._o.keys():
                key += 1
            self._next_idx = key + 1
        self[key] = node


    def hideAll(self):
        """ Set all objects in this collection to invisible """
        for obj in self._o.keys():
            self._o[obj].visible(False)


    def showAll(self):
        """ Set all objects in this collection to visible """
        for obj in self._o.keys():
            self._o[obj].visible(True)


    def hide(self, key):
        """ Convenience function to set a single object invisible """
        self._O[key].visible(False)


    def show(self, key, position=None, euler=None, scale=None, color=None):
        """ Set a specific object from the collection to visible. Allows 
        quickly setting position, scale, euler orientation and/or color
        in the same call.

        Args:
            key (str): Key of the object to show
            position, euler, scale, color: optional inputs to Vizard
                "set<X>" functions, to modify and display an object at the same time
        """
        if position is not None:
            self._o[key].setPosition(position)
        if scale is not None:
            self._o[key].setScale(scale)
        if euler is not None:
            self._o[key].setEuler(euler)
        if color is not None:
            self._o[key].color(color)
        self._o[key].visible(True)


    def showOnly(self, key, position=None, euler=None, scale=None, color=None):
        """ Show only the specified object from the collection,
        hiding all other objects. Allows quickly setting position, 
        scale, euler orientation and/or color in the same call.

        Args:
            key (str): Key of the object to show
        position, euler, scale, color: optional inputs to Vizard
            "set<X>" functions, to modify and display an object at the same time
        """
        self.hideAll()
        self.show(key, position=position, euler=euler, scale=scale, color=color)


    @classmethod
    def fromFiles(cls, files):
        """ Create a new ObjectCollection by loading assets from
        a folder or list of file names. File base names will be used
        as keys in the collection.

        Args:
            files: path spec, e.g. 'objects/*.glb', or list of file names
        """
        obj = {}
        if type(files) == str:
            for of in glob.glob(files):
                key = os.path.splitext(os.path.split(of)[1])[0]
                obj[key] = vizfx.addChild(of)
                obj[key].visible(False)
        else:
            for of in files:
                try:
                    key = os.path.splitext(os.path.split(of)[1])[0]
                    obj[key] = vizfx.addChild(of)
                    obj[key].visible(False)
                except:
                    print('Error: could not load {:s}'.format(of))

        return ObjectCollection(_src=obj)



def showVRText(msg, color=[1.0, 1.0, 1.0], distance=2.0, scale=0.05, duration=3.0):
    """ Display head-locked message in VR, e.g. for instructions.
    
    Args:
        msg (str): Message text
        color: RBG 3-tuple of color values
        distance (float): Z rendering distance from MainView
        scale (float): Text node scaling factor
        duration (float): Message display duration (seconds)
    """
    # Create 3D text object
    text = viz.addText3D(msg, scale=[scale, scale, scale], color=color)
    text.resolution(1.0)
    text.setThickness(0.1)
    text.alignment(viz.ALIGN_CENTER)
    
    # Lock text to user viewpoint at fixed distance
    text_link = viz.link(viz.MainView, text, enabled=True)
    text_link.preTrans([0.0, 0.0, distance])
    
    # Fade text away after <duration> seconds
    fadeout = vizact.fadeTo(0, time=0.7)
    yield viztask.waitTime(duration)
    text.addAction(fadeout)
    yield viztask.waitActionEnd(text, fadeout)
    text.remove()


def waitVRText(msg, color=[1.0, 1.0, 1.0], distance=2.0, scale=0.05, keys=' ', controller=None):
    """ Display head-locked message in VR and wait for key press.
    
    Args:
        msg (str): Message text
        color: RBG 3-tuple of color values
        distance (float): Z rendering distance from MainView
        scale (float): Text node scaling factor
        keys (str): Key code(s) to dismiss message (see viztask.waitKeyDown)
        controller (sensor): Specify a controller sensor to also dismiss on button press
    
    Returns: Vizard keypress event
    """
    # Create 3D text object
    text = viz.addText3D(msg, scale=[scale, scale, scale], color=color)
    text.resolution(1.0)
    text.setThickness(0.1)
    text.alignment(viz.ALIGN_CENTER)
    
    # Lock text to user viewpoint at fixed distance
    text_link = viz.link(viz.MainView, text, enabled=True)
    text_link.preTrans([0.0, 0.0, distance])
    
    if controller is not None:
        event = yield viztask.waitAny([viztask.waitKeyDown(keys), viztask.waitSensorDown(controller, None)])
    else:
        event = yield viztask.waitKeyDown(keys)
    text.remove()
    viztask.returnValue(event)


def addRayPrimitive(origin, direction, length=100, color=viz.RED, 
                    alpha=0.6, linewidth=3, parent=None):
    """ Create a Vizard ray primitive from two vertices. Can be used
    to e.g. indicate a raycast or gaze vector in a VR environment.
    
    Args:
        origin (3-tuple): Ray origin
        direction (3-tuple): Unit direction vector
        length (float): Ray length (set to 1 and use direction=<end>
            to draw point-to-point ray)
        color (3-tuple): Ray color
        alpha (float): Ray alpha value
        linewidth (int): OpenGL line drawing width in pixels
        parent: Vizard node to use as parent
    """
    viz.startLayer(viz.LINES)
    viz.lineWidth(linewidth)
    viz.vertexColor(color)
    viz.vertex(origin)
    viz.vertex([x * length for x in direction])
    ray = viz.endLayer()
    ray.disable([viz.INTERSECTION, viz.SHADOW_CASTING])
    ray.alpha(alpha)
    if parent is not None:
        ray.setParent(parent)
    return ray
