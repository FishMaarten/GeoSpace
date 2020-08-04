# GeoSpace
Author: Maarten Fish


### Web application to plot locations in Flanders

### How to install:
- Change directory to projects folder
- $git clone https://github.com/FishMaarten/GeoSpace.git
- Change directory to /GeoSpace

### Getting started:
- Create and activate a new virtual environment
  - $python3 -m venv venv
  - $source venv/bin/activate
- $pip install -r requirements.txt
- Populate data, run SubScrape.py in /data  
(this will download and subdivide k15 to match the lookup)
- $export FLASK_ENV=development
- $export FLASK_APP=geospace.py

### "flask run" to get started
