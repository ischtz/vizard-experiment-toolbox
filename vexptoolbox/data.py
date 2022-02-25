# -*- coding: utf-8 -*-

# vexptoolbox: Vizard Toolbox for Behavioral Experiments
# Data structures and classes that do not depend on Vizard

import json
import copy
import pickle

from .stats import *

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

MISSING_VALUE = -99999.0


class ParamSet(object):
    """ Stores study or trial parameters that can be accessed 
    using both key (x['key']) and dot notation (x.key) for 
    convenience. Supports JSON im-/export. """

    def __init__(self, input_dict=None):
        if input_dict is not None:
            if type(input_dict) not in [dict, ParamSet]:
                raise ValueError('input_dict must be a dict or ParamSet!')
            
            if type(input_dict) == ParamSet:
                self.__dict__ = input_dict.__dict__.copy()
            else:
                self.__dict__ = input_dict.copy()
    
    
    def __getitem__(self, key):
        return self.__dict__[key]
    
    
    def __setitem__(self, key, value):
        self.__dict__[key] = value

    
    def __repr__(self):
        return repr(self.__dict__)
    
    
    def __str__(self):
        """ Pretty-print parameters for readability """
        if len(self.__dict__) > 0:
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
        else:
            return('Empty parameter set.')
    
    
    def __len__(self):
        return len(self.__dict__)
    
    
    def __iter__(self):
        """ Iteration returns parameters as (key, value) tuples """
        return iter(zip(self.__dict__.keys(), self.__dict__.values()))


    def __contains__(self, key):
        if key in self.__dict__.keys():
            return True
        else:
            return False


    def toDict(self):
        """ Return a copy of all attributes as a dict """
        return copy.deepcopy(self.__dict__)

    
    def toJSON(self):
        """ Return JSON representation of this ParamSet """
        return json.dumps(self.__dict__)


    def toJSONFile(self, json_file):
        """ Save this ParamSet to a JSON file 
        
        Args:
            json_file (str): Output file name
        """
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
        self.targets = targets	# by-target list of validation result dicts
        self.samples = samples	# by-target list of raw sample data
        self._results = {}

        self._setResults(result)


    def _setResults(self, result):
        """ Update aggregate result variables based on a dictionary """
        self._results = {}
        vars = ['acc', 'accX', 'accY', 'sd', 'sdX', 'sdY',  'rmsi', 'rmsiX', 'rmsiY', 'ipd', 
                'acc_L', 'accX_L', 'accY_L', 'sd_L', 'sdX_L', 'sdY_L',  'rmsi_L', 'rmsiX_L', 'rmsiY_L',
                'acc_R', 'accX_R', 'accY_R', 'sd_R', 'sdX_R', 'sdY_R',  'rmsi_R', 'rmsiX_R', 'rmsiY_R',
                'start_sample', 'end_sample']

        for v in vars:
            setattr(self, v, MISSING_VALUE)
            self._results[v] = MISSING_VALUE
            if result is not None and v in result.keys():
                setattr(self, v, result[v])
                self._results[v] = result[v]

    
    def __str__(self):
        """ Printable validation summary """
        s = 'Validation Result: Acc: {:.2f} (x: {:.2f}, y: {:.2f}), RMSi: {:.2f}, SD: {:.2f}'
        out = s.format(self.acc, self.accX, self.accY, self.rmsi, self.sd)
        for tar in self.targets:
            s = '\n  Target #{:d} - x: {:+.1f}, y: {:+.1f}, d: {:.1f} - Acc: {:.2f} (x: {:.2f}, y: {:.2f})\t RMSi: {:.2f}, SD: {:.2f}'
            out += s.format(tar['set_no'], tar['x'], tar['y'], tar['d'], tar['acc'], tar['accX'], tar['accY'], tar['rmsi'], tar['sd'])
        return out


    @property
    def results(self):
        return self._results.copy()


    def toDict(self):
        """ Return a copy of all results as a dict """
        return copy.deepcopy(self.__dict__)

    
    def toJSON(self):
        """ Return JSON representation of validation data """
        return json.dumps(self.__dict__)


    def toJSONFile(self, json_file):
        """ Save validation results to a JSON file 

        Args:
            json_file (str): Output file name
        """
        with open(json_file, 'w') as jf:
            jf.write(json.dumps(self.__dict__))


    def toPickleFile(self, pickle_file='val_result.pkl'):
        """ Save ValidationResult object to a pickle file. 
        
        This will enable access to built-in analysis and 
        plotting methods during later analysis. 

        Args:
            pickle_file (str): Output file name
        """
        with open(pickle_file, 'wb') as f:
            pickle.dump(self, f)


    if _HAS_SCI_PKGS:
        def recomputeMetrics(self, start_sample=0, end_sample=None, 
                            tar_x_range=None, tar_y_range=None, depth_range=None,
                            agg_fun=None):
            """ Recompute validation result metrics from stored sample data,
            while allowing to specify the range of samples and targets to analyze

            Args:
                start_sample (int): First sample to use for each target
                end_sample (int): Last sample to use for each target
                tar_x_range: A 2-tuple of (min, max) horizontal target position, or
                    a scalar value denoting maximum horizontal eccentricity
                tar_y_range: Same as tar_x_range, but for vertical target positions
                depth_range: A 2-tuple of (min, max) target depth, or a single scalar
                agg_fun (function): Function to use for aggregation, default: mean

            Returns: new ValidationResult object with updated target and average metrics
            
            """
            tar_data = []
            avg_data = {}
            
            if agg_fun is None:
                agg_fun = mean

            if tar_x_range is not None:
                try:
                    if len(tar_x_range) != 2:
                        raise ValueError('tar_x_range must be scalar or contain exactly two values!')
                except TypeError:
                    tar_x_range = (-1 * tar_x_range, tar_x_range)
            if tar_y_range is not None:
                try:
                    if len(tar_y_range) != 2:
                        raise ValueError('tar_y_range must be scalar or contain exactly two values!')
                except TypeError:
                    tar_y_range = (-1 * tar_y_range, tar_y_range)
            if depth_range is not None:
                try:
                    if len(depth_range) != 2:
                        raise ValueError('depth_range must be scalar or contain exactly two values!')
                except TypeError:
                    depth_range = (0, depth_range)
                if depth_range[0] < 0 or depth_range[1] < 0:
                    raise ValueError('depth_range values cannot be negative!')

            # By-target metrics
            for tar, sam in zip(self.targets, self.samples):
                
                d = tar.copy()
                if end_sample is None:
                    end_sample = len(sam)
                s = pd.DataFrame(sam[start_sample:end_sample])
                
                # Gaze position and offset
                d['avgX'] = mean(s.targetGaze_X)
                d['avgY'] = mean(s.targetGaze_Y)
                d['medX'] = median(s.targetGaze_X)
                d['medY'] = median(s.targetGaze_Y)
                d['offX'] = mean(s.targetErr_X)
                d['offY'] = mean(s.targetErr_Y)

                # Angular gaze errors
                tgtHMD = np.array([tar['xm'], tar['ym'], tar['d']]) # Target position re: HMD                
                deltaX = np.abs(s.targetErr_X.values)
                deltaY = np.abs(s.targetErr_Y.values)
                delta = []
                deltaM = [[], []]

                # Recompute absolute angular deviations if necessary (later addition to format)
                if 'targetErr' in s.columns:
                    delta = s.targetErr.values
                    if 'targetErrL' in s.columns and 'targetErrR' in s.columns:
                        deltaM = np.array([s.targetErrL.values, s.targetErrR.values])

                else:
                    for ix in s.iterrows():

                        # Combined gaze vector
                        vEyeGaze = np.array((ix[1].trackVec_X, ix[1].trackVec_Y, ix[1].trackVec_Z))

                        # Compute eye-target vector using actual eye origin on each sample
                        # This is necessary to account for eye tracker jitter
                        gazeOri = (ix[1].tracker_posX, ix[1].tracker_posY, ix[1].tracker_posZ)
                        vEyeTar = tgtHMD - gazeOri
                        vEyeTar = vEyeTar / np.linalg.norm(vEyeTar)

                        # Compute angular error
                        delta.append(np.degrees(np.arccos(np.clip(np.dot(vEyeTar, vEyeGaze), -1.0, 1.0))))

                        # Compute error for monocular data, if available
                        for eyei, eye in enumerate(['L', 'R']):
                            if 'tracker{:s}_posX'.format(eye) in ix[1]:
                                vEyeGazeM = (ix[1]['trackVec{:s}_X'.format(eye)], ix[1]['trackVec{:s}_Y'.format(eye)], ix[1]['trackVec{:s}_Z'.format(eye)])
                                gazeOriM = (ix[1]['tracker{:s}_posX'.format(eye)], ix[1]['tracker{:s}_posY'.format(eye)], ix[1]['tracker{:s}_posZ'.format(eye)])
                                vEyeTarM = tgtHMD - gazeOriM
                                vEyeTarM = vEyeTarM / np.linalg.norm(vEyeTarM)
                                deltaM[eyei].append(np.degrees(np.arccos(np.clip(np.dot(vEyeTarM, vEyeGazeM), -1.0, 1.0))))

                # Accuracy
                d['acc'] = mean(delta)
                d['accX'] = mean(deltaX)
                d['accY'] = mean(deltaY)
                d['medacc'] = median(delta)
                d['medaccX'] = mean(deltaX)
                d['medaccY'] = mean(deltaY)

                # Precision
                d['sd'] = sd(delta)
                d['sdX'] = sd(deltaX)
                d['sdY'] = sd(deltaY)
                d['rmsi'] = rmsi(delta)
                d['rmsiX'] = rmsi(deltaX)
                d['rmsiY'] = rmsi(deltaY)

                # Monocular measures, if available
                for eyei, eye in enumerate(['L', 'R']):
                    if len(deltaM[eyei]) > 0:

                        d['avgX_{:s}'.format(eye)] = mean(s.loc[:, 'targetGaze{:s}_X'.format(eye)].values)
                        d['avgY_{:s}'.format(eye)] = mean(s.loc[:, 'targetGaze{:s}_Y'.format(eye)].values)
                        d['medX_{:s}'.format(eye)] = median(s.loc[:, 'targetGaze{:s}_X'.format(eye)].values)
                        d['medY_{:s}'.format(eye)] = median(s.loc[:, 'targetGaze{:s}_Y'.format(eye)].values)
                        d['offX_{:s}'.format(eye)] = mean(s.loc[:, 'targetErr{:s}_X'.format(eye)].values)
                        d['offY_{:s}'.format(eye)] = mean(s.loc[:, 'targetErr{:s}_Y'.format(eye)].values)
                        
                        d['acc_{:s}'.format(eye)] = mean(deltaM[eyei])
                        d['accX_{:s}'.format(eye)] = mean(s.loc[:, 'targetErr{:s}_X'.format(eye)].abs().values)
                        d['accY_{:s}'.format(eye)] = mean(s.loc[:, 'targetErr{:s}_Y'.format(eye)].abs().values)
                        d['medacc_{:s}'.format(eye)] = median(deltaM[eyei])
                        d['medaccX_{:s}'.format(eye)] = median(s.loc[:, 'targetErr{:s}_X'.format(eye)].abs().values)
                        d['medaccY_{:s}'.format(eye)] = median(s.loc[:, 'targetErr{:s}_Y'.format(eye)].abs().values)

                        d['sd_{:s}'.format(eye)] = sd(deltaM[eyei])
                        d['sdX_{:s}'.format(eye)] = sd(s.loc[:, 'targetErr{:s}_X'.format(eye)].values)
                        d['sdY_{:s}'.format(eye)] = sd(s.loc[:, 'targetErr{:s}_Y'.format(eye)].values)
                        d['rmsi_{:s}'.format(eye)] = rmsi(deltaM[eyei])                        
                        d['rmsiX_{:s}'.format(eye)] = rmsi(s.loc[:, 'targetErr{:s}_X'.format(eye)].values)
                        d['rmsiY_{:s}'.format(eye)] = rmsi(s.loc[:, 'targetErr{:s}_Y'.format(eye)].values)

                # Inter-pupillary distance (only if both eyes were recorded)
                if len(deltaM[0]) > 0 and len(deltaM[1]) > 0:
                    d['ipd'] = mean(np.abs(s.trackerR_posX - s.trackerL_posX) * 1000.0)

                tar_data.append(d)

                # Collect target for aggregration, skip if outside specified range
                if tar_x_range is not None and (tar['x'] < tar_x_range[0] or tar['x'] > tar_x_range[1]):
                    continue
                if tar_y_range is not None and (tar['y'] < tar_y_range[0] or tar['y'] > tar_y_range[1]):
                    continue
                if depth_range is not None and (tar['d'] < depth_range[0] or tar['d'] > depth_range[1]):
                    continue
                for var in d.keys():
                    if var not in avg_data:
                        avg_data[var] = []
                    avg_data[var].append(d[var])


            # Aggregate
            for var in avg_data.keys():
                avg_data[var] = agg_fun(avg_data[var])

            avg_data['start_sample'] = start_sample
            avg_data['end_sample'] = end_sample

            return ValidationResult(result=avg_data, 
                                    metadata=self.metadata, 
                                    samples=self.samples, 
                                    targets=tar_data)


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
            


