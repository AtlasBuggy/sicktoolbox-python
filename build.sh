#!/bin/sh

cd build
cmake ..
make
cp sicktoolbox.so ../lms200
cd ..
