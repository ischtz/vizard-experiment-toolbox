## vexptoolbox: A Python toolbox for VR behavioral experiments using Vizard

The *vexptoolbox* package aims to help researchers in implementing common tasks in behavioral experiments using the WorldViz Vizard VR platform. Current features include randomized, trial-based experimental designs, straightforward storing of result data to standardized file formats, and built-in recording of eye tracking and motion tracking data. The code supports Vizard 6 (based on Python 2.7) and Vizard 7 (based on Python 3). 

This project began as a collection of common functionality that we encountered frequently when implementing behavioral VR experiments at [the Giessen University Perception and Action Lab](https://www.uni-giessen.de/fbz/fb06/psychologie/abt/allgemeine-psychologie/wh). It is a work in progress - please feel free to report any bugs you find or feature suggestsions using the Issues tool or provide a Pull Request! A manuscript describing this toolbox is currently in preparation and will be linked here after peer-review. 

## Installation

Currently, the toolbox can be added to a Vizard script as follows: 
- Clone or download this repository
- Copy the *vexptoolbox* subfolder to the folder containing your Vizard script
- Add an *import* statement at the top of your script, e.g. `import vexptoolbox as vx`

We plan to make the package available on PyPI upon the first full release, which would also allow installation using the Vizard package manager.


## Documentation

A proper documentation website is in the works. Until then, take a look at the *examples* folder, which includes a growing list of example scripts that showcase common functionality. 

There is also a Github repository containing an [example VR experiment implemented using this toolbox](https://github.com/ischtz/proantireach-vizard) (pro-/anti-reaching paradigm), including sample data and analysis examples. 




## License

The code is made available under the MIT license (see LICENSE). It is provided in the hope that it will be useful to others, but without warranties of any kind!

Note: This is an academic open-source project. Neither this toolbox nor its authors are affiliated with WorldViz Inc. or Vizard. 
