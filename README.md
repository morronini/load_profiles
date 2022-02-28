# load_profiles
A simple way of indexing load profiles for buildings

Steps to get this running:
1. clone this repo
2. Create a python (v3.10) environment with the dependencies listed in requirements.txt
3. Call main.py with the arguments:
	--zip (building zip code)
	--type (first 2 digits of the NAICS Code)
	--year (year of building construction, this is currently not used)
	--sqft (net square footage of the building)
Example: "python main.py --zip 80016 --type 61 --year 2005 --sqft 20000"
4. Profile will be output as an html graph and a xlsx to view
