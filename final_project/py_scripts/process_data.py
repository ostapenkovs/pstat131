# %%
# Libraries
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# %%
# Helper
def flatten_iterable(xs):
    res = []
    def loop(ys):
        for i in ys:
            if isinstance(i, list) or isinstance(i, np.ndarray):
                loop(i)
            else:
                res.append(i)
    loop(xs)
    return res

# %%
# Constants
DATA_FOLDER = "../data/unprocessed/"
DATA_FNAME = os.path.join(DATA_FOLDER, "2021VAERSDATA.csv")
SYMPTOMS_FNAME = os.path.join(DATA_FOLDER, "2021VAERSSYMPTOMS.csv")
VACCINE_FNAME = os.path.join(DATA_FOLDER, "2021VAERSVAX.csv")

# %%
# Format DATA dataframe
# Read in df
dat = pd.read_csv(DATA_FNAME, encoding="latin-1", low_memory=False)

# Read in US state information to map between state abbreviation and US region
states = pd.read_csv('https://raw.githubusercontent.com/cphalpert/census-regions/master/us%20census%20bureau%20regions%20and%20divisions.csv')
state_to_region_map = dict(states[["State Code", "Region"]].values)

# Find out which columns are mostly empty
prop_empty = (dat.isna().sum() / len(dat))

# Drop columns which are more than 50% empty
dat = dat.drop(labels=prop_empty[prop_empty > 0.5].index.tolist(), axis=1)

# Map states to region (unknown states become NaN) and drop state column
dat["REGION"] = dat["STATE"].apply(
    lambda x: state_to_region_map[x.upper()] if str(x).upper() in state_to_region_map.keys() else np.nan)
dat = dat.drop("STATE", axis=1)

# Convert RECVDATE (date of receiving incident report) and ONSET_DATE (date of symptom(s) onset) to datetime objects
dat["RECVDATE"], dat["ONSET_DATE"] = pd.to_datetime(dat["RECVDATE"]), pd.to_datetime(dat["ONSET_DATE"])

# Create new derived column representing time between incident report reception and symptomatic onset
dat["RECEIVED MINUS ONSET"] = dat["RECVDATE"] - dat["ONSET_DATE"]
dat["RECEIVED MINUS ONSET"] = dat["RECEIVED MINUS ONSET"].dt.days

# Drop all unnecessary time-related columns as we now have all information we need from those 4
dat = dat.drop(labels=["RECVDATE", "VAX_DATE", "ONSET_DATE", "TODAYS_DATE"], axis=1)

# Drop redundant column representing age in months
dat = dat.drop("CAGE_YR", axis=1)

# Replace "U" value in SEX column with NaN
dat["SEX"] = dat["SEX"].replace("U", np.nan)

# Drop SYMPTOM_TEXT column (we have symptom information derived from this column in another dataframe)
dat = dat.drop("SYMPTOM_TEXT", axis=1)

# Replace "U" value in RECOVD column with NaN
dat["RECOVD"] = dat["RECOVD"].replace("U", np.nan)

# Replace "UNK" value in V_ADMINBY column with NaN
dat["V_ADMINBY"] = dat["V_ADMINBY"].replace("UNK", np.nan)

# Drop FORM_VERS column which is not useful
dat = dat.drop("FORM_VERS", axis=1)

# Convert all values in OTHER_MEDS column to lowercase and convert na-type strings to NaN
dat["OTHER_MEDS"] = dat["OTHER_MEDS"].apply(lambda x: x.lower() if pd.notna(x) else np.nan)
dat["OTHER_MEDS"] = dat["OTHER_MEDS"].replace(
    ['n/a', 'na', 'no', 'none', 'none known', 'none reported',
    'none.', 'not known', 'unk', 'unknown', ''], np.nan)

# Replace multiple ways of saying multivitamin with the same word
dat["OTHER_MEDS"] = dat["OTHER_MEDS"].replace(
    ["prenatal vitamins", "multi vitamin", "vitamins", 
    "prenatal vitamin", "multi-vitamin", "multivitamins"], "multivitamin")

# Map top 20 most common medications to a unique numeric value
# NaN (not medicated) will be 0; some other uncommon medications will be 1
common_meds = dat["OTHER_MEDS"].value_counts().head(20).index.tolist()
med_map = dict(zip(common_meds, list(range(2, len(common_meds)+2))))
med_map[np.nan] = 0
dat["OTHER_MEDS"] = dat["OTHER_MEDS"].apply(lambda x: med_map[x] if x in med_map.keys() else 1)

# Convert all values in HISTORY column to lowercase and convert na-type strings to NaN
# Pull first value of patient's history, which is separated by commas
dat["HISTORY"] = dat["HISTORY"].apply(lambda x: x.lower() if pd.notna(x) else np.nan)
dat["HISTORY"] = dat["HISTORY"].apply(lambda x: x.split(",")[0] if pd.notna(x) else np.nan)
dat["HISTORY"] = dat["HISTORY"].replace(
    ['n/a', 'na', 'no', 'none', 'none known', '', 
    'none reported', 'none.', 'not known', 'unk', 'unknown'], np.nan)

# Replace multiple ways of saying hypertension with the same word
dat["HISTORY"] = dat["HISTORY"].replace("high blood pressure", "hypertension")

# Replace values containing comments with NaN
dat["HISTORY"] = dat["HISTORY"].apply(lambda x: np.nan if (pd.notna(x) and "comment" in x) else x)

# Map top 20 most common histories to a unique numeric value
# NaN (no / unknown history) will be 0; some other uncommon history will be 1
common_hist = dat["HISTORY"].value_counts().head(20).index.tolist()
hist_map = dict(zip(common_hist, list(range(2, len(common_hist)+2))))
hist_map[np.nan] = 0
dat["HISTORY"] = dat["HISTORY"].apply(lambda x: hist_map[x] if x in hist_map.keys() else 1)

# Drop rows with any NaN values
dat = dat.dropna(how="any", axis=0)

# Map REGION to numeric value
region_types = dat["REGION"].value_counts().index.tolist()
region_map = dict(zip(region_types, list(range(1, len(region_types)+1))))
dat["REGION"] = dat["REGION"].apply(lambda x: region_map[x])

# Map V_ADMINBY to numeric value
admin_types = dat["V_ADMINBY"].value_counts().index.tolist()
admin_map = dict(zip(admin_types, list(range(1, len(admin_types)+1))))
dat["V_ADMINBY"] = dat["V_ADMINBY"].apply(lambda x: admin_map[x])

# Rename columns
dat.columns = ["vaersId", "age", "sex", "recovered", "deltaOnset", "adminBy", "otherMeds", "history", "region", "deltaReceived"]

# Write to csv
dat.to_csv("../data/processed/processed_data.csv", index=False)

# %%
dat

# %%
# Format VAX dataframe
# Read in df
vax = pd.read_csv(VACCINE_FNAME, encoding="latin-1", low_memory=False)

# Pull only the useful columns
vax = vax[["VAERS_ID", "VAX_TYPE", "VAX_MANU", "VAX_ROUTE", "VAX_SITE"]]

# Convert all values in VAX_TYPE column to lowercase and convert na-type strings to NaN
vax["VAX_TYPE"] = vax["VAX_TYPE"].apply(lambda x: x.lower() if pd.notna(x) else np.nan)
vax = vax.replace(["unk", "unknown manufacturer"], np.nan)

# Convert all values in VAX_MANU column to lowercase and clean up names
vax["VAX_MANU"] = vax["VAX_MANU"].apply(lambda x: x.lower().split("\\")[0] if pd.notna(x) else np.nan)

# Drop rows with any NaN values
vax = vax.dropna(how="any", axis=0)

# Make binary column representing presence of COVID vaccine
vax["COVID"] = vax["VAX_TYPE"].apply(lambda x: 1 if x=="covid19" else 0)

# Remap VAX_TYPE and VAX_MANU columns to numeric
vax_types = vax["VAX_TYPE"].value_counts().index.tolist()
vax_map = dict(zip(vax_types, list(range(1, len(vax_types)+1))))
vax["VAX_TYPE"] = vax["VAX_TYPE"].apply(lambda x: vax_map[x])

manu_types = vax["VAX_MANU"].value_counts().index.tolist()
manu_map = dict(zip(manu_types, list(range(1, len(manu_types)+1))))
vax["VAX_MANU"] = vax["VAX_MANU"].apply(lambda x: manu_map[x])

# Rename columns
vax.columns = ["vaersId", "vaxType", "vaxManu", "vaxRoute", "vaxSite", "covid"]

# Write to csv
vax.to_csv("../data/processed/processed_vax.csv", index=False)

# %%
vax

# %%
# Format SYMPTOMS dataframe
# Read df
sym = pd.read_csv(SYMPTOMS_FNAME, encoding="latin-1", low_memory=False)

# Keep only useful columns (various symptoms) and combine into a single list of symptoms
sym["combined"] = sym[["SYMPTOM1", "SYMPTOM2", "SYMPTOM3", "SYMPTOM4", "SYMPTOM5"]].values.tolist()
sym = sym[["VAERS_ID", "combined"]]

# Get all symptoms for each VAERS_ID and get rid of none type symptoms
# Keeping max 5 symptoms per VAERS ID
sym = pd.DataFrame(sym.groupby("VAERS_ID")["combined"].apply(sum))
sym["combined"] = sym["combined"].apply(lambda x: [y.lower() for y in x if y not in [np.NaN, ""]][:5])

# Identify which VAERS IDs are involved in myocarditis symptoms
sym["myocarditis"] = sym["combined"].apply(lambda x: int(bool([y for y in x if "myocarditis" in y])))

# Get rid of rows with no symptoms remaining
sym = sym[sym["combined"].str.len() > 0].copy()

# Remap combined column list values to numeric
symptom_types = list(set(flatten_iterable(sym["combined"].values)))
symptom_map = dict(zip(symptom_types, list(range(1, len(symptom_types)+1))))
sym["combined"] = sym["combined"].apply(lambda x: [symptom_map[y] for y in x])

# Explode column of lists into multiple columns of values
temp = pd.DataFrame(sym["combined"].tolist(), index=sym.index)
temp = temp.fillna(value=0)
temp.columns = ["s1", "s2", "s3", "s4", "s5"]

# Combine ordinal encoded symptoms with myocarditis indicator (binary) column
sym = pd.concat([temp, sym["myocarditis"]], axis=1)

# Rename index
sym.index.names = ["vaersId"]

# Write to csv
sym.to_csv("../data/processed/processed_symptoms.csv")

# %%
sym

# %%
# Pull only information from vax DF which could be sensibly used given we need to get rid of duplicates
vax = pd.DataFrame(vax.groupby("vaersId")["covid"].apply(sum))

# We make a single column vax DF which represents number of Covid vaccines received
vax = vax.reset_index()
vax.columns = ["vaersId", "nCovidVax"]

# %%
# Merge all three dataframes together, combining X (features) and y (target)
sigma = dat.merge(vax, on="vaersId").merge(sym.reset_index(), on="vaersId")

# %%
sigma

# %%
# Write df to csv
sigma.to_csv("../data/processed/combined.csv", index=False)


