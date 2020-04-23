



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
from ProcessingDataForPresentation import ProcessDataForPresentation as ProcessDataForPresentation
import sys, getopt

import multiprocessing 

def testpbsjobs(i,OutputResultsFolder):
    thisdict = {
        "brand": "Ford",
        "model": "Mustang",
        "year": 1964
    }
    
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str("hello")+str(i)+".pickle"), thisdict)
    
    AgeStats = []
    for j in range(0,100):
        AgeStats.append(random.random())
    csvFileAge = os.path.join(OutputResultsFolder,"Age_test"+str(i)+".csv") 
    np.savetxt(csvFileAge,AgeStats,delimiter=",", fmt='%5s')

def main(argv):
    
    runs, OutputResultsFolder = Utils.ModelFolderStructureSetup(argv)
        
    jobs = []
    for i in range(runs):
        print(i)
        jobs.append(multiprocessing.Process(target=testpbsjobs,args=(i,OutputResultsFolder)))
    
    for j in jobs:
        j.start()
    	
    for j in jobs:  
        j.join()
        
            
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])    