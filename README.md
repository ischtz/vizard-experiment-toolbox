## vexptoolbox: A Python toolbox for VR behavioral experiments using Vizard

[![PyPI version](https://badge.fury.io/py/vexptoolbox.svg)](https://badge.fury.io/py/vexptoolbox)

The *vexptoolbox* package aims to help researchers in implementing common tasks in behavioral experiments using the WorldViz Vizard VR platform. Current features include randomized, trial-based experimental designs, straightforward storing of result data to standardized file formats, and built-in recording of eye tracking and motion tracking data. The code supports Vizard 6 (based on Python 2.7) and Vizard 7 (based on Python 3). 

This project began as a collection of common functionality that we encountered frequently when implementing behavioral VR experiments at [the Giessen University Perception and Action Lab](https://www.uni-giessen.de/fbz/fb06/psychologie/abt/allgemeine-psychologie/wh). It is a work in progress - please feel free to report any bugs you find or feature suggestsions using the Issues tool or provide a Pull Request! A manuscript describing this toolbox is currently in preparation and will be linked here after peer-review. 

## Installation

### Using the Vizard Package Manager

1. Open the [Vizard package manager](https://docs.worldviz.com/vizard/latest/#Package_Manager.htm) using *Tools > Package Manager* from the menu bar
2. Search for "vexptoolbox" 

    ![grafik](https://user-images.githubusercontent.com/7711674/156032118-87a3875d-d431-4673-97a9-e6b1389e67ba.png)

3. Select *Install*
    - In *Vizard 6*, the package manager will install and update the toolbox globally for all Vizard scripts
    - In *Vizard 7*, you will be able to install the package globally or only for the current script. The latter option will create a subfolder next to the currently selected script file but allow different packages and versions for each experiment.

4. Add an *import* statement at the top of your script, e.g. `import vexptoolbox as vx`

### Manual Installation

1. Clone a copy of the *vizard-experiment-toolbox* repository using ```git clone https://github.com/ischtz/vizard-experiment-toolbox.git``` or download using Github's "Download ZIP" functionality behind the "Code" button (upper right).
2. Copy the *vexptoolbox* subfolder to the folder containing your Vizard script
3. Add an *import* statement at the top of your script, e.g. `import vexptoolbox as vx`


## Documentation

A proper documentation website is in the works. Until then, take a look at the *examples* folder, which includes a growing list of example scripts that showcase common functionality. 

There is also a Github repository containing an [example VR experiment implemented using this toolbox](https://github.com/ischtz/proantireach-vizard) (pro-/anti-reaching paradigm), including sample data and analysis examples. 


## Citation

**The manuscript accompanying this project is currently under review and will be linked here after acceptance.**


## License

The code is made available under the MIT license (see LICENSE). It is provided in the hope that it will be useful to others, but without warranties of any kind!

Note: This is an academic open-source project. Neither this toolbox nor its authors are affiliated with WorldViz Inc. or Vizard. 
