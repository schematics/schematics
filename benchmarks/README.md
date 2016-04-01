# Schematics benchmark suite

The benchmarks can be run with the asv utility.

## Setup
```
git clone schematics

git checkout master
git checkout development
git checkout benchmark

virtualenv .
. bin/activate
pip install virtualenv
pip install git+https://github.com/spacetelescope/asv

sh benchmarks/run.sh
```
