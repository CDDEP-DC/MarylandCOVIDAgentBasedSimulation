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

def WriteAggregatedResults(results,model,resultsName,modelPopNames,RegionalList,HospitalNames=[],endTime=0):

    print('Writing Results')
    totdays = len(results.keys())
    output = np.empty((totdays,14),dtype=int)
    csvFile = ParameterSet.ResultsFolder+"/ResultsByDay_"+model+"_"+resultsName+".csv"

    for day in results.keys():
        sus = 0
        inc = 0
        inf = 0
        col = 0
        rec = 0
        hos = 0
        dead = 0
        R0 = 0
        R0R = 0
        R0HH = 0
        totHI = 0
        totHE = 0
        In = 0
        InR = 0
        InH = 0
        Ai = 0
        totICU = 0
        numInfList = results[day]
        for reg in numInfList.keys():
            rdict = numInfList[reg]
            for rkey in rdict:
                lpdict = rdict[rkey]
                if len(lpdict) > 0:
                    inf += lpdict['I']
                    col += lpdict['C']
                    hos += lpdict['H']
                    totICU += lpdict['ICU']
                    inc += lpdict['N']
                    rec += lpdict['R']
                    sus += lpdict['S']
                    dead += lpdict['D']
                    In += lpdict['In']
                    InR += lpdict['InR']
                    InH += lpdict['InH']
                    Ai += lpdict['Ai']
                    totHI += lpdict['HI']
                    totHE += lpdict['HE']
        
        if Ai > 0:
            R0 = In / Ai
            R0R = InR / Ai
            R0HH = InH / Ai
        output[(day - 1), :] = [day, sus, inc, inf, col, rec, dead, hos,R0,R0R,R0HH,totHI,totHE,totICU]

    titles = ['Day', 'Susceptible', 'Incubating', 'Infected', 'Colonized', 'Recovered', 'Dead', 'Hospitalized','R0','R0R','R0HH','NewAdmissions','EDVisits','ICU']
    
    np.savetxt(csvFile,np.vstack([titles,output]),delimiter=",", fmt='%5s')
    
    
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
    csvFile = ParameterSet.ResultsFolder+"/HospitalOccupancyByDay_"+model+"_"+resultsName+".csv"
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
        csvFile = ParameterSet.ResultsFolder + "/CountyResultsByDay_" + str(i) + "_" + resultsName +".csv"
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