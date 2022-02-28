# load_profiles
A simple way of indexing load profiles for buildings

Steps to get this running:
1. clone this repo
2. Create a python (v3.10) environment with the dependencies listed in requirements.txt
3. Call main.py with the arguments:
	--zip (building zip code)
	--type (NAICS Code)
	--sqft (net square footage of the building)
Example: "python main.py --zip 80016 --type 61 --sqft 20000"
4. Profile will be output as an html visualization and a xlsx to view
