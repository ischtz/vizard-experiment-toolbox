# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# VR helper functions

import viz
import vizact
import viztask

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


def waitVRText(msg, color=[1.0, 1.0, 1.0], distance=2.0, scale=0.05, keys=' '):
    """ Display head-locked message in VR and wait for key press.
    
    Args:
        msg (str): Message text
        color: RBG 3-tuple of color values
        distance (float): Z rendering distance from MainView
        scale (float): Text node scaling factor
        keys (str): Key code(s) to dismiss message (see viztask.waitKeyDown)
    
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
    
    event = yield viztask.waitKeyDown(keys)
    text.remove()
    viztask.returnValue(event)

