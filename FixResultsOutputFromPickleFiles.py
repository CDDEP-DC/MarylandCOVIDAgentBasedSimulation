



import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv

import PostProcessing
import ParameterSet
import Utils
import GlobalModel

modelPopNames = 'ZipCodes'
Model = 'Maryland'  # select model
ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MarylandInt"


endTime = 121
for filename in os.listdir(ParameterSet.ResultsFolder):
    if ".pickle" in filename:
        resultsName = filename[filename.find("_")+1:filename.find(".pickle")]
        print(filename)
        results = Utils.FileRead(ParameterSet.ResultsFolder + "/" + filename)
        print(results)
        
#PostProcessing.WriteAggregatedResults(results,Model,resultsNameP,modelPopNames,RegionalList,HospitalNames,endTime)    
#def WriteAggregatedResults(results,model,resultsName,modelPopNames,RegionalList,HospitalNames=[],endTime=0):
