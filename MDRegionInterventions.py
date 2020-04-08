


import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv
import pandas as pd

import PostProcessing
import ParameterSet
import Utils
import GlobalModel


def main():
    
    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
        
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
        
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
    
    LocalResultsFolder = ParameterSet.ResultsFolder + "/MDregionInt"
    if not os.path.exists(LocalResultsFolder):
        os.makedirs(LocalResultsFolder)
    else:
        for filename in os.listdir(LocalResultsFolder):
            if ".csv" in filename or ".pickle" in filename:
                os.remove(LocalResultsFolder+"/"+filename)
                
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MDregionInt/Results"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
    else:
        for filename in os.listdir(ParameterSet.ResultsFolder):
            if ".csv" in filename or ".pickle" in filename:
                os.remove(ParameterSet.ResultsFolder+"/"+filename)    
                
    

    runs = 10000
    modelPopNames = 'ZipCodes'
    Model = 'Maryland'  # select model
    GlobalModel.cleanUp(modelPopNames)
    
    #interventionnames = ['seasonality2','seasonality','distance.10','highcontact','worse','baseline']
    #interventionnames = ['distance.10','worse']
    #intervenionreduction1 = [1,.9,.9]
    #intervenionreduction2 = [0,0,0]
    #intervenionreductionSchool = [1,.5,.5]
    #interventionnames = ['distance.9','distance.75','distance.5','distance.25','worse','altdistance.9','altdistance.5']
    #interventionnames = ['distance.95','distance.75','distance.5','distance.25','altdistance.9']
    interventionnames = ['seasonalitydistance.90','seaonalitydistance.5','distance.9','distance.5']
    intervenionreduction1 = [.1,.5,.1,.5]
    intervenionreduction2 = [0,0,0,0]
    intervenionreductionSchool = [.1,.5,.1,.5]
    
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
                endTime = 15
            else:
                endTime = 15
            ParameterSet.Intervention = interventionnames[intnum]
            Utils.JiggleParameters('worse')
            if 'distance' in interventionnames[intnum]:
                ParameterSet.InterventionDate = random.randint(46,50)
                ParameterSet.InterventionEndDate = ParameterSet.InterventionDate + 75
            else:
                ParameterSet.InterventionDate = -1
                ParameterSet.InterventionEndDate = -1
            ParameterSet.InterventionReduction = intervenionreduction1[intnum]
            ParameterSet.InterventionReduction2 = intervenionreduction1[intnum]
            ParameterSet.InterventionReductionSchool = intervenionreductionSchool[intnum]
            resultsNameP = interventionnames[intnum] + "_" + resultsName
            
            #ParameterSet.debugmodelevel = ParameterSet.debugerror
            HospitalNames = GlobalModel.RunDefaultModelType(Model, modelPopNames,resultsNameP,endTime)
            
            interventionruns = [0] * len(interventionnames)
            for filename in os.listdir(ParameterSet.ResultsFolder):
                if interventionnames[intnum] in filename and "HospitalOccupancyByDay" in filename:
                    interventionruns[intnum] += 1
           
            Hdata = {}
            Sdata = {}
            numHruns = 0
            numSruns = 0
            for filename in os.listdir(ParameterSet.ResultsFolder):
                if interventionnames[intnum] in filename:
                    print(filename)
                    if "HospitalOccupancyByDay" in filename:
                        datain = pd.read_csv(ParameterSet.ResultsFolder+"/"+filename)
                        
                        #print(datain)
                        # Get ndArray of all column names 
                        columnsNamesArr = datain.columns.values
                        datain["sumoccu"] = datain.iloc[:,1:len(HospitalNames)].sum(axis=1) 
                        datain["sumadmis"] = datain.iloc[:,len(HospitalNames):(2*len(HospitalNames))].sum(axis=1) 
                        datain["sumed"] = datain.iloc[:,(2*len(HospitalNames)):(3*len(HospitalNames))].sum(axis=1) 
                        datain["sumICU"] = datain.iloc[:,(3*len(HospitalNames)):(4*len(HospitalNames))].sum(axis=1)
                        datain["count"] = interventionruns[intnum]
                        
                        Hdata[numHruns] = datain
                        print(filename," ",len(Hdata[numHruns].columns.values))
                        if numHruns == 0:
                            HosNames = Hdata[numHruns].columns.values
                        numHruns += 1
                    elif "ResultsByDay" in filename:
                        #print(filename)
                        datain = pd.read_csv(ParameterSet.ResultsFolder+"/"+filename)
                        datain["count"] = interventionruns[intnum]
                        Sdata[numSruns] = datain
                        if numSruns == 0:
                            StateCompNames = Sdata[numSruns].columns.values
                        numSruns += 1
            
            HosdataVals = [[]] * len(list(Hdata.keys()))
            StatedataVals = [[]] * len(list(Sdata.keys()))
                        
            n = 0
            for i in Hdata.keys():
                HosdataVals[n] = Hdata[i].values
                n += 1
            HosdataVals = np.array(HosdataVals)
        
            n = 0
            for i in Sdata.keys():
                StatedataVals[n] = Sdata[i].values
                n += 1
            StatedataVals = np.array(StatedataVals)
            
            # # Calculate Means
            HosDataMean = HosdataVals.mean(axis=0)
            HosDataStd = HosdataVals.std(axis=0)
            
            StateDataMean = StatedataVals.mean(axis=0)
            StateDataStd = StatedataVals.std(axis=0)
            
            np.savetxt(LocalResultsFolder+"/HospitalOccupancyAverage_"+interventionnames[intnum] + "_" + overallResultsName+".csv",
                       np.vstack([HosNames, HosDataMean]), delimiter=",", fmt='%5s')
            np.savetxt(LocalResultsFolder+"/HospitalOccupancyStdDev_"+interventionnames[intnum] + "_" + overallResultsName+".csv",
                       np.vstack([HosNames, HosDataStd]), delimiter=",", fmt='%5s')
            
            np.savetxt(LocalResultsFolder+"/StateAverage_"+interventionnames[intnum] + "_" + overallResultsName+".csv",
                       np.vstack([StateCompNames, StateDataMean]), delimiter=",", fmt='%5s')
            np.savetxt(LocalResultsFolder+"/StateStdDev_"+interventionnames[intnum] + "_" + overallResultsName+".csv",
                       np.vstack([StateCompNames, StateDataStd]), delimiter=",", fmt='%5s')
                #except:        
                #    GlobalModel.cleanUp(modelPopNames)
            
if __name__ == "__main__":
    # execute only if run as a script
    main()
