# -----------------------------------------------------------------------------
# PostProcessing.py extracts results
# -----------------------------------------------------------------------------
import time
#import matplotlib.pyplot as plt
#from matplotlib  import cm
import numpy as np
import pandas as pd
import ParameterSet
import Utils

import os

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
       
    
    ### Get the age stats
    csvFileAge = os.path.join(writefolder,"Age_"+model+"_"+resultsName+".csv")

    AgeStats = [0]*15
    for i in range(0,len(RegionalList)):
        if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "AgeStats.pickle"):
            AgeStatsList = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "AgeStats.pickle")
            for key in AgeStatsList.keys():
                AgeStat = AgeStatsList[key]
                for rkey in AgeStat.keys():
                    rvals = AgeStat[rkey]
                    aon = 0
                    for agekey in rvals.keys():
                        avals = rvals[agekey]
                        for r in range(0,len(avals)):
                            AgeStats[aon] += avals[r]
                            aon+=1
    
    np.savetxt(csvFileAge,AgeStats,delimiter=",", fmt='%5s')
    
    ### Get the results
    totdays = len(results.keys())
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
    keyvals = ['S','N','I','C','R','D','H','HI','HE','ICU']
    colvals = ['Susceptible', 'Incubating', 'Infected', 'Colonized', 'Recovered', 'Dead', 'Hospitalized','NewAdmissions','EDVisits','ICU']
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
        resultdayvals = [0]*(len(colvals)*len(regionalvals)+len(colvals))
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
            CurrentHospOccList = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
            #print(CurrentHospOccList)
            
            
            for key in CurrentHospOccList.keys():
                tydict = CurrentHospOccList[key]
                for key2 in tydict:
                    hsdict = tydict[key2]  
                    x = 0
                    for hsn in hospstatsnames: 
                        lpdict = hsdict[hsn]
                        for h in range(0,len(lpdict)):
                            HospitalOccupancyByDay[key][x] += lpdict[h]
                            x += 1

    # print(HospitalOccupancyByDay)
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


def WriteAggregatedCountyResults(results,model,resultsName):

    # reattach zipcodes
    MDPop = pd.read_csv('data/Maryland/MDZipCentroidPop.csv')
    MDPop = MDPop.dropna(subset=['POPULATION'])
    MDPop = MDPop[MDPop.POPULATION != 0].copy()
    zipnames = np.asarray(MDPop['ZIP_CODE'])

    # attach zipcode ot county
    ZipToCounty = pd.read_csv('data/Maryland/ZipToCountyMaryland.csv')
    ZipCodes = ZipToCounty.ZIP             # zipcodes
    CountyName = ZipToCounty.COUNTYNAME     # county names
    Fips = ZipToCounty.STCOUNTYFP

    CountyToZipDict = dict.fromkeys(CountyName)
    for i in range(0,len(ZipCodes)):
        CountyToZipDict[CountyName[i]] = []
    for i in range(0, len(ZipCodes)):
        CountyToZipDict[CountyName[i]].append(ZipCodes[i])

    # find unique counties and store as keys
    CountyToFips = {}
    for i in range(0, len(CountyName)):
        fips = Fips[i]
        if fips not in CountyToFips.keys():
            CountyToFips[CountyName[i]] = fips

    countyOut = dict.fromkeys(CountyToZipDict.keys())
    for i in CountyToZipDict.keys():
        print('Writing results for ' + i)
        totdays = len(results.keys())
        output = np.zeros((totdays, 8), dtype=int)
        dailyOut = dict.fromkeys(results.keys())
        for day in results.keys():
            sus = 0
            inc = 0
            inf = 0
            col = 0
            rec = 0
            hos = 0
            dead = 0
            numInfList = results[day]
            for reg in numInfList.keys():
                rdict = numInfList[reg]
                for rkey in rdict:
                    if zipnames[rkey - 1] in CountyToZipDict[i]:
                        lpdict = rdict[rkey]
                        if len(lpdict) > 0:
                            inf += lpdict['I']
                            col += lpdict['C']
                            hos += lpdict['H']
                            inc += lpdict['N']
                            rec += lpdict['R']
                            sus += lpdict['S']
                            dead += lpdict['D']
            output[(day - 1), :] = [day, sus, inc, inf, col, rec, dead, hos]
            dailyOut[day] = {'S': sus, 'N': inc, 'I': inf, 'C': col, 'R': rec, 'D': dead, 'H': hos}
        countyOut[i] = dailyOut
        csvFile = writefolder + "/CountyResultsByDay_" + str(i) + "_" + resultsName +".csv"
        titles = ['Day', 'Susceptible', 'Incubating', 'Infected', 'Colonized',
                  'Recovered', 'Dead','Hospitalized']
        np.savetxt(csvFile, np.vstack([titles, output]), delimiter=",", fmt='%5s')

    # print(countyOut)

    jsonOut = {}
    for day in results.keys():
        for county in countyOut.keys():
            if day not in jsonOut:
                jsonOut[day] = {}
            jsonOut[day] = {**jsonOut[day], **{CountyToFips[county] : countyOut[county][day]}}

    print(jsonOut)

    pass