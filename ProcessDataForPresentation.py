"""

Copyright (C) 2020  Eili Klein

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
    

"""

import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv
import pandas as pd
import string

def Presentation(interventionnames,ReadFolder,WriteFolder):
    
    interventionruns = [0] * len(interventionnames)
    
    for intnum in range(0,len(interventionnames)):
        print(interventionnames[intnum])
                      
        resultsName = interventionnames[intnum] #+ resultsName
            
        for root, dirs, files in os.walk(".", topdown=False):
            for filename in files:
                if interventionnames[intnum] in filename and "Hospital" in filename:
                    interventionruns[intnum] += 1
       
        Hdata = {}
        Sdata = {}
        Ldata = {}
        Adata = {}
        numHruns = 0
        numSruns = 0
        numLruns = 0
        numAruns = 0
        for root, dirs, files in os.walk(ReadFolder, topdown=False):
            for filename in files:
                if interventionnames[intnum] in filename:
                    #print(filename)
                    if "Age_" in filename:
                        datain = pd.read_csv(os.path.join(root, filename), header=None)
                        datain["count"] = interventionruns[intnum]
                        Adata[numAruns] = datain
                        numAruns += 1
                        
                    
                    if "Hospital" in filename:
                        datain = pd.read_csv(os.path.join(root, filename))
                        
                        #print(datain)
                        # Get ndArray of all column names 
                        columnsNamesArr = datain.columns.values
                        #datain["sumoccu"] = datain.iloc[:,11:57].sum(axis=1) 
                        #datain["sumadmis"] = datain.iloc[:,48:95].sum(axis=1) 
                        #datain["sumed"] = datain.iloc[:,95:142].sum(axis=1) 
                        #datain["sumICU"] = datain.iloc[:,142:183].sum(axis=1)
                        datain["count"] = interventionruns[intnum]
                        
                        Hdata[numHruns] = datain
                        #print(filename," ",len(Hdata[numHruns].columns.values))
                        if numHruns == 0:
                            HosNames = Hdata[numHruns].columns.values
                        numHruns += 1
                    elif "LocalInfectedByDay" in filename:
                        datain = pd.read_csv(os.path.join(root, filename))
                        datain["count"] = interventionruns[intnum]
                        Ldata[numLruns] = datain
                        if numLruns == 0:
                            LocalCompNames = Ldata[numLruns].columns.values
                        numLruns += 1
                    elif "ResultsByDay" in filename:
                        #print(filename)
                        datain = pd.read_csv(os.path.join(root, filename))
                        datain["count"] = interventionruns[intnum]
                        Sdata[numSruns] = datain
                        if numSruns == 0:
                            StateCompNames = Sdata[numSruns].columns.values
                        numSruns += 1
            
        HosdataVals = [[]] * len(list(Hdata.keys()))
        StatedataVals = [[]] * len(list(Sdata.keys()))
        LocaldataVals = [[]] * len(list(Ldata.keys()))
        AgedataVals = [[]] * len(list(Adata.keys()))
        
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
        
        n = 0
        for i in Ldata.keys():
            LocaldataVals[n] = Ldata[i].values
            n += 1
        LocaldataVals = np.array(LocaldataVals)
        
        n = 0
        for i in Adata.keys():
            AgedataVals[n] = Adata[i].values
            n += 1
        AgedataVals = np.array(AgedataVals)
        
        # # Calculate Means
        HosDataMean = HosdataVals.mean(axis=0)
        HosDataStd = HosdataVals.std(axis=0)
        StateDataMean = StatedataVals.mean(axis=0)
        StateDataStd = StatedataVals.std(axis=0)
        LocalDataMean = LocaldataVals.mean(axis=0)
        LocalDataStd = LocaldataVals.std(axis=0)
        AgeDataMean = AgedataVals.mean(axis=0)
        AgeDataStd = AgedataVals.std(axis=0)
        AgeDataMedian = np.median(AgedataVals,axis=0)
        AgeDataQ1 = np.percentile(AgedataVals,q=25,axis=0)
        AgeDataQ3 = np.percentile(AgedataVals,q=75,axis=0)
    
    
        np.savetxt(os.path.join(WriteFolder,"AgeAverage_"+resultsName+".csv"),
                   np.hstack([AgeDataMean, AgeDataStd, AgeDataMedian, AgeDataQ1, AgeDataQ3]), delimiter=",", fmt='%5s')
                
        np.savetxt(os.path.join(WriteFolder,"HospitalOccupancyAverage_"+resultsName+".csv"),
                   np.vstack([HosNames, HosDataMean]), delimiter=",", fmt='%5s')
        np.savetxt(os.path.join(WriteFolder,"HospitalOccupancyStdDev_"+resultsName+".csv"),
                   np.vstack([HosNames, HosDataStd]), delimiter=",", fmt='%5s')
                  
        np.savetxt(os.path.join(WriteFolder,"StateAverage_"+resultsName+".csv"),
                   np.vstack([StateCompNames, StateDataMean]), delimiter=",", fmt='%5s')
        np.savetxt(os.path.join(WriteFolder,"StateStdDev_"+resultsName+".csv"),
                   np.vstack([StateCompNames, StateDataStd]), delimiter=",", fmt='%5s')
        
        np.savetxt(os.path.join(WriteFolder,"LocalAverage_"+resultsName+".csv"),
                   np.vstack([LocalCompNames, LocalDataMean]), delimiter=",", fmt='%5s')
        np.savetxt(os.path.join(WriteFolder,"LocalStdDev_"+resultsName+".csv"),
                   np.vstack([LocalCompNames, LocalDataStd]), delimiter=",", fmt='%5s')
       
