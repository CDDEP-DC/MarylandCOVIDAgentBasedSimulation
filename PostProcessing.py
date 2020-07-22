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

import time
#import matplotlib.pyplot as plt
#from matplotlib  import cm
import numpy as np
import pandas as pd
import ParameterSet
import Utils

import os

def CompileResults(resultsName,modelPopNames,RegionalList,timeRange):
    
    results = {}
    for tend in timeRange:
        results[tend] = {}
    
    for i in range(0,len(RegionalList)):
        regionVals = Utils.PickleFileRead(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"))
        for tend in timeRange:
            dayVals = regionVals[tend]
            for day in dayVals.keys():
                rdict = dayVals[day]
                results[tend][i]=rdict
        
    return results
    

def WriteParameterVals(resultsName,model,ParameterVals,writefolder=''):

    if writefolder == '':
        writefolder = ParameterSet.ResultsFolder
 
    
    csvFile = writefolder+"/Parameters_"+model+"_"+resultsName+".csv"
    try:
        with open(csvFile, 'w') as f:
            for key in ParameterVals.keys():
                f.write("%s,%s\n" % (key,ParameterVals[key]))
            f.write("\n")

    except IOError:
        print("I/O error")

def WriteAggregatedResults(results,model,resultsName,modelPopNames,RegionalList,HospitalNames=[],endTime=0,writefolder=''):

    # add flag to write regional values
    # add flag to write local values

    print('Writing Results')
    if writefolder == '':
        writefolder = ParameterSet.ResultsFolder
       
    ### Get the results
    maxday = 0
    for d in results.keys():
        daynow = d
        if daynow > maxday:
            maxday = daynow
    #totdays = len(results.keys())
    totdays = maxday
    csvFile = writefolder+"/ResultsByDay_"+model+"_"+resultsName+".csv"
    csvFileLocal = writefolder+"/LocalInfectedByDay_"+model+"_"+resultsName+".csv"
    
    # This goes through the first row of results and gets the regional id - so results can be group by region. If none exists then we just give one set of results        
    regionalvals = []
    localpopvals = []
    numInfList = results[list(results.keys())[0]]
   
    for reg in numInfList.keys():
        rdict = numInfList[reg]
        for rkey in rdict:
            lpdict = rdict[rkey]
            if 'regionalid' in lpdict.keys():
                regionalval = lpdict['regionalid']
                if not regionalval in regionalvals:
                    regionalvals.append(regionalval)
            if 'localpopid' in lpdict.keys():
                localpopval = lpdict['localpopid']
                if not localpopval in localpopvals:
                    localpopvals.append(localpopval)
                    
    ###########################################################################
    # Write the regional data and totals for the main buckets out to disk
    keyvals = ['S','N','I','C','R','D','H','HI','HE','ICU','numTests','numQ','numInfPrev','InfEvtClear','CC']
    colvals = ['Susceptible', 'Incubating', 'Infected', 'Colonized', 'Recovered', 'Dead', 'Hospitalized','NewAdmissions','EDVisits','ICU','Tests','Quarantined','numHousholdQuarantined','InfectiousEventsPrevented','confirmedcases']
    colvaltitles = []
    
    if len(regionalvals) > 1:
        for j in range(0,len(regionalvals)):
            for i in range(0,len(colvals)):
                colvaltitles.append(colvals[i]+"_"+str(regionalvals[j]).encode("ascii",errors="ignore").decode())
        colvaltitles.extend(colvals)        
    else:
        colvaltitles = list(colvals)
    #set up output    
    output = np.empty((totdays,len(colvaltitles)+1),dtype=int)
    
    # now go through the results and add the results as totals to each bucket
    for day in results.keys():
        
        if len(regionalvals) > 1:
            resultdayvals = [0]*(len(colvals)*len(regionalvals)+len(colvals))
        else:
            resultdayvals = [0]*(len(colvals))
        numInfList = results[day]
        for reg in numInfList.keys():
            rdict = numInfList[reg]
            for rkey in rdict:
                lpdict = rdict[rkey]
                regionalval = lpdict['regionalid']
                idx = regionalvals.index(regionalval)
                st = idx*len(colvals)
                totst = (len(regionalvals))*len(colvals)
                keyon = 0
                for i in range(st,st+(len(colvals))):
                    resultdayvals[i]+=lpdict[keyvals[keyon]]
                    keyon+=1
                keyon = 0  
                if len(regionalvals) > 1:  
                    for i in range(totst,totst+(len(colvals))):
                        resultdayvals[i]+=lpdict[keyvals[keyon]]
                        keyon+=1

        output[(day - 1), :] = [day]+resultdayvals
    titles = ['Day']
    titles.extend(colvaltitles)
    
    np.savetxt(csvFile,np.vstack([titles,output]),delimiter=",", fmt='%5s')
    ###########################################################################
    
    # Write the local pop data and totals for I
    
        #set up output    
    output = np.empty((totdays,len(localpopvals)+1),dtype=int)
    
    # now go through the results and add the results as totals to each bucket
    for day in results.keys():
        resultdayvals = [0]*len(localpopvals)
        numInfList = results[day]
        for reg in numInfList.keys():
            rdict = numInfList[reg]
            for rkey in rdict:
                lpdict = rdict[rkey]
                localpopval = lpdict['localpopid']
                idx = localpopvals.index(localpopval)
                resultdayvals[idx]+=lpdict['I']
                    
        output[(day - 1), :] = [day]+resultdayvals
    titles = ['Day']
    for x in range(0,len(localpopvals)):
        titles.append(str(localpopvals[x]).encode("ascii",errors="ignore").decode())
    
    np.savetxt(csvFileLocal,np.vstack([titles,output]),delimiter=",", fmt='%5s')
    ##############################################################################
    if ParameterSet.SaveHospitalData:
        hospstatsnames = ['occupancy','admissions','edvisits','ICU']
    
        HospitalOccupancyByDay = {}
        for day in range(0, endTime + 1):
            hoc = []
            for hsn in hospstatsnames:
                for h in range(0, len(HospitalNames)):
                    hoc.append(0)
            HospitalOccupancyByDay[day] = hoc
        
        for i in range(0,len(RegionalList)):
            if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle"):
                CurrentHospOccList = Utils.PickleFileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
                for key in CurrentHospOccList.keys():
                    tydict = CurrentHospOccList[key]
                    for key2 in tydict.keys():
                        hsdict = tydict[key2]  
                        x = 0
                        for hsn in hospstatsnames: 
                            lpdict = hsdict[hsn]
                            for h in range(0,len(lpdict)):
                                HospitalOccupancyByDay[key][x] += lpdict[h]
                                x += 1
    
        csvFile = writefolder+"/HospitalOccupancyByDay_"+model+"_"+resultsName+".csv"
        try:
            with open(csvFile, 'w') as f:
                f.write("day")
                for hsn in hospstatsnames:
                    for h1 in range(0, len(HospitalNames)):
                        f.write(",%s_%s" % (HospitalNames[h1],hsn))
                f.write("\n")        
                for key in HospitalOccupancyByDay.keys():
                    f.write("%s" % key)
                    for h in range(0, len(HospitalOccupancyByDay[key])):
                        f.write(",%s" % HospitalOccupancyByDay[key][h])
                    f.write("\n")
    
        except IOError:
            print("I/O error")
    
    ############
    csvFileR0 = writefolder+"/R0_"+model+"_"+resultsName+".csv"
    R0Stats = [0]*101   
    for i in range(0,len(RegionalList)):
        if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle"):
            R0StatsList = Utils.PickleFileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle")
            for key in R0StatsList.keys():
                R0Stat = R0StatsList[key]
                for rkey in R0Stat.keys():
                    rvals = R0Stat[rkey]
                    for r in range(0,len(rvals)):
                        R0Stats[r] += rvals[r]
    rnum = 0
    rdenom = 0
    for i in range(0,len(R0Stats)):
        rdenom += R0Stats[i]
        rnum += R0Stats[i]*i     
        
    np.savetxt(csvFileR0,R0Stats,delimiter=",", fmt='%5s')
    