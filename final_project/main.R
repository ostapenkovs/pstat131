library(tidyverse)

DATA_FOLDER = "./2021VAERSData"
DATA_FNAME = file.path(DATA_FOLDER, "2021VAERSDATA.csv")
SYMPTOMS_FNAME = file.path(DATA_FOLDER, "2021VAERSSYMPTOMS.csv")
VACCINE_FNAME = file.path(DATA_FOLDER, "2021VAERSVAX.csv")

data = read.csv(DATA_FNAME)
symptoms = read.csv(SYMPTOMS_FNAME)
vaccine = read.csv(VACCINE_FNAME)
