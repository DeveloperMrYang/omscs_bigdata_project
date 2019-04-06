import os
import csv
import pickle
import pyspark
import pandas as pd

from pyspark import SparkConf, SparkContext
from pyspark.sql import SQLContext, Row, Window, functions as F
from pyspark.sql.types import IntegerType, StringType
from pyspark.sql.functions import udf, row_number, col, monotonically_increasing_id
from local_configuration import *
import csv

#----------VITALS------------||-------------------LAB RESULT VALUES------------------------
#HR, SBP, DBP, TEMP, RR, SP02,   Albumin, BUN, Ca, Cre, Na, K,HCO3, Glc, PH, PaC02, Platelets
#    cols = [['heartrate', 'sysbp', 'diasbp', 'tempc', 'resprate', 'spo2', 'glucose'],
#                   ['albumin', 'bun','creatinine', 'sodium', 'bicarbonate', 'platelet', 'inr'],
#                   ['potassium', 'calcium', 'ph', 'pco2', 'lactate']]


def translate(mapping):
    def translate_(col):
        return mapping.get(col)
    return udf(translate_, StringType())



def get_event_key_ids():
    #TODO (for final) aggregate all synonomous variations of each measurement --- SEE INPORTANT CONSIDERATIONS: https://mimic.physionet.org/mimictables/d_items/

    #TODO Finish this section.  There should be two item numbers that map to the same item as described in the link above.   Let's get it mostly right for the draft.

    item_mappings = {}
    item_mappings['211'] = 'HEART_RATE'   #HEART RATE
    item_mappings['220045'] = 'HEART_RATE'  # HEART RATE
    item_mappings['3313'] = 'SBP'  #BP Cuff [Systolic]
    item_mappings['X'] = 'DBP'  #
    item_mappings['X'] = 'TEMP'  #
    item_mappings['X'] = 'RR'  #
    item_mappings['X'] = 'SP02'  #
    item_mappings['3066'] = 'albumin'  #albumin
    item_mappings['227000'] = 'BUN_ApacheIV'  #BUN_ApacheIV
    item_mappings['227001'] = 'BunScore_ApacheIV'  #BunScore_ApacheIV
    item_mappings['1162'] = 'BUN'  # BUN
    item_mappings['225624'] = 'BUN'  #BUN
    item_mappings['44441'] = 'Calcium'  #
    item_mappings['227005'] = 'Creatinine_ApacheIV'
    item_mappings['227006'] = 'CreatScore_ApacheIV'
    item_mappings['4231'] = 'NaCl'
    item_mappings['1535'] = 'Potassium'
    item_mappings['227006'] = 'CreatScore_ApacheIV'

    return item_mappings




def filter_chart_events(spark, orig_chrtevents_file_path, filtered_chrtevents_outfile_path):
    #TAKES ONLY THE RELEVANT ITEM ROWS FROM THE CHARTEVENTS.CSV file
    item_mappings = get_event_key_ids()

    df_chartevents = spark.read.csv(orig_chrtevents_file_path, header=True, inferSchema="false")
    filtered_chartevents = df_chartevents.filter(col('ITEMID').isin(list(item_mappings.keys())))
    filtered_chartevents = filtered_chartevents.withColumn("ITEMNAME", translate(item_mappings)("ITEMID"))


    #TODO join filtered_chartevents with ADMISSIONS.csv on HADMID --- only keep HADMID AND ADMITTIME COLUMNS FROM ADMISSIONS
    #TODO filter out all events where CHARTTIME is greater than 48 hours after ADMITTIME from ADMISSIONS.csv

    #TODO add column that contains the hour the observation occurred after admission  (0 - X)

    #TODO filter out all observations where X > 48  (occurred after initial 48 hours of admission)

    #TODO: REMOVE columns that are not needed (keep CHARTEVENTS cols, ITEMNAME, HOUR_OF_OBS
    with open(filtered_chrtevents_outfile_path, "w+") as f:
        w = csv.DictWriter(f, fieldnames=filtered_chartevents.schema.names)
        w.writeheader()

        for rdd_row in filtered_chartevents.rdd.toLocalIterator():
            w.writerow(rdd_row.asDict())



def aggregate_features_hourly(filtered_chartevents_path):
    df_filtered_chartevents = spark.read.csv(filtered_chartevents_path, header=True, inferSchema="true")





if __name__ == '__main__':
    conf = SparkConf().setMaster("local[4]").setAppName("My App")
    sc = SparkContext(conf=conf)
    spark = SQLContext(sc)
    filtered_chart_events_path = os.path.join(PATH_OUTPUT, 'FILTERED_CHARTEVENTS.csv')
    filter_chart_events(spark, os.path.join(PATH_MIMIC_ORIGINAL_CSV_FILES, 'CHARTEVENTS.csv'), filtered_chart_events_path) # 'CHARTEVENTS.csv'

    #low priority- remove patient admissions that don't have enough data points during 1st 48 hours of admission  - determine "enough" may need to look at other code

    #filter out any events that are not within the 1st 48 hours of an admission

    #create hourly average for each feature, for each patient-admission
    #TODO GROUP BY HADMID, FEATURE_NAME AVERAGE EACH FEATURE BY HOUR
    #fill foward data to hours that have missing data

    #standardize each feature as in the paper  -- in their preprocess.py this is what they did:  (values - min_feat_value) / (95thpercentile - min_value)   from their preprocessing.py:  dfs[idx][c] = (dfs[idx][c]-dfs[idx][c].min() )/ (dfs[idx][c].quantile(.95) - dfs[idx][c].min())

    #for each admission, for each hourly bin, construct feature vector

    #write feature file with list of tuple (patientid.hadmid, list patient-admission sequences 48 long each)
