

import random
import numpy as np
import math
from statistics import mean
import time
import pickle
from datetime import datetime
from datetime import timedelta  
import os
import sys
import csv

import PostProcessing
import ParameterSet
import Utils
import GlobalModel


def main():

    LocalData = ParameterSet.ResultsFolder + "/WuhanFit"
    keyvals = ['endTime','AG04AsymptomaticRate','AG04HospRate','AG517AsymptomaticRate','AG517HospRate','AG1849AsymptomaticRate','AG1849HospRate','AG5064AsymptomaticRate','AG5064HospRate','AG65AsymptomaticRate','AG65HospRate','IncubationTime','totalContagiousTime','hospitalSymptomaticTime','hospTime','EDVisit','preContagiousTime','postContagiousTime','NumInfStart','householdcontactRate','ProbabilityOfTransmissionPerContact','symptomaticContactRateReduction']
    for filename in os.listdir(LocalData):
        print(filename)
        if "WuhanFitVals" in filename and ".csv" not in filename:
            results = Utils.FileRead(LocalData+"/"+filename)
            csvFile = LocalData+"/"+filename+".csv"
            try:
                with open(csvFile, 'w') as f:
                    f.write("run,")
                    for i in range(0,len(keyvals)):
                        f.write(keyvals[i]+",")
                    f.write("\n")        
                    for key in results.keys():
                        dayvals = results[key]
                        f.write("%s" % key)
                        for h in range(0, len(keyvals)):
                            f.write(",%s" % results[key][keyvals[h]])
                        f.write("\n")
        
            except:
                print(sys.exc_info()[0])


    
if __name__ == "__main__":
    # execute only if run as a script
    main()
