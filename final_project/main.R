library(tidyverse)
library(plyr)
library(data.table)

DATA_FOLDER = "./2021VAERSData"
DATA_FNAME = file.path(DATA_FOLDER, "2021VAERSDATA.csv")
SYMPTOMS_FNAME = file.path(DATA_FOLDER, "2021VAERSSYMPTOMS.csv")
VACCINE_FNAME = file.path(DATA_FOLDER, "2021VAERSVAX.csv")

data = read.csv(DATA_FNAME)
symptoms = read.csv(SYMPTOMS_FNAME)
vaccine = read.csv(VACCINE_FNAME)

myo_indices = sapply(symptoms[c("SYMPTOM1", "SYMPTOM2", "SYMPTOM3", "SYMPTOM4", "SYMPTOM5")],
                     grep, pattern="myocarditis", ignore.case=TRUE) %>% Reduce(f=union)
symptoms = symptoms[myo_indices, ] %>% copy()
symptoms = symptoms[!duplicated(symptoms$VAERS_ID), ] %>% copy()

vaccine = vaccine[vaccine$VAX_TYPE == "COVID19", ] %>% copy()
