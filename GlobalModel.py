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

# System Imports
import numpy as np
import random
import os, shutil
import gc
import math
import time
import pandas as pd
from datetime import datetime  
from datetime import timedelta  
import traceback
import copy

## Model Imports
import ProcessManager
import GlobalLocationSetup
import ParameterSet
import data.ConstructInteractionMatrix
import Utils
import PostProcessing


def getCountyHHsAgesMatrix(dfHH,dfNational57,fip_code,zip_code):
        
    SelectedCounty = dfHH.loc[fip_code,:].values
    SelectedCountyAges = SelectedCounty * dfNational57.values
    
    HHSizeDist = list(SelectedCounty*100)
    HHSizeDist = [round(elem, 2) for elem in HHSizeDist]
    HHSizeAgeDist = {}
    for i in range(len(HHSizeDist)):
        HHSizeAgeDist[i+1] = [round(elem, 2) for elem in SelectedCountyAges[:,i]*100]

    return HHSizeDist, HHSizeAgeDist

def getHospitalData(ModelType,modelvals,popdata):

    #""" Import Adjacency Matrix from the Input Folder """
    
    if int(modelvals['UseHospital']) == 1:
        try:
            ComHosAdj = pd.read_csv(os.path.join("data",ModelType,modelvals['HospitalMatrixFile']), index_col=0)
        except:
            print("Error reading Hospital Matrix file. Please ensure this is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            raise Exception("File Read Error")
            
        #""" Create Adjacency Flow Matrix """
        td = pd.DataFrame(popdata[modelvals['GeographicScale']].copy())
        
        td = td.merge(pd.DataFrame(ComHosAdj), how='left',
                      left_on=modelvals['GeographicScale'], right_index=True) # left join on population > 0
        td = td.set_index(modelvals['GeographicScale'])
        TranCH = np.asarray(td.values)
        
        HosNames = list(ComHosAdj.columns)
        #FacList = pd.read_csv(os.path.join("data",ModelType,modelvals['HospitalNamesFile']))
        
        #HosNames = []
        # This makes sure it runs on all unix systems
        #for i in range(0,len(FacList.HOSPID)):
        #    HosNames.append(FacList.ProviderNames[i].encode("ascii",errors="ignore").decode())
        
    else:
        
        PopulationData = np.asarray(popdata['POPULATION'])
        RegionalNames = np.asarray(popdata[modelvals['RegionalPopName']])
        hospitals = np.unique(np.asarray(popdata[modelvals['RegionalPopName']]))
        
        HospitalInteractionMatrix = np.empty([len(PopulationData), len(hospitals)], np.single)
        for i in range(0, len(PopulationData)):
            for j in range(0, len(hospitals)):
                if RegionalNames[i] == hospitals[j]:
                    HospitalInteractionMatrix[i][j] = (1)
                else:
                    HospitalInteractionMatrix[i][j] = (0)

        TranCH = np.empty([len(PopulationData), len(hospitals)], np.single)
        for i in range(0, len(PopulationData)):
            rowSum = 0.0
            for j in range(0, len(hospitals)):
                rowSum = rowSum + HospitalInteractionMatrix[i, j]
            for j in range(0, len(hospitals)):
                TranCH[i][j] = HospitalInteractionMatrix[i, j] / rowSum
    
        HosNames = []
        for i in range(0,len(hospitals)):
            HosNames.append(hospitals[i])
        
    return TranCH, HosNames
    
def LoadModel(ModelType,modelvals,DiseaseParameters,substate=None):
    print("Loading",ModelType," ...")
    
    PopData = pd.read_csv(os.path.join("data",ModelType,modelvals['PopulationFile']))
    if substate:
        PopData = PopData.loc[PopData['stname'] == substate]
        
    # just check that there are no NAs in the file
    PopData = PopData.dropna(subset=['POPULATION'])
    PopData = PopData[PopData.POPULATION != 0].copy()
    # delete all rows not in ED Matrix
    PopulationData = np.asarray(PopData['POPULATION'])
    PopulationDensity = np.asarray(PopData['POPULATION']/PopData['SQMI'])
    GeoArea = np.asarray(PopData[modelvals['GeographicScale']])
    CountyFIP = np.asarray(PopData['STCOUNTYFP'])
    LPNames = np.asarray(PopData[modelvals['LocalPopName']])
    RegionalNames = np.asarray(PopData[modelvals['RegionalPopName']])
    LongCentroid = np.asarray(PopData['Longitude'])
    LatCentroid = np.asarray(PopData['Latitude'])
    BAProportion = np.asarray(PopData['BAProportion'])
    NursingCareFacilities = np.asarray(PopData['NursingCareFacilities'])
    AssistedLivingFacilities = np.asarray(PopData['AssistedLivingFacilities'])
    LTCF = np.asarray(PopData['LTCF'])
    HealthcareWorkerPercent = np.asarray(PopData['HealthcareWorkerPercent'])
    
    # Now get the hospital data
    HospitalTransitionRate, HospitalColNames = getHospitalData(ModelType,modelvals,PopData)
    
    numpops = len(PopulationData)  # number of HRRs
    print("Found: ", numpops, " Populations, with a total population of ", sum(PopulationData), " (mean:",
          sum(PopulationData) / len(PopulationData), " max:", max(PopulationData), " min:", min(PopulationData),")")

    InteractionMatrix = data.ConstructInteractionMatrix. \
        CreateInteractionMatrix(LongCentroid, LatCentroid, PopulationData)
    
    # Get the data to create the household matrices    
    dfHH = pd.read_csv(os.path.join("data","HHSize_USCounty.csv"), index_col = 'FIPS')
    dfHH = dfHH.loc[:,'1.Person.Household':].div(dfHH.Total, axis=0) # get the percentage
    dfNational57 = pd.read_csv(os.path.join("data","AgeAvgHH_Matrix.csv"), index_col = 0)
        
    
    #county_fips        county_name  PRE.mean  APRIL.mean  MAY.LastWeek.mean
    #print(dfPhoneData)
    if DiseaseParameters['UseCountyLevel'] == 1:
        # Get the county level phonse use data if using
        dfPhoneData = pd.read_csv(os.path.join("data",ModelType,DiseaseParameters['CountyEncountersFile']), index_col = 'county_fips')
        minval = abs(min(dfPhoneData['APRIL.mean']))+1
    
    
    # Now load the global locations
    GlobalLocations = []
    for G in range(0, numpops):
        HHSizeDist, HHSizeAgeDist = getCountyHHsAgesMatrix(dfHH,dfNational57,CountyFIP[G],GeoArea[G])
        
        newdeclinevals = []
        newdeclinevalsLow = []
        
        if DiseaseParameters['UseCountyLevel'] == 1:
            
            premean = dfPhoneData.loc[CountyFIP[G],:].values.tolist()[dfPhoneData.columns.tolist().index('PRE.mean')]+minval
            aprilmean = dfPhoneData.loc[CountyFIP[G],:].values.tolist()[dfPhoneData.columns.tolist().index('APRIL.mean')]+minval
            maylatest = dfPhoneData.loc[CountyFIP[G],:].values.tolist()[dfPhoneData.columns.tolist().index('LastWeek.mean')]+minval
            
            perreduc = (premean-aprilmean)/premean
            perreducLow = perreduc*DiseaseParameters['InterventionReductionPerLow']
            mayopen = ((premean-maylatest)/premean)*.5
            if mayopen < 0:
                mayopen = 0
            #mayopenLow = mayopen*DiseaseParameters['InterventionReductionPerLow']    
            
            #transmissonmodifier=1-math.exp(-premean/DiseaseParameters['pdscale1'])+math.log1p(PopulationDensity[G])/DiseaseParamet ers['pdscale2'] ## pdscale1 = .25  / pdscale2 = 50
            transmissonmodifier = 1/(1+ DiseaseParameters['pdscale1']*math.exp(-1*DiseaseParameters['pdscale2']*PopulationDensity[G]))  ## pdscale1 = .25  / pdscale2 = .001
            
            for i in range(0,DiseaseParameters['InterventionStartReductionDate']):
                newdeclinevals.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier)
                newdeclinevalsLow.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier)
            
            intdays = int(DiseaseParameters['InterventionStartReductionDateCalcDays'])-int(DiseaseParameters['InterventionStartReductionDate'])    
            intredred = perreduc/intdays
            intredredLow = perreducLow/intdays
            intredval = 1
            intredvalLow = 1
            
            for i in range(int(DiseaseParameters['InterventionStartReductionDate']),int(DiseaseParameters['InterventionStartReductionDateCalcDays'])):
                newdeclinevals.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredval)    
                newdeclinevalsLow.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredvalLow)
                intredval -= intredred
                intredvalLow -= intredredLow
            
            for i in range(int(DiseaseParameters['InterventionStartReductionDateCalcDays'])+1,int(DiseaseParameters['InterventionStartEndLift'])):
                newdeclinevals.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredval)    
                newdeclinevalsLow.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredvalLow)
            
            OpenDateNow = (Utils.dateparser("2020-05-18") - DiseaseParameters['startdate']).days    
            opendays = OpenDateNow - (int(DiseaseParameters['InterventionStartEndLift'])+1)
            openinc = (((1-mayopen)-(1-perreduc))/opendays)*.5
            #openincLow = ((1-mayopenLow)-(1-perreducLow))/opendays
            
            for i in range(int(DiseaseParameters['InterventionStartEndLift']+1),OpenDateNow):
                newdeclinevals.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredval)    
                newdeclinevalsLow.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredvalLow)
                intredval+=openinc
                #intredvalLow+=openincLow
            
            RestOfOpenDays = int(DiseaseParameters['InterventionStartEndLiftCalcDays']) - OpenDateNow
            lefttoincrease = (perreduc)*float(DiseaseParameters['InterventionEndPerIncrease']) - intredval
            #lefttoincreaseLow = (perreducLow)*float(DiseaseParameters['InterventionEndPerIncrease']) - intredvalLow
            #print(lefttoincrease,(perreduc),DiseaseParameters['InterventionEndPerIncrease'], intredval)
            if lefttoincrease > 0:
                openinc = lefttoincrease / RestOfOpenDays
            else:
                openinc = 0
            
            for i in range(OpenDateNow+1),int(DiseaseParameters['InterventionStartEndLiftCalcDays']):
                newdeclinevals.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredval)    
                newdeclinevalsLow.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredvalLow)
                intredval+=openinc
                #intredvalLow+=openincLow
                                          
            opendays = (int(DiseaseParameters['finaldate']) - int(DiseaseParameters['InterventionStartEndLiftCalcDays']+1))
            openinc = (1-intredval)/opendays
            openincLow = (1-intredvalLow)/opendays
            for i in range(int(DiseaseParameters['InterventionStartEndLiftCalcDays']+1),int(DiseaseParameters['finaldate'])):
                newdeclinevals.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredval)    
                newdeclinevalsLow.append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*transmissonmodifier*intredvalLow)
                intredval+=openinc
                intredvalLow+=openincLow
                
        else:    
            if DiseaseParameters['AdjustPopDensity']:
                transmissonmodifier = 1/(1+ DiseaseParameters['pdscale1']*math.exp(-1*DiseaseParameters['pdscale2']*PopulationDensity[G]))  ## pdscale1 = .25  / pdscale2 = .001
                for TP in range(0,len(DiseaseParameters['TransProb'])):
                    newdeclinevals.append(DiseaseParameters['TransProb'][TP]*transmissonmodifier)
                    newdeclinevalsLow.append(DiseaseParameters['TransProbLow'][TP]*transmissonmodifier)
            else:                  
                newdeclinevals = DiseaseParameters['TransProb'].copy()
                newdeclinevalsLow = DiseaseParameters['TransProbLow'].copy()

        GL = GlobalLocationSetup.\
            GlobalLocationSetup(G, PopulationData[G], HHSizeDist,HHSizeAgeDist, 
                                DiseaseParameters, LPNames[G],RegionalNames[G],
                                (1-BAProportion[G])+HealthcareWorkerPercent[G],NursingCareFacilities[G]+AssistedLivingFacilities[G]+LTCF[G],newdeclinevals,newdeclinevalsLow)
        GlobalLocations.append(GL)
    print("Loaded Populations")    
    return PopulationData, InteractionMatrix, HospitalTransitionRate, HospitalColNames,GlobalLocations

    

def modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters,substate=None):

    ## Need error check here to make sure that modelpopnames is a valid system name
    #if modelPopNames is None:
    #    modelPopNames = 'region'

    GlobalInteractionMatrix = []

    HospitalTransitionRate = []
    PopulationDensity = []
    
    WuhanCoordDict = {}
    
    GlobalLocations = []
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations = LoadModel(ModelType,modelvals,DiseaseParameters,substate=substate)
    LocationImportationRisk = []
    popsum = sum(PopulationData)
    for i in range(0,len(PopulationData)):
        LocationImportationRisk.append(PopulationData[i]/popsum)     
   
    return PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk


def RunDefaultModelType(ModelType,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder='',startDate=datetime(2020,2,1),fitdates=[],hospitalizations=[],deaths=[],cases=[],fitper=.3,StartInfected=-1):
    
    cleanUp(modelPopNames)
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters)
    
    RegionalList, timeRange, fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,mprandomseed,startDate=startDate,modelPopNames=modelPopNames,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper,StartInfected=StartInfected)
    
    if fitted:
        PostProcessing.WriteParameterVals(resultsName,ModelType,ParameterVals,writefolder)
        results = PostProcessing.CompileResults(resultsName,modelPopNames,RegionalList,timeRange)
        PostProcessing.WriteAggregatedResults(results,ModelType,resultsName,modelPopNames,RegionalList,HospitalNames,endTime,writefolder)    
    
    cleanUp(modelPopNames,len(RegionalList))
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

    return fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases
    
def RunBurnin(ModelType,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder='',startDate=datetime(2020,2,1),fitdates=[],hospitalizations=[],deaths=[],cases=[],fitper=.3):
    
    cleanUp(modelPopNames)
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters)
    
    RegionalList, timeRange, fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,mprandomseed,startDate=startDate,modelPopNames=modelPopNames,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,cases=cases,fitper=fitper,burnin=True)
    
    cleanUp(modelPopNames,len(RegionalList))
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

    return fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases

def RunUSStateForecastModel(ModelType,state,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder='',startDate=datetime(2020,2,1),fitdates=[],hospitalizations=[],deaths=[],fitper=.3):
    
    cleanUp(modelPopNames)
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters,substate=state)
    
    RegionalList, timeRange, fitted = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,mprandomseed,startDate=startDate,modelPopNames=modelPopNames,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper)
    
    if fitted:
        PostProcessing.WriteParameterVals(resultsName,ModelType,ParameterVals,writefolder)
        results = PostProcessing.CompileResults(resultsName,modelPopNames,RegionalList,timeRange)
        PostProcessing.WriteAggregatedResults(results,ModelType,resultsName,modelPopNames,RegionalList,HospitalNames,endTime,writefolder)    
    
    cleanUp(modelPopNames,len(RegionalList))
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

    return fitted

            
def cleanUp(modelPopNames='',lengthnum=1000):
    
    # Cleanup population data
    for i in range(0, lengthnum):
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle"))
        except:
            #print("error removing main model")
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"STATS.pickle"))
        except:
            #print("error removing Stats")
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"AgeStats.pickle"))
        except:
            #print("error removing AgeStats")
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"))
        except:
            #print("error removing RegionStats")
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"HOSPLIST.pickle"))
        except:
            #print("error removing HOSPLIST")
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"))
        except:
            #print("error removing Queue")
            pass
        try:
            os.remove(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"testextra.pickle"))
        except:
            #print("error removing testextra")
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"R0Stats.pickle"))
        except:
            #print("error removing ROstats")
            pass
    