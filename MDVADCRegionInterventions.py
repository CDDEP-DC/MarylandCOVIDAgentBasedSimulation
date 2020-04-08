


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


def main():
    
    generatePresentationVals = 0 # set this to 1 if this is the only run across nodes to complete analysis - set to 0 if this is run across several nodes and use ProcessingDataForPresentation file as standalone afterwards to combine
    runs = 10000 # sets the number of times to run model - results print after each run to ensure that if the job fails the data is still there
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is
    Model = 'MDDCVAregion'  # select model - defines the model type to run
    
    ## Set the interventions to run here - each intervention should have a value for reductions
    #interventionnames = ['distance.9','distance.75','distance.5','distance.25','worse','altdistance.9','altdistance.5']
    #interventionnames = ['distance.95','distance.75','distance.5','distance.25','altdistance.9']
    interventionnames = ['distance.75','distance.50','distance.25','seasonalitydistance.90','seaonalitydistance.50','baseline']
    intervenionreduction1 = [.25,.5,.25,.1,.5,1]
    intervenionreduction2 = [0,0,0,0,0,0,0]
    intervenionreductionSchool = [.25,.5,.25,.1,.5,1]
    
    ## alter values related to transmission in Utils file
    
    ### Below here is model runs and should not be altered
    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
        
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
        
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
        
    OutputResultsFolder = ParameterSet.ResultsFolder + "/MDDCVAregionInt"
    if not os.path.exists(OutputResultsFolder):
        os.makedirs(OutputResultsFolder)
    else:
        for filename in os.listdir(OutputResultsFolder):
            if ".csv" in filename or ".pickle" in filename:
                os.remove(OutputResultsFolder+"/"+filename)
                
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MDDCVAregionInt/Results"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
    else:
        for filename in os.listdir(ParameterSet.ResultsFolder):
            if ".csv" in filename or ".pickle" in filename:
                os.remove(ParameterSet.ResultsFolder+"/"+filename)    
           
    
    GlobalModel.cleanUp(modelPopNames)
    
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
    
    
                      
    for run in range(0,runs):
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        
        Utils.JiggleParameters()
        
        for intnum in range(0,len(interventionnames)):
            
            if 'seasonality' in interventionnames[intnum]:
                endTime = 300
            else:
                endTime = 300
            ParameterSet.Intervention = interventionnames[intnum]
            Utils.JiggleParameters('worse')
            if 'distance' in interventionnames[intnum]:
                ParameterSet.InterventionDate = random.randint(46,50)
                ParameterSet.InterventionEndDate = ParameterSet.InterventionDate + 60
            else:
                ParameterSet.InterventionDate = -1
                ParameterSet.InterventionEndDate = -1
            ParameterSet.InterventionReduction = intervenionreduction1[intnum]
            ParameterSet.InterventionReduction2 = intervenionreduction2[intnum]
            ParameterSet.InterventionReductionSchool = intervenionreductionSchool[intnum]
            
            resultsNameP = interventionnames[intnum] + "_" + resultsName
            
            #ParameterSet.debugmodelevel = ParameterSet.debugerror
            HospitalNames = GlobalModel.RunDefaultModelType(Model, modelPopNames,resultsNameP,endTime,writefolder=OutputResultsFolder)
            
            if generatePresentationVals == 1:
                ProcessDataForPresentation(interventionnames,HospitalNames,readFolder=OutputResultsFolder,writefolder=OutputResultsFolder,resultsName=overallResultsName)
            
if __name__ == "__main__":
    # execute only if run as a script
    main()
