import pandas as pd
import os
import argparse
import plotly.graph_objects as go
import webbrowser





def make_process_dominated_load_profile(naics_code, floor_area, heat_cool_profile, folders):
    # https://info.ornl.gov/sites/publications/files/pub45942.pdf for the daily profile
    mecs_db = pd.read_csv(folders["data"]+"mecs_lookup.csv", index_col=0)
    base_profile = pd.read_csv(folders["data"]+"base_manu_profile.csv")
    wkdy_scaler = [0.5,0.5,0.5,0.5,0.53,0.6,0.65,0.75,0.85,0.98,1,0.97,0.9,
                    0.94,0.97,1,1,0.85,0.73,0.6,0.55,0.5,0.5,0.5]
    wknd_scaler = [0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5]
    matched = False
    for i in range(4):
        if int(str(naics_code)[:(6-i)]) in mecs_db.index.to_list():
            mio_kwh = float(mecs_db.at[int(str(naics_code)[:(6-i)]), "USA (Mio kWh)"])
            mio_sqft = float(mecs_db.at[int(str(naics_code)[:(6-i)]), "USA (Mio SQFT)"])
            if (mio_kwh < 0) or (mio_sqft < 0):
                print("NAICS Code not supported yet. MECS data not good enough")
                raise ValueError
            kwh_per_sqft = mio_kwh/mio_sqft
            matched = True
    if not matched:
        print("NAICS Code not supported yet.")
        raise ValueError
    hours_at_peak_if_flat = sum(wkdy_scaler)*(52*5+1)+sum(wknd_scaler)*(52*2)
    peak_kw = kwh_per_sqft/hours_at_peak_if_flat * floor_area
    base_profile["Electricity kW"] = base_profile["Electricity kW"]*peak_kw
    heat_cool_profile["Electricity kW"] = base_profile["Electricity kW"].to_list()
    return heat_cool_profile


def load_doe_bldg_dict():
    doe_bldg_dict = {  # First element area, second element number of floors
        "Large Office": [498588, 12],
        "Medium Office": [53628, 3],
        "Small Office": [5500, 1],
        "Warehouse": [52045, 1],
        "Stand-alone Retail": [24962, 1],
        "Strip Mall": [22500, 1],
        "Primary School": [73960, 1],
        "Secondary School": [210887, 2],
        "Supermarket": [45000, 1],
        "Quick Service Restaurant": [2500, 1],
        "Full Service Restaurant": [5500, 1],
        "Hospital": [241351, 5],
        "Outpatient Health Care": [40946, 3],
        "Small Hotel": [43200, 4],
        "Large Hotel": [122120, 6],
        "Midrise Apartment": [33740, 4],
    }
    return doe_bldg_dict


def get_load_profile(station, eia_occupancy_type, vint, area, folders, repr_weather_station):
    reference_sqft = load_doe_bldg_dict()[eia_occupancy_type][0]
    profile_scaling_factor = area / reference_sqft
    folder_name = station + "/"
    file_name = "RefBldg"+eia_occupancy_type.replace(" ", "").replace("-", "") + vint + \
                "_v1.3_7.1_" + repr_weather_station + ".csv"
    ref_profile = pd.read_csv(folders["load_profiles"]+folder_name+file_name, index_col=0)
    scaled_profile = pd.DataFrame()
    scaled_profile["Electricity kW"] = ref_profile["Electricity:Facility [kW](Hourly)"]*profile_scaling_factor
    scaled_profile["Natural Gas kW"] = ref_profile["Gas:Facility [kW](Hourly)"]*profile_scaling_factor
    scaled_profile["Unprocessed Date"] = scaled_profile.index.to_list()
    scaled_profile[["Date", "Time"]] = scaled_profile["Unprocessed Date"].str.split("  ", expand=True)
    return scaled_profile


def get_cond_load_profile(station, eia_occupancy_type, vint, area, folders, repr_weather_station):
    reference_sqft = load_doe_bldg_dict()[eia_occupancy_type][0]
    profile_scaling_factor = area / reference_sqft
    folder_name = station + "/"
    file_name = "RefBldg"+eia_occupancy_type.replace(" ", "").replace("-", "") + vint + \
                "_v1.3_7.1_" + repr_weather_station + ".csv"
    ref_profile = pd.read_csv(folders["load_profiles"]+folder_name+file_name, index_col=0)
    scaled_profile = pd.DataFrame()
    scaled_profile["Elec Heating kW"] = ref_profile["Heating:Electricity [kW](Hourly)"]*profile_scaling_factor
    scaled_profile["Gas Heating kW"] = ref_profile["Heating:Gas [kW](Hourly)"]*profile_scaling_factor
    scaled_profile["Cooling kW"] = ref_profile["Cooling:Electricity [kW](Hourly)"]*profile_scaling_factor
    scaled_profile["Unprocessed Date"] = scaled_profile.index.to_list()
    scaled_profile[["Date", "Time"]] = scaled_profile["Unprocessed Date"].str.split("  ", expand=True)
    return scaled_profile


def naics_to_eia_type_map(naics_type, sqft, db):
    naics_type = int(str(naics_type)[:2])
    sqft_separator = {
        "Office": {"Small Office": [0, 10000],
                   "Medium Office": [10000, 100000],
                   "Large Office": [100000, 999999999]},
        "Education": {"Primary School": [0, 100000],
                      "Secondary School": [100000, 999999999]},
        "Health Care": {"Outpatient Health Care": [0, 100000],
                        "Hospital": [100000, 999999999]},
        "Restaurant+Accomodation": {"Quick Service Restaurant": [0, 3500],
                                    "Full Service Restaurant": [3500, 20000],
                                    "Small Hotel": [20000, 80000],
                                    "Large Hotel": [80000, 999999999]}
    }
    try:
        type_unprocessed = db.at[int(naics_type), "EIA"]
        if db.at[int(naics_type), "Post-process with SQFT"]:
            for eia in list(sqft_separator[type_unprocessed].keys()):
                if (sqft >= sqft_separator[type_unprocessed][eia][0]) & \
                        (sqft < sqft_separator[type_unprocessed][eia][1]):
                    type_processed = eia
                    break
        else:
            type_processed = type_unprocessed
        return type_processed
    except KeyError:
        return "This NAICS Type Currently Not Supported"


def get_vintage_from_year_built(year):
    split_years = [1980, 2004]
    vintages = ["Pre1980", "Post1980", "New2004"]
    vintage_new = "Not Found"
    for i in range(len(split_years)):
        if year < split_years[i]:
            vintage_new = vintages[i]
            break
    if vintage_new == "Not Found":
        vintage_new = "New2004"
    #  return vintage_new -- Currently only new building profiles
    return "New2004"


def load_epw_dict():
    epw_dict = {"1A": "1A_USA_FL_MIAMI.epw",
                         "2A": "2A_USA_TX_HOUSTON.epw",
                         "2B": "2B_USA_AZ_PHOENIX.epw",
                         "3A": "3A_USA_GA_ATLANTA.epw",
                         "3B": "3B_USA_NV_LAS_VEGAS.epw",
                         "3C": "3C_USA_CA_SAN_FRANCISCO.epw",
                         "4A": "4A_USA_MD_BALTIMORE.epw",
                         "4B": "4B_USA_NM_ALBUQUERQUE",
                         "4C": "4C_USA_WA_SEATTLE",
                         "5A": "5A_USA_IL_CHICAGO-OHARE.epw",
                         "5B": "5B_USA_CO_BOULDER.epw",
                         "6A": "6A_USA_MN_MINNEAPOLIS.epw",
                         "6B": "6B_USA_MT_HELENA",
                         "7A": "7A_USA_MN_DULUTH",
                         "8A": "8A_USA_AK_FAIRBANKS"}
    return epw_dict


def get_weather_station_from_zip(building_zip):
    zip_to_station = pd.read_csv(folders["data"]+"Zip to Weather Station by Triangulation.csv", index_col=0)
    zip_to_climate_zone = pd.read_csv(folders["data"]+"zip_to_climate_zone.csv", index_col=0)
    station = zip_to_station.at[int(building_zip), "Station"]
    cz = str(zip_to_climate_zone.at[int(building_zip), "number"])+zip_to_climate_zone.at[int(building_zip), "letter"]
    cz_epw = load_epw_dict()[cz]
    return station, cz_epw[:-4]


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()
    # Optional arguments
    parser.add_argument("-z", "--zip", help="Zip Code of the building as an integer", type=int, default=80016)
    parser.add_argument("-t", "--type", help="First 2 digits of the building type code following NAICS schema",
                        type=str, default="61")
    parser.add_argument("-y", "--year", help="Year the building was constructed", type=int, default=2000)
    parser.add_argument("-s", "--sqft", help="Net building square footage", type=float, default=20000)
    parser.add_argument("-v", "--vis", help="Open visualization or not", type=bool, default=True)
    # Print version
    parser.add_argument("--version", action="version", version='Version 1.0')
    # Parse arguments
    arguments = parser.parse_args()
    return arguments


def visualize_profile(df, vis_bool, folders, mode):
    fig = go.Figure()
    if mode == "DoE":
        varlist = ["Electricity kW", "Natural Gas kW"]
    if mode == "MECS":
        varlist = ["Electricity kW"]
    for variable in varlist:
        fig.add_trace(
            go.Scatter(visible=True, line=dict(width=3), name=variable, x=df.index.to_list(), y=df[variable].to_list()))
    fig.update_layout(
        title="Yearly Load Profile",
        xaxis_title="Time (hours)",
        yaxis_title="Load (kW)",
        xaxis=dict(tickmode="array"),
        font=dict(
            family="Courier New, monospace",
            size=18,
        ))
    with open(folders["output"] + "profile.html", "w") as f:
        f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
    return "Successful"


if __name__ == "__main__":
    month = 3 #1,2,3,4,5,6,7,8,9,10,11,12,all
    folder = os.path.dirname(os.path.realpath(__file__)) + "/"
    folders = {
        "base": folder,
        "data": folder + "data/",
        "output": folder + "outputs/",
        "load_profiles": folder + "template_load_profiles/"
    }
    args = parse_arguments()
    naics_to_eia = pd.read_csv(folders["data"]+"naics_to_eia_type_map.csv", index_col=0)
    if int(str(args.type)[:2]) in naics_to_eia.index.to_list():
        eia_type = naics_to_eia_type_map(args.type, args.sqft, naics_to_eia)
        weather_station, repr_weather_station = get_weather_station_from_zip(args.zip)
        vintage = get_vintage_from_year_built(args.year)
        profile_df = get_load_profile(weather_station, eia_type, vintage, args.sqft, folders, repr_weather_station)
        profile_df = profile_df.drop(columns = ["Unprocessed Date", "Date", "Time"])
        mode = "DoE"
    elif str(args.type)[0] == "3":
        eia_type = "Warehouse"
        weather_station, repr_weather_station = get_weather_station_from_zip(args.zip)
        vintage = get_vintage_from_year_built(args.year)
        heat_and_cool_profile_df = get_cond_load_profile(weather_station, eia_type, vintage, args.sqft, folders, repr_weather_station)
        profile_df = make_process_dominated_load_profile(args.type, args.sqft, heat_and_cool_profile_df, folders)
        mode = "MECS"
    else:
        profile_df = pd.DataFrame()
        print("NAICS code note yet supported.")
        raise ValueError
    profile_df.to_excel(folders["output"] + "load_profile_out.xlsx")
    if str(month) != "all":
        profile_df = profile_df.iloc[int(round(month*30.5*24, 0)):int(round(month*30.5*24+7*24, 0))]
    print(visualize_profile(profile_df, args.vis, folders, mode))
