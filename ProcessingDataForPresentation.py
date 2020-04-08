

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


def ProcessDataForPresentation(interventionnames,HospitalNames=[],readFolder='.',writefolder='',resultsName=''):

    if writefolder == '':
        writefolder = ParameterSet.ResultsFolder
        
    interventionruns = [0] * len(interventionnames)
    if resultsName == '':
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute)
    
    for intnum in range(0,len(interventionnames)):
        ### Have to hard code to change process running for now --- need to add function to process different intervention results
       
        foundhospnames = 0
        for root, dirs, files in os.walk(".", topdown=False):
            for filename in files:
                if interventionnames[intnum] in filename and "HospitalOccupancyByDay_" in filename:
                    interventionruns[intnum] += 1
                    if len(HospitalNames) == 0:
                        if foundhospnames == 0:
                            datain = pd.read_csv(ParameterSet.ResultsFolder+"/"+filename)
                            HospitalNames = datain.columns.values
                            foundhospnames = 1
       
        Hdata = {}
        Sdata = {}
        numHruns = 0
        numSruns = 0

        
        for root, dirs, files in os.walk(readFolder, topdown=False):
            for filename in files:
                if "_" + interventionnames[intnum] + "_" in filename:
                    
                    if "HospitalOccupancyByDay_" in filename:
                        datain = pd.read_csv(os.path.join(root, filename))
                        #print(os.path.join(root, filename))
                        # Get ndArray of all column names 
                        columnsNamesArr = datain.columns.values
                        datain["sumoccu"] = datain.iloc[:,1:len(HospitalNames)].sum(axis=1) 
                        datain["sumadmis"] = datain.iloc[:,len(HospitalNames):(2*len(HospitalNames))].sum(axis=1) 
                        datain["sumed"] = datain.iloc[:,(2*len(HospitalNames)):(3*len(HospitalNames))].sum(axis=1) 
                        datain["sumICU"] = datain.iloc[:,(3*len(HospitalNames)):(4*len(HospitalNames))].sum(axis=1)
                        datain["count"] = interventionruns[intnum]
                        Hdata[numHruns] = datain
                        if numHruns == 0:
                            HosNames = Hdata[numHruns].columns.values
                        numHruns += 1
                    elif "ResultsByDay_" in filename:
                        #print(filename)
                        datain = pd.read_csv(os.path.join(root, filename))
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
        HosDataMean = np.array(HosdataVals.mean(axis=0))
        HosDataStd = np.array(HosdataVals.std(axis=0))
    
        n = 0
        for i in Sdata.keys():
            StatedataVals[n] = Sdata[i].values
            n += 1
        StatedataVals = np.array(StatedataVals)
        StateDataMean = np.array(StatedataVals.mean(axis=0))
        StateDataStd = np.array(StatedataVals.std(axis=0))

        HosSeries = HosNames[:,None].transpose()
        StateSeries = StateCompNames[:,None].transpose()

        np.savetxt(writefolder+"/HospitalOccupancyAverage_"+interventionnames[intnum] + "_" + resultsName+".csv",
                   np.vstack((HosSeries, HosDataMean)), delimiter=",", fmt='%5s')
        np.savetxt(writefolder+"/HospitalOccupancyStdDev_"+interventionnames[intnum] + "_" + resultsName+".csv",
                   np.vstack((HosSeries, HosDataStd)), delimiter=",", fmt='%5s')
        
        np.savetxt(writefolder+"/StateAverage_"+interventionnames[intnum] + "_" + resultsName+".csv",
                   np.vstack((StateSeries, StateDataMean)), delimiter=",", fmt='%5s')
        np.savetxt(writefolder+"/StateStdDev_"+interventionnames[intnum] + "_" + resultsName+".csv",
                   np.vstack((StateSeries, StateDataStd)), delimiter=",", fmt='%5s')

        print('File Writing for Presentation Completed')

if __name__ == "__main__":
    # execute only if run as a script
    ProcessDataForPresentation(['baseline'])