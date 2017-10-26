# Introduction
sicktoolbox-python is an atlasbuggy wrapper for the sicktoolbox library. Using this library, you can interface with SICK LIDARs that can be interfaced with using the standard sicktoolbox library.

# Setup

## Dependencies

sicktoolbox-python depends on Boost, with header files for Python. To install Boost on a linux machine, follow the instructions below.

1. Install libicu-dev for unicode support:
```bash
sudo apt-get install libicu-dev
```
2. Download the latest Boost source from [here](http://www.boost.org/) and unzip the file.
3. Navigate to the unzipped directory and generate the build configuration with Python 3.x support.
```bash
./bootstrap.sh --prefix=boost_output --with-python=python3
```
4. Build the library. If you would like to build in parallel, add -j <n> after install, with n representing the number of cores.
```bash
./b2 install
```

5. Set the BOOST_ROOT environmental variable in your .bashrc to the path to the boost_output directory created when building.
```bash
echo 'export BOOST_ROOT=\path\to\boost_output' >> ~/.bashrc
source ~/.bashrc
```

sicktoolbox-python also depends on sicktoolbox. We will work with a fork of the main sicktoolbox repository.
```bash
git clone https://github.com/AtlasBuggy/sicktoolbox-fork.git
cd sicktoolbox-fork
./configure
make
sudo make install
```
## Installation

Now that we have dependencies setup, we can install sicktoolbox-python. To install, simply do the following:

```bash
mkdir build
./build.sh
```

To add lms200 to your python packages, create a symlink to the lms200 folder in your python installation's site packages. For example, if your python installation is located at /usr/local/lib/python3.5 and you are currently in the sicktoolbox-python folder, run the following.

```bash
sudo ln -s ./lms200 /usr/local/lib/python3.5/site-packages/lms200
```
