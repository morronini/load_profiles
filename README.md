# load_profiles
A simple way of indexing load profiles for buildings

Steps to get this running:
1. clone this repo
2. Create a python (v3.10) environment with the dependencies listed in requirements.txt
3. Call main.py with the arguments:
	--zip (building zip code)
	--type (NAICS Code)
	--sqft (net square footage of the building)
	--peak (peak yearly kW draw for the building, if known)
	Note: sqft or peak must be passed as an argument. If both are passed, peak will be used instead of sqft.
Example 1: "python main.py --zip 80016 --type 61 --sqft 20000"
Example 2: "python main.py --zip 80220 --type 321 --peak 150"
4. Profile will be output as 4 html visualizations, a json with 4 timeperiods, and an excel spreadsheet
