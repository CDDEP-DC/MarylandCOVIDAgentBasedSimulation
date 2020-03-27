

import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv
import pandas as pd

import ParameterSet


def main():

    #### MAKE SURE THESE ARE SET CORREECTLY BEFORE RUNNING --- NEED TO make a function to process, but for now is just hardcoded    
    LocalData = ParameterSet.ResultsFolder + "/MarylandInt"
    FinalLocData = "/mnt/c/Users/eklein8.WIN/OneDrive - Center for Disease Dynamics, Economics & Policy/CDDEP Research Projects (active)/CDC RFK - HAI/CDDEPGlobalAgentModel/Maryland"
    #FinalLocData = ParameterSet.ResultsFolder

    #interventionnames = ['seasonality2','seasonality','distance.10','highcontact','worse','baseline']
    #interventionnames = ['distance.10'] #,'worse']
    interventionnames = ['worsedistance.10']
    interventionruns = [0] * len(interventionnames)
    
    for intnum in range(0,len(interventionnames)):
        print(interventionnames[intnum])
        ### Have to hard code to change process running for now --- need to add function to process different intervention results
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute)
                      
        resultsName = interventionnames[intnum] + "_" + resultsName
            
        ZipToCounty = pd.read_csv('data/Maryland/ZipToCountyMaryland.csv')
        CountyName = ZipToCounty.COUNTYNAME  # county names
        
        for filename in os.listdir(LocalData):
            if interventionnames[intnum] in filename:
                interventionruns[intnum] += 1
       
        Hdata = {}
        Sdata = {}
        numHruns = 0
        numSruns = 0
        for filename in os.listdir(LocalData):
            if interventionnames[intnum] in filename:
                print(filename)
                if "Hospital" in filename:
                    datain = pd.read_csv(LocalData+"/"+filename)
                    
                    #print(datain)
                    # Get ndArray of all column names 
                    columnsNamesArr = datain.columns.values
                    datain["sumoccu"] = datain.iloc[:,1:48].sum(axis=1) 
                    datain["sumadmis"] = datain.iloc[:,48:95].sum(axis=1) 
                    datain["sumed"] = datain.iloc[:,95:142].sum(axis=1) 
                    datain["sumICU"] = datain.iloc[:,142:183].sum(axis=1)
                    datain["count"] = interventionruns[intnum]
                    
                    Hdata[numHruns] = datain
                    print(filename," ",len(Hdata[numHruns].columns.values))
                    if numHruns == 0:
                        HosNames = Hdata[numHruns].columns.values
                    numHruns += 1
                elif "ResultsByDay" in filename:
                    #print(filename)
                    datain = pd.read_csv(LocalData+"/"+filename)
                    datain["count"] = interventionruns[intnum]
                    Sdata[numSruns] = datain
                    if numSruns == 0:
                        StateCompNames = Sdata[numSruns].columns.values
                    numSruns += 1
        
        HosdataVals = [[]] * len(list(Hdata.keys()))
        StatedataVals = [[]] * len(list(Sdata.keys()))
        CountyCompDict = {}
        
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
        #print(len(HosDataMean)," ",len(HosNames))
        HosDataStd = HosdataVals.std(axis=0)
        #HosDataMedian = np.median(HosdataVals,axis=0)
        #HosDataQ1 = np.percentile(HosdataVals,q=25,axis=0)
        #HosDataQ3 = np.percentile(HosdataVals,q=75,axis=0)
    
        StateDataMean = StatedataVals.mean(axis=0)
        StateDataStd = StatedataVals.std(axis=0)
    
        #comment back in when the county data exists
        #CountyDataMean = {}
        #CountyDataStd = {}
        #for i in CountyName:
        #    CountyDataMean[i] = np.row_stack(CountyCompDict[i].mean(axis=0))
        #    CountyDataStd[i] = np.row_stack(CountyCompDict[i].std(axis=0))
    
        #print(CountyDataMean[i].shape)
        
        
        # print
        #print(HosNames)
        #print(HosDataMean[14])
        print("here")
        np.savetxt(FinalLocData+"/HospitalOccupancyAverage_"+resultsName+".csv",
                   np.vstack([HosNames, HosDataMean]), delimiter=",", fmt='%5s')
        np.savetxt(FinalLocData+"/HospitalOccupancyStdDev_"+resultsName+".csv",
                   np.vstack([HosNames, HosDataStd]), delimiter=",", fmt='%5s')
                   
        print("here2")
        #np.savetxt(FinalLocData+"/HospitalOccupancyMedian_"+resultsName+".csv",
        #           np.vstack([HosNames, HosDataMedian]), delimiter=",", fmt='%5s')
        #np.savetxt(FinalLocData+"/HospitalOccupancyIQRQ1_"+resultsName+".csv",
        #           np.vstack([HosNames, HosDataQ1]), delimiter=",", fmt='%5s')
        #np.savetxt(FinalLocData+"/HospitalOccupancyIQRQ3_"+resultsName+".csv",
        #           np.vstack([HosNames, HosDataQ3]), delimiter=",", fmt='%5s')
    
        np.savetxt(FinalLocData+"/StateAverage_"+resultsName+".csv",
                   np.vstack([StateCompNames, StateDataMean]), delimiter=",", fmt='%5s')
        np.savetxt(FinalLocData+"/StateStdDev_"+resultsName+".csv",
                   np.vstack([StateCompNames, StateDataStd]), delimiter=",", fmt='%5s')
        print("here3")
        
        #comment back in when the county data exists
        #randkey = i
        #for j in range(0,len(CountyCompName)):
        #    CountyMeanOut = np.zeros(shape=(CountyDataMean[randkey].shape[0],len(CountyName)))
        #    CountyStdOut = np.zeros(shape=(CountyDataStd[randkey].shape[0],len(CountyName)))
        #    if j == 0:
        #        pass
        #    else:
        #        for i in range(0,len(CountyName)):
        #            CountyMeanOut[:,i] = CountyDataMean[CountyName[i]][:,j]
        #            CountyStdOut[:,i] = CountyDataStd[CountyName[i]][:,j]
        #        np.savetxt(FinalLocData + "/CountyMean_" + str(CountyCompName[j]) + '_' + resultsName + ".csv",
        #                   np.vstack([CountyName, CountyMeanOut]), delimiter=",",
        #                   fmt='%5s')
        #        np.savetxt(FinalLocData + "/CountyStd_" + str(CountyCompName[j]) + '_' + resultsName + ".csv",
        #                   np.vstack([CountyName, CountyStdOut]), delimiter=",",
        #                   fmt='%5s')
        #
        # StatedataVals.to_csv(FinalLocData+"/ResultsByDayTotals_"+resultsName+".csv", index = False)
        # CountydataVals.to_csv(FinalLocData+"/ResultsByDayTotals_"+resultsName+".csv", index = False)
        #
        # HosdataVals = HosdataVals/numHruns
        # StatedataVals = StatedataVals/numSruns
        #
        # CountydataVals.to_csv(FinalLocData+"/HospitalOccupancyAverages_"+resultsName+".csv", index = False)
        # HosdataVals.to_csv(FinalLocData+"/HospitalOccupancyAverages_"+resultsName+".csv", index = False)
        # StatedataVals.to_csv(FinalLocData+"/ResultsByDayAverages_"+resultsName+".csv", index = False)

    
if __name__ == "__main__":
    # execute only if run as a script
    main()