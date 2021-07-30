# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Statistics helper functions that work without numpy/scipy installed

import math

def mean(x):
    """ Calculate Arithmetic Mean without using numpy """
    return sum([float(a) for a in x]) / float(len(x))


def sd(x):
    """ Calculate population Standard Deviation without numpy """
    xm = mean(x)
    return math.sqrt(sum([(float(xi) - xm)**2 for xi in x]) / float(len(x)))


def median(x):
    """ Calculate sample Median without using numpy """
    x = sorted(x)
    m = int(len(x) / 2.0)
    if len(x) % 2 == 0:		
        return (x[m] + x[m-1]) / 2.0
    else:
        return x[m]


def rmsi(x):
    """ Calculate intersample Root Mean Square (RMS) error (precision) 
    see also Holmqvist, Nyström & Mulvey, 2012, ETRA """
    dsq = [(float(x[t])-float(x[t-1]))**2 for t in range(1, len(x))]
    return math.sqrt(sum(dsq) / len(dsq))


def rmsm(x):
    """ Calculate 1D RMS error between samples and the sample mean """
    xm = mean(x)
    dsq = [(float(x[t])-xm)**2 + (float(y[t])-ym)**2 + (float(z[t])-zm)**2 for xi in x]
    return math.sqrt(sum(dsq) / len(dsq))


def rmsm3(x, y, z):
    """ Calculate 3D RMS error between samples and the sample mean """	
    xm = mean(x)
    ym = mean(y)
    zm = mean(z)
    dsq = [((float(x[i])-xm)**2) + ((float(y[i])-ym)**2) +((float(z[i])-zm)**2) for i in range(0, len(x))]
    return math.sqrt(sum(dsq) / len(dsq))


def mad(x):
    """ Calculate Median Absolute Deviation (MAD) of samples (precision)
    see also Lohr, Friedman & Komogortsev, 2019, arXiv.
    """
    medx = median(x)
    return median([abs(xi - medx) for xi in x])


def mad2(x, y):
    """ Calculate 2D Median Absolute Deviation (MAD) of samples (precision).
    2D version used for horizontal and vertical gaze angles. See also 
    Lohr, Friedman & Komogortsev, 2019, arXiv.
    """
    medx = median(x)
    medy = median(y)
    return math.sqrt((median([abs(xi - medx) for xi in x]) ** 2) + (median([abs(yi - medy) for yi in y]) ** 2))
