library(tidyverse)
library(data.table)

DATA_FOLDER = "./data"
COMBINED_FNAME = file.path(DATA_FOLDER, "combined.csv")

df = read.csv(COMBINED_FNAME) %>% column_to_rownames("vaersId")

print(table(df$myocarditis, df$covid))
