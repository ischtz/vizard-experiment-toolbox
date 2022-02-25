# -*- coding: utf-8 -*-

# vexptoolbox: Vizard Toolbox for Behavioral Experiments
# SteamVR debug overlay class
# 
# Standalone version available at:
# https://github.com/ischtz/vizard-steamvr-debug


import os
import sys 
import csv
import random
import colorsys

import viz
import vizfx
import vizact
import vizinfo
import viztask
import vizshape

import steamvr

from .vrutil import addRayPrimitive, showVRText

DEBUGGER_SHOW_EVENT = viz.getEventID('SteamVRDebugOverlayShowEvent')
DEBUGGER_HIDE_EVENT = viz.getEventID('SteamVRDebugOverlayHideEvent')


class SteamVRDebugOverlay(object):

    def __init__(self, enable=False, hotkey=viz.KEY_F12):
        
        self._enable = enable
        self._hotkey = hotkey
        self._next_screenshot = 1
        self._points = []
        
        # Visualization parameters
        self.GRID_COLOR = [1, 1, 1]
        self.DEBUG_ALPHA = 0.6
        self.LABEL_SCALE = 0.05
        self.VALUE_SCALE = 0.015
        self.MARKER_SIZE = 0.05
        self.HUD_POS = [0.4, 0.3, 1] # Works for Vive / Vive Pro

        # SteamVR devices
        self.hmd = {}
        self.controllers = {}
        self.trackers = {}
        self.lighthouses = {}
        self.nodes = {}

        # Set up scene objects
        self._root = viz.addGroup()
        self._obj = []
        self._obj.append(vizshape.addGrid((100, 100), color=self.GRID_COLOR, pos=[0.0, 0.001, 0.0], parent=self._root))
        self._obj.append(vizshape.addAxes(pos=(0,0,0), scale=(0.5, 0.5, 0.5), parent=self._root))
        
        # Set up possible marker objects
        self._markers = {'sphere_red': vizshape.addSphere(radius=self.MARKER_SIZE / 2, color=viz.RED, parent=self._root),
                         'sphere_green': vizshape.addSphere(radius=self.MARKER_SIZE / 2, color=viz.GREEN, parent=self._root),
                         'sphere_blue': vizshape.addSphere(radius=self.MARKER_SIZE / 2, color=viz.BLUE, parent=self._root),
                         'sphere_yellow': vizshape.addSphere(radius=self.MARKER_SIZE / 2, color=viz.YELLOW, parent=self._root),
                         'cube_red': vizshape.addCube(size=self.MARKER_SIZE, color=viz.RED, parent=self._root),
                         'cube_green': vizshape.addCube(size=self.MARKER_SIZE, color=viz.GREEN, parent=self._root),
                         'cube_blue': vizshape.addCube(size=self.MARKER_SIZE, color=viz.BLUE, parent=self._root),
                         'cube_yellow': vizshape.addCube(size=self.MARKER_SIZE, color=viz.YELLOW, parent=self._root)
        }
        for marker in self._markers.keys():
            self._markers[marker].visible(False)

        # Note: X/Z axis rays moved up (y) by 1 mm to avoid z-fighting with the ground plane
        self._obj.append(addRayPrimitive(origin=[0,0.001,0], direction=[1, 0.001, 0], color=viz.RED, parent=self._root))   # x
        self._obj.append(addRayPrimitive(origin=[0,0.001,0], direction=[0, 0.001, 1], color=viz.BLUE, parent=self._root))  # z
        self._obj.append(addRayPrimitive(origin=[0,0,0], direction=[0, 1, 0], color=viz.GREEN, parent=self._root)) # y
        
        # Set up UI
        txt = 'Hotkeys:\nS - Save collected points data\nC - Clear point data\nL - Toggle Lighthouse rays\nX - Export debug scene\n\n'
        txt += 'Controller Buttons:\nTrigger - place point axes\nA - Save point data\nB - Take screenshot'
        self._ui = vizinfo.InfoPanel(txt, icon=True, align=viz.ALIGN_RIGHT_TOP, title='SteamVR Debug Tool')
        self._ui.renderToEye(viz.RIGHT_EYE)
        self._ui.addSeparator()
        self._obj.append(self._ui)

        # Register key callbacks
        self._callbacks = []
        self._callbacks.append(vizact.onkeydown('s', self.savePoints))
        self._callbacks.append(vizact.onkeydown('c', self.clearPoints))
        self._callbacks.append(vizact.onkeydown('l', self.showLighthouseRays, viz.TOGGLE))
        self._callbacks.append(vizact.onkeydown('x', self.saveDebugScene))

        self.findDevices()
        self.enable(self._enable)
        self._hotkey_callback = vizact.onkeydown(self._hotkey, self.enable, viz.TOGGLE)
        self._ui_callback = vizact.onupdate(viz.PRIORITY_LINKS+1, self._updateUI)
        print('* SteamVR Debug Overlay initialized.')


    def findDevices(self):
        """ Enumerate SteamVR devices and set up models """

        # HMD
        hmd = steamvr.HMD()
        self.hmd['sensor'] = hmd.getSensor()

        hmd_ui = viz.addText('N/A')
        self._ui.addItem(viz.addText('Headset'))        
        self._ui.addLabelItem('0', hmd_ui)
        self._ui.addSeparator()
        self.hmd['ui'] = hmd_ui

        hud = viz.addText3D('X: 0.00 (123.0°)', scale=(self.VALUE_SCALE * 2.5,) * 3, color=viz.GRAY)
        hud_link = viz.link(viz.MainView, hud)
        hud_link.preTrans(self.HUD_POS, viz.REL_LOCAL)
        self.hmd['hud'] = hud
        self._obj.append(hud)

        # Lighthouses
        for lidx, lighthouse in enumerate(steamvr.getCameraList()):
            lighthouse.model = lighthouse.addModel(parent=self._root)
            if not lighthouse.model:
                lighthouse.model = viz.addGroup()
            lighthouse.model.setCompositeAlpha(self.DEBUG_ALPHA)
            lighthouse.model.disable(viz.INTERSECTION)
            viz.link(lighthouse, lighthouse.model)
            
            l_text = viz.addText3D(str(lidx), scale=(self.LABEL_SCALE,) * 3, color=viz.YELLOW,
                                parent=lighthouse.model, pos=(0.1, 0, 0))
            l_text.setEuler(180, 0, 0)
            
            # Lighthouse normal vector
            l_normal = addRayPrimitive(origin=[0,0,0], direction=[0,0,1], color=viz.YELLOW, parent=lighthouse.model)
            l_normal.visible(False)

            self.lighthouses[lidx] = {'model': lighthouse.model,
                                      'normal': l_normal,
                                      'text': l_text}
            self._obj.append(lighthouse.model)
            print('* Found Lighthouse: {:d}'.format(lidx))

        # Controllers
        if steamvr.getControllerList():
            self._ui.addItem(viz.addText('Controllers'))

            for cidx, controller in enumerate(steamvr.getControllerList()):
                
                controller.model = controller.addModel(parent=self._root)
                if not controller.model:
                    controller.model = viz.addGroup(parent=self._root)
                controller.model.setCompositeAlpha(self.DEBUG_ALPHA)
                controller.model.disable(viz.INTERSECTION)
                viz.link(controller, controller.model)
                
                c_axes = vizshape.addAxes(scale=(0.1, 0.1, 0.1))
                viz.link(controller, c_axes)

                markers = {'axes': c_axes}
                for m in self._markers:
                    markers[m] = self._markers[m].copy()
                    markers[m].visible(False)
                    viz.link(controller, markers[m])

                c_text = viz.addText3D(str(cidx), scale=(self.LABEL_SCALE,) * 3, 
                                    parent=controller.model, pos=(-0.05, 0, 0))
                val_x = viz.addText3D('X: 0.00 (123.0°)', scale=(self.VALUE_SCALE,) * 3, 
                                    parent=controller.model, pos=(-0.18, 0.04, 0), color=viz.RED)
                val_y = viz.addText3D('Y: 0.00 (123.0°)', scale=(self.VALUE_SCALE,) * 3, 
                                    parent=controller.model, pos=(-0.18, 0.02, 0), color=viz.GREEN)
                val_z = viz.addText3D('Z: 0.00 (123.0°)', scale=(self.VALUE_SCALE,) * 3, 
                                    parent=controller.model, pos=(-0.18, 0, 0), color=viz.BLUE)
                
                self.controllers[cidx] = {'model': controller.model,
                                          'axes': c_axes,
                                          'text': c_text,
                                          'values': [val_x, val_y, val_z],
                                          'ui': viz.addText('N/A'),
                                          'markers': markers,
                                          'active_marker': 'axes'}

                self._ui.addLabelItem(str(cidx), self.controllers[cidx]['ui'])
                self._obj.extend([controller.model, c_axes, val_x, val_y, val_z])
                print('* Found Controller: {:d}'.format(cidx))

                self._callbacks.append(vizact.onsensordown(controller, steamvr.BUTTON_TRIGGER, self._storePoint, controller, cidx))
                self._callbacks.append(vizact.onsensordown(controller, steamvr.BUTTON_TRACKPAD, self._switchMarker, cidx))
                self._callbacks.append(vizact.onsensordown(controller, 1, self.savePoints))
                self._callbacks.append(vizact.onsensordown(controller, 0, self.saveScreenshot))
        else:
            print('* No controllers detected.')

        # Trackers
        if steamvr.getTrackerList():
            self._ui.addSeparator()
            self._ui.addItem(viz.addText('Trackers'))

            for tidx, tracker in enumerate(steamvr.getTrackerList()):
                
                tracker.model = tracker.addModel(parent=self._root)
                if not tracker.model:
                    tracker.model = viz.addGroup(parent=self._root)
                tracker.model.setCompositeAlpha(self.DEBUG_ALPHA)
                tracker.model.disable(viz.INTERSECTION)
                viz.link(tracker, tracker.model)

                t_axes = vizshape.addAxes(scale=(0.1, 0.1, 0.1))
                viz.link(tracker, t_axes)

                t_text = viz.addText3D(str(tidx), scale=(0.05, 0.05, 0.05), color=viz.BLUE,
                                    parent=tracker.model, pos=(-0.1, 0, 0))
                val_x = viz.addText3D('X: 0.00 (123.0°)', scale=(self.VALUE_SCALE,) * 3, 
                                    parent=tracker.model, pos=(0.18, 0.04, 0), color=viz.RED)
                val_x.setEuler([180, 0, 0], mode=viz.REL_LOCAL)
                val_y = viz.addText3D('Y: 0.00 (123.0°)', scale=(self.VALUE_SCALE,) * 3, 
                                    parent=tracker.model, pos=(0.18, 0.02, 0), color=viz.GREEN)
                val_y.setEuler([180, 0, 0], mode=viz.REL_LOCAL)
                val_z = viz.addText3D('Z: 0.00 (123.0°)', scale=(self.VALUE_SCALE,) * 3, 
                                    parent=tracker.model, pos=(0.18, 0, 0), color=viz.BLUE)
                val_z.setEuler([180, 0, 0], mode=viz.REL_LOCAL)

                self.trackers[tidx] = {'model': tracker.model,
                                       'axes': t_axes,
                                       'text': t_text,
                                       'values': [val_x, val_y, val_z],
                                       'ui': viz.addText('N/A')}
                self._ui.addLabelItem(str(tidx), self.trackers[tidx]['ui'])
                self._obj.extend([tracker.model, t_axes, val_x, val_y, val_z])
                print('* Found Vive tracker: {:d}'.format(tidx))
        else:
            print('* No trackers detected.')


    def addDebugModel(self, node, label, model=None, color=None, size=None):
        """ Add a debug model, axes and label for any node3d object. 
        Debug nodes are shown in UI and displayed/hidden together with 
        the rest of the debug scene. 

        Args:
            node: any Vizard node, group, or sensor object
            label (str): Brief text to identify the node in UI and VR
            model (str): One of:
                - 'sphere', 'cube', 'axes': use a vizshape primitive
                - a valid model file name ('test.osg'): load and use model
            color (3-tuple): RGB color, None for random (ignored for model files)
            size (float): Size of primitive, or scaling factor for model files
        """
        if label in self.nodes.keys():
            raise ValueError('Label already exists - node labels must be unique!')
            return None

        if color is None:
            color = colorsys.hsv_to_rgb(random.uniform(0.0, 1.0), 
                                        random.uniform(0.4, 1.0), 
                                        random.uniform(0.5, 1.0))
        # Add model and label text objects
        if model is not None and os.path.isfile(model):
            if size is None:
                size = 1.0
            _m = viz.addChild(model, parent=node)
            _m.setScale([size,] * 3)

        else:
            if size is None:
                size = 0.05

            if model is None:
                _m = viz.addGroup(parent=node)
                
            elif model == 'sphere':
                _m = vizshape.addSphere(radius=size, color=color, parent=node)
        
            elif model == 'cube':
                _m = vizshape.addCube(size=size, color=color, parent=node)

            elif model == 'axes':
                _m = vizshape.addAxes(length=size, color=color, parent=node)

        _m.disable(viz.INTERSECTION)
        _text = viz.addText3D(str(label), scale=(self.VALUE_SCALE,) * 3,
                              color=color, parent=_m, pos=(size * 1.1, 0.01, 0))
        _text.alignment(alignment=viz.ALIGN_LEFT_CENTER)
        _text.setEuler(0, 45, 0)

        # Add UI section for debug nodes if this is the first one
        if len(self.nodes) == 0:
            self._ui.addSeparator()
            self._ui.addItem(viz.addText('Other Nodes'))

        _ui = viz.addText('N/A')
        lbl = self._ui.addLabelItem(str(label), _ui)
        lbl.label.color(color)
        self._obj.extend([_m, _text])
        _m.visible(self._enable)
        _text.visible(self._enable)

        self.nodes[str(label)] = {'model': _m,
                                  'text': _text,
                                  'ui': _ui}

        print('* Added extra node entry: {:s}'.format(str(label)))
        return _m


    def enable(self, value):
        """ Set visibility of all debug objects and enable 
        or disable key callbacks (except the main debug toggle) """
        if value == -1:
            self._enable = not self._enable
        else:
            self._enable = value
        for obj in self._obj:
            obj.visible(self._enable)
        for c in self._callbacks:
            c.setEnabled(self._enable)
        if len(self._points) > 0:
            for point in self._points:
                point.visible(self._enable)
        if self._enable:
            viz.sendEvent(DEBUGGER_SHOW_EVENT)
        elif not self._enable:
            viz.sendEvent(DEBUGGER_HIDE_EVENT)


    def showLighthouseRays(self, state):
        """ Set visibility of lighthouse normal vectors """
        for lh in self.lighthouses.values():
            lh['normal'].visible(state)
    
    
    def _switchMarker(self, controller_index):
        """ Switch the currently shown (and placed) marker """
        m = list(self.controllers[controller_index]['markers'].keys())
        m.sort()
        mx = m.index(self.controllers[controller_index]['active_marker'])
    
        # Switch to next marker, or reset if reached the last one
        if mx == len(self.controllers[controller_index]['markers']) - 1:
            mx = 0
        else:
            mx += 1
        self.controllers[controller_index]['active_marker'] = m[mx]

        # Show the current marker and hide all others
        for marker in self.controllers[controller_index]['markers']:
            self.controllers[controller_index]['markers'][marker].visible(False)
        self.controllers[controller_index]['markers'][m[mx]].visible(True)

    def _storePoint(self, controller, index):
        """ Save and print controller position / orientation data 
        
        Args:
            controller: steamvr.Controller object,
            index: device index in steamvr.getControllerList
        """
        s = 'Controller {:d}: pos=[{:1.3f}, {:1.3f}, {:1.3f}], ori=[{:3.3f}, {:3.3f}, {:3.3f}]'
        p = controller.getPosition()
        e = controller.getEuler()
        print(s.format(index, p[0], p[1], p[2], e[0], e[1], e[2]))
        
        active_marker = self.controllers[index]['active_marker']
        px = self.controllers[index]['markers'][active_marker].copy()
        px.setParent(self._root)
        px.setPosition(p)
        px.setEuler(e)
        if active_marker == 'axes':
            px.setScale([self.MARKER_SIZE,] * 3)
        px._dev_index = index
        px._label = active_marker
        self._points.append(px)


    def savePoints(self, filename='viz_svr_debug.csv'):
        """ Save list of stored coordinate points 
        
        Args:
            filename (str): Name of CSV output file
        """
        fields = ['point', 'device', 'marker', 'posX', 'posY', 'posZ', 'eulerX', 'eulerY', 'eulerZ']
        with open(filename, 'w') as pfile:
            writer = csv.DictWriter(pfile, delimiter='\t', lineterminator='\n', 
                                    fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for pidx, point in enumerate(self._points):
                p = point.getPosition()
                e = point.getEuler()
                writer.writerow({'point': pidx, 'posX': p[0], 'posY': p[1], 'posZ': p[2], 
                                'eulerX': e[0], 'eulerY': e[1], 'eulerZ': e[2], 
                                'device': point._dev_index, 'marker': point._label})

        viztask.schedule(showVRText('Points data saved.'))
        print('Points data saved.')


    def clearPoints(self):
        """ Remove previously placed point axes objects
        and clear the point data list """
        for object in self._points:
            object.remove()
        self._points = []
        viztask.schedule(showVRText('Points data cleared.'))
        print('Point data and axes cleared.')


    def saveScreenshot(self):
        """ Save a BMP screenshot of the current Vizard window """
        fn = 'svr_screenshot_{:d}.bmp'.format(self._next_screenshot)
        viz.window.screenCapture(fn)
        self._next_screenshot += 1
        viztask.schedule(showVRText('Screenshot saved.'))
        print('Screenshot saved.')


    def saveDebugScene(self, filename='svr_debug.osgb'):
        """ Save the debug overlay scene to a 3D model file """
        print('Exporting scene. This could take a while and Vizard rendering may stop.')
        self._root.save(filename)
        print('Scene exported to {:s}.'.format(filename))

    
    def _updateUI(self):
        """ Update displayed position and orientation data """
        FMT = '({:.2f},{:.2f},{:.2f}) / ({:3.1f},{:3.1f},{:3.1f})'
        VAL_FMT = '{:s}: {:0.2f} ({:3.1f}°)'
        
        hmdpos = self.hmd['sensor'].getPosition(viz.ABS_GLOBAL)
        hmdori = self.hmd['sensor'].getEuler(viz.ABS_GLOBAL)
        self.hmd['ui'].message(FMT.format(hmdpos[0], hmdpos[1], hmdpos[2], 
                                          hmdori[1], hmdori[0], hmdori[2]))
        self.hmd['hud'].message('X: {:.2f}\nY: {:.2f}\nZ: {:.2f}'.format(hmdpos[0], hmdpos[1], hmdpos[2]))

        for c in self.controllers.keys():
            pos = self.controllers[c]['model'].getPosition(viz.ABS_GLOBAL)
            ori = self.controllers[c]['model'].getEuler(viz.ABS_GLOBAL)
            self.controllers[c]['ui'].message(FMT.format(pos[0], pos[1], pos[2], 
                                                    ori[1], ori[0], ori[2]))
            self.controllers[c]['values'][0].message(VAL_FMT.format('X', pos[0], ori[1]))
            self.controllers[c]['values'][1].message(VAL_FMT.format('Y', pos[1], ori[0]))
            self.controllers[c]['values'][2].message(VAL_FMT.format('Z', pos[2], ori[2]))

        for t in self.trackers.keys():
            pos = self.trackers[t]['model'].getPosition(viz.ABS_GLOBAL)
            ori = self.trackers[t]['model'].getEuler(viz.ABS_GLOBAL)
            self.trackers[t]['ui'].message(FMT.format(pos[0], pos[1], pos[2], 
                                                ori[1], ori[0], ori[2]))

            self.trackers[t]['values'][0].message(VAL_FMT.format('X', pos[0], ori[1]))
            self.trackers[t]['values'][1].message(VAL_FMT.format('Y', pos[1], ori[0]))
            self.trackers[t]['values'][2].message(VAL_FMT.format('Z', pos[2], ori[2]))

        for n in self.nodes.keys():
            pos = self.nodes[n]['model'].getPosition(viz.ABS_GLOBAL)
            ori = self.nodes[n]['model'].getEuler(viz.ABS_GLOBAL)
            self.nodes[n]['ui'].message(FMT.format(pos[0], pos[1], pos[2], 
                                                   ori[1], ori[0], ori[2]))



if __name__ == '__main__':
    """ If module is called directly, just display the debug view """
    viz.setMultiSample(4)    
    viz.go()
    hmd = steamvr.HMD()
    navigationNode = viz.addGroup()
    viewLink = viz.link(navigationNode, viz.MainView)
    viewLink.preMultLinkable(hmd.getSensor())
    
    vizshape.addPlane(size=(100,100), color=(0.4, 0.4, 0.4))
    headlight = viz.MainView.getHeadLight()
    headlight.disable()
    main_light = vizfx.addDirectionalLight(euler=(0,90,0), color=viz.WHITE)
    origin_light = vizfx.addPointLight(color=viz.WHITE, pos=(0,0,0))

    debugger = SteamVRDebugOverlay(enable=True)
