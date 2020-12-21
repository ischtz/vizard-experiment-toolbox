# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Data structures and classes that do not depend on Vizard

import json
import pickle

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



class ParamSet(object):
    """ Stores study or trial parameters that can be accessed 
    using both key (x['key']) and dot notation (x.key) for 
    convenience. Supports JSON im-/export. """

    def __init__(self, input_dict=None):
        if input_dict is not None:
            self.__dict__ = input_dict.copy()
    
    
    def __getitem__(self, key):
        return self.__dict__[key]
    
    
    def __setitem__(self, key, value):
        self.__dict__[key] = value

    
    def __repr__(self):
        return repr(self.__dict__)
    
    
    def __str__(self):
        """ Pretty-print parameters for readability """
        key_lens = []
        for key in self.__dict__:
            key_lens.append(len(key))
        spacing = max(key_lens)
        if spacing > 20:
            spacing = 20
        s = ''
        fmt = '{{:{:d}s}}: {{:s}}\n'.format(spacing)
        for key in sorted(self.__dict__.keys()):
            s += fmt.format(str(key), str(self.__dict__[key]))
        return s
    
    
    def __len__(self):
        return len(self.__dict__)
    
    
    def __iter__(self):
        return iter(self.__dict__)
    

    def __contains__(self, key):
        if key in self.__dict__.keys():
            return True
        else:
            return False


    def toJSON(self):
        """ Return JSON representation of this ParamSet """
        return json.dumps(self.__dict__)


    def toJSONFile(self, json_file):
        """ Save this ParamSet to a JSON file """
        with open(json_file, 'w') as jf:
            jf.write(json.dumps(self.__dict__))


    @classmethod
    def fromJSONFile(cls, json_file):
        """ Create a new ParamSet from a JSON file """
        with open(json_file, 'r') as jf:
            return ParamSet(input_dict=json.load(jf))



class ValidationResult(object):
    """ Container to hold results and raw data of a gaze validation sequence 
    
    Attributes:
        result (dict): Dict of result measures
        metadata (dict): Participant metadata dict
        targets: List of result dicts per target
        samples: List of raw sample data per target
    """
    def __init__(self, result=None, metadata={}, targets=None, samples=None):

        self.metadata = metadata

        # Global average accuracy, precision, etc. 
        vars = ['acc', 'accX', 'accY', 'sd', 'sdX', 'sdY',  'rmsi', 'rmsiX', 'rmsiY', 'ipd', 
                'acc_L', 'accX_L', 'accY_L', 'sd_L', 'sdX_L', 'sdY_L',  'rmsi_L', 'rmsiX_L', 'rmsiY_L',
                'acc_R', 'accX_R', 'accY_R', 'sd_R', 'sdX_R', 'sdY_R',  'rmsi_R', 'rmsiX_R', 'rmsiY_R']
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


    def save(self, file_name='val_result.pkl', format='pickle'):
        """ Save validation data to a file. 
        Pickling the whole object enables later access to built-in analysis
        and plotting methods, but other file formats are available as well. 
        
        Args:
            file_name (str): Output file name
            format (str): File type, 'json' or 'pickle'
        """
        if format.lower() == 'json':
            with open(file_name, 'w') as f:
                f.write(json.dumps(self.__dict__))

        elif format.lower() == 'pickle':
            with open(file_name, 'wb') as f:
                pickle.dump(self, f)

    
    if _HAS_SCI_PKGS:
        def plotAccuracy(self):
            """ Spatial plot of mean and median accuracy in dataset """
            fig = plt.figure()

            # One subplot per depth plane
            depths = []
            for t in self.targets:
                if t['d'] not in depths:
                    depths.append(t['d'])
            
            axs = {}
            c = 1
            for d in depths:
                ax = fig.add_subplot(1, len(depths), c)
                ax.set_title('Accuracy, d={:.1f}m'.format(d))
                ax.set_xlabel('Horizontal Position (degrees)')
                ax.set_ylabel('Vertical Position (degrees)')

                legend_handles = []
                for t in self.targets:
                    if t['d'] == d:
                        ax.plot(t['x'], t['y'], 'k+', markersize=12)
                        ax.plot([t['x'], t['avgX']], [t['y'], t['avgY']], 'r-', linewidth=1)
                        Hmean, = ax.plot(t['avgX'], t['avgY'], 'r.', markersize=10)
                        ax.plot([t['x'], t['medX']], [t['y'], t['medY']], 'b-', linewidth=1)
                        Hmedian, = ax.plot(t['medX'], t['medY'], 'b.', markersize=10)
                        ax.annotate('{:.2f}'.format(t['acc']), xy=(t['x'], t['y']), xytext=(0, 10),
                                    textcoords='offset points', ha='center')

                        if len(legend_handles) < 1:
                            legend_handles.append(Hmean)
                            legend_handles.append(Hmedian)

                ax.margins(x=0.15, y=0.15)
                ax.legend(legend_handles, ['mean', 'median'], ncol=2, bbox_to_anchor=(0, 0), loc='lower left')
                axs[d] = ax
                c += 1

            fig.show()


        def plotPrecision(self, measure='sd'):
            """ Spatial plot of individual samples and SD precision in dataset 
            
            Args:
                measure (str): 'sd' or 'rmsi'
            """
            if measure not in ['sd', 'rmsi']:
                raise ValueError('Invalid measure specified.')
            fig = plt.figure()

            # One subplot per depth plane
            depths = []
            for t in self.targets:
                if t['d'] not in depths:
                    depths.append(t['d'])
            
            axs = {}
            c = 1
            for d in depths:
                ax = fig.add_subplot(1, len(depths), c)
                ax.set_title('Precision ({:s}), d={:.1f}m'.format(measure, d))
                ax.set_xlabel('Horizontal Position (degrees)')
                ax.set_ylabel('Vertical Position (degrees)')

                for idx, t in enumerate(self.targets):
                    sam = self.samples[idx]
                    if t['d'] == d:
                        ax.plot(t['x'], t['y'], 'k+', markersize=12)
                        tar_samX = []
                        tar_samY = []
                        for s in sam:
                            tar_samX.append(s['targetGaze_X'])
                            tar_samY.append(s['targetGaze_Y'])
                        ax.plot(tar_samX, tar_samY, '.',  markersize=3)
                        ax.plot(t['avgX'], t['avgY'], 'k.', markersize=6)
                        ax.annotate('{:.2f}'.format(t[measure]), xy=(t['x'], t['y']), xytext=(0, 10),
                                    textcoords='offset points', ha='center')

                ax.margins(x=0.15, y=0.15)
                axs[d] = ax
                c += 1

            fig.show()


        def getTargetDataFrame(self):
            """ Return pandas.DataFrame of individual target results """
            return pd.DataFrame(self.targets)


        def getSamplesDataFrame(self, target):
            """ Return pandas.DataFrame of raw sample data for given target 
            
            Args:
                target (int): Target index in self.targets to retrieve
            """
            return pd.DataFrame(self.samples[target])
            


