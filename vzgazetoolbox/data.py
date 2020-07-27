# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Data structures and classes that do not depend on Vizard

try:
	# Some functionality such as plotting is only available when a scientific 
	# Python stack is installed, which by default is not the case in Vizard.
	import numpy as np
	import pandas as pd
	import matplotlib.pyplot as plt
	_HAS_SCI_PKGS = True

except ImportError:
	_HAS_SCI_PKGS = False


# single central target (default)
VAL_TAR_C =		[[0.0,  0.0,  6.0]]	

# 5-point cross at +/- 5 deg, 6m distance
VAL_TAR_CR5 =  [[0.0,  0.0,  6.0],	
				[5.0,  0.0,  6.0],
				[0.0,  -5.0, 6.0],
				[-5.0, 0.0,  6.0],
				[0.0, 5.0,   6.0]] # N=5

# 3x3 full square at +/- 5 deg, 6m distance
VAL_TAR_SQ5 =  [[0.0,  0.0,  6.0],
				[5.0,  0.0,  6.0],
				[0.0,  -5.0, 6.0],
				[-5.0, 0.0,  6.0],
				[0.0, 5.0,   6.0],
				[5.0, 5.0,   6.0],
				[5.0,  -5.0, 6.0],
				[-5.0, -5.0, 6.0],
				[-5.0,  5.0, 6.0]] # N=9

# 5x5 major positions, +/- 10 deg, 6m distance
VAL_TAR_CR10 = [[0.0,  0.0,  6.0],	
				[5.0,  0.0,  6.0],
				[0.0,  -5.0, 6.0],
				[-5.0, 0.0,  6.0],
				[0.0,  5.0,  6.0],
				[5.0,  5.0,  6.0],
				[5.0,  -5.0, 6.0],
				[-5.0, -5.0, 6.0],
				[-5.0,  5.0, 6.0],
				[10.0, 0.0,  6.0],
				[0.0, -10.0, 6.0],
				[-10.0, 0.0, 6.0],
				[0.0,  10.0, 6.0],
				[10.0, 10.0, 6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0]] # N=17

# 5x5 full square, +/- 10 deg, 6m distance
VAL_TAR_SQ10 = [[0.0,  0.0,   6.0],	
				[5.0,  0.0,   6.0],
				[0.0,  -5.0,  6.0],
				[-5.0, 0.0,   6.0],
				[0.0,  5.0,   6.0],
				[5.0,  5.0,   6.0],
				[5.0,  -5.0,  6.0],
				[-5.0, -5.0,  6.0],
				[-5.0,  5.0,  6.0],
				[10.0, 0.0,   6.0],
				[0.0, -10.0,  6.0],
				[-10.0, 0.0,  6.0],
				[0.0,  10.0,  6.0],
				[10.0, 10.0,  6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0],
				[10.0, 5.0,   6.0],
				[10.0, -5.0,  6.0],
				[5.0, -10.0,  6.0],
				[-5.0, -10.0, 6.0],				
				[-10.0, -5.0, 6.0],
				[-10.0, 5.0,  6.0],
				[-5.0, 10.0,  6.0], 
				[5.0, 10.0,   6.0]] # N=25

# 7x7 major positions, +/- 15 deg, 6m distance
VAL_TAR_CR15 = [[0.0,  0.0,   6.0],
				[5.0,  0.0,   6.0],
				[0.0,  -5.0,  6.0],
				[-5.0, 0.0,   6.0],
				[0.0,  5.0,   6.0],
				[5.0,  5.0,   6.0],
				[5.0,  -5.0,  6.0],
				[-5.0, -5.0,  6.0],
				[-5.0,  5.0,  6.0],
				[10.0, 0.0,   6.0],
				[0.0, -10.0,  6.0],
				[-10.0, 0.0,  6.0],
				[0.0,  10.0,  6.0],
				[10.0, 10.0,  6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0],
				[15.0, 0.0,   6.0],
				[0.0, -15.0,  6.0],
				[-15.0, 0.0,  6.0],
				[0.0, 15.0,   6.0],
				[15.0, 15.0,  6.0],
				[15.0, -15.0, 6.0],
				[-15.0,-15.0, 6.0],
				[-15.0, 15.0, 6.0]] # N=25
				
# 7x7 full square, +/- 15 deg, 6m distance
VAL_TAR_SQ15 = [[0.0,  0.0,   6.0],
				[5.0,  0.0,   6.0],
				[0.0,  -5.0,  6.0],
				[-5.0, 0.0,   6.0],
				[0.0,  5.0,   6.0],
				[5.0,  5.0,   6.0],
				[5.0,  -5.0,  6.0],
				[-5.0, -5.0,  6.0],
				[-5.0,  5.0,  6.0],
				[10.0, 0.0,   6.0],
				[0.0, -10.0,  6.0],
				[-10.0, 0.0,  6.0],
				[0.0,  10.0,  6.0],
				[10.0, 10.0,  6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0],
				[10.0, 5.0,   6.0],
				[10.0, -5.0,  6.0],
				[5.0, -10.0,  6.0],
				[-5.0, -10.0, 6.0],
				[-10.0, -5.0, 6.0],
				[-10.0, 5.0,  6.0],
				[-5.0, 10.0,  6.0], 
				[5.0, 10.0,   6.0],
				[15.0, 0.0,   6.0],
				[0.0, -15.0,  6.0],
				[-15.0, 0.0,  6.0],
				[0.0, 15.0,   6.0],
				[15.0, 15.0,  6.0],
				[15.0, -15.0, 6.0],
				[-15.0,-15.0, 6.0],
				[-15.0, 15.0, 6.0],
				[15.0, 10.0,  6.0],
				[15.0, 5.0,   6.0],
				[15.0, -5.0,  6.0],
				[15.0, -10.0, 6.0],
				[10.0, -15.0, 6.0],
				[5.0, -15.0,  6.0],
				[-5.0, -15.0, 6.0],
				[-10.0,-15.0, 6.0],
				[-15.0,-10.0, 6.0],
				[-15.0, -5.0, 6.0],
				[-15.0, 5.0,  6.0],
				[-15.0, 10.0, 6.0],
				[-10.0, 15.0, 6.0],
				[-5.0, 15.0,  6.0],
				[5.0, 15.0,   6.0],
				[10.0, 15.0,  6.0]] # N=49



class ValidationResult():
	""" Container to hold results and raw data of a gaze validation sequence 
	
	Attributes:
		time (str): Validation time stamp
		label (str): Optional label for this validation (e.g., 'pre' or 'post')
		result (dict): Dict of result measures
		targets: List of result dicts per target
		samples: List of raw sample data per target
	"""
	def __init__(self, time='', label='', result=None, targets=None, samples=None):

		# Metadata
		self.time = time
		self.label = label

		# Global average accuracy, precision, etc. 
		vars = ['acc', 'accX', 'accY', 'sd', 'sdX', 'sdY',  'rmsi', 'rmsiX', 'rmsiY', 'ipd']
		for v in vars:
			setattr(self, v, -99999.0)
			if result is not None and v in result.keys():
				setattr(self, v, result[v])

		# By-target data
		self.targets = targets	# by-target list of validation result dicts
		self.samples = samples	# by-target list of raw sample data


	def __str__(self):
		""" Printable validation summary """
		s = 'Validation Result: Acc: {:.2f} (x: {:.2f}, y: {:.2f}), RMSi: {:.2f}, SD: {:.2f}'
		out = s.format(self.acc, self.accX, self.accY, self.rmsi, self.sd)
		for tar in self.targets:
			s = '\n  Target #{:d} - x: {:+.1f}, y: {:+.1f}, d: {:.1f} - Acc: {:.2f} (x: {:.2f}, y: {:.2f})\t RMSi: {:.2f}, SD: {:.2f}'
			out += s.format(tar['set_no'], tar['x'], tar['y'], tar['d'], tar['acc'], tar['accX'], tar['accY'], tar['rmsi'], tar['sd'])
		return out


	if _HAS_SCI_PKGS:
		def plot_accuracy(self):
			""" Spatial plot of mean and median accuracy in dataset """
			legend_markers = []
			fig = plt.figure()
			ax = fig.add_subplot(111)
			
			for t in self.targets:
				ax.plot(t['x'], t['y'], 'k+', markersize=12)
				ax.plot([t['x'], t['avgX']], [t['y'], t['avgY']], 'r-', linewidth=1)
				ax.plot(t['avgX'], t['avgY'], 'r.', markersize=10)
				ax.plot([t['x'], t['medX']], [t['y'], t['medY']], 'b-', linewidth=1)
				ax.plot(t['medX'], t['medY'], 'b.', markersize=10)
			
			ax.set_title('Validation Accuracy Plot')
			ax.set_xlabel('Horizontal Position (degrees)')
			ax.set_ylabel('Vertical Position (degrees)')
			fig.show()
			


