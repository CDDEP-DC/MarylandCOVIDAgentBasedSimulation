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
        print("Using County Level Data")
    
    # Now load the global locations
    GlobalLocations = []
    for G in range(0, numpops):
        HHSizeDist, HHSizeAgeDist = getCountyHHsAgesMatrix(dfHH,dfNational57,CountyFIP[G],GeoArea[G])
        
        newdeclinevals = []
        newdeclinevalsLow = []
        
        if DiseaseParameters['UseCountyLevel'] == 1:
            
            countyrows = dfPhoneData.loc[CountyFIP[G],:]
            visitrate = countyrows.iloc[:,dfPhoneData.columns.tolist().index('daily_visitation_diff')].values.tolist()
            
            unacaststdate = Utils.dateparser('2020-02-24')
            day_count = (unacaststdate - DiseaseParameters['startdate']).days
            
            TransProbC = []
            TransProbCLow = []
            for i in range(0,day_count):
                TransProbC.append(DiseaseParameters['TransProb'][i])
                TransProbCLow.append(DiseaseParameters['TransProbLow'][i])
            
            lastseven = []
            for i in range(0,len(visitrate)):
                #DiseaseParameters['TransProb_AH'].append((1-1/(1+0.4*math.exp(-float(ahvals[i])*.1)))*probtransscale)
                #DiseaseParameters['TransProb_intnumval'].append(intnumval[i])
                day_count+=1
                transprobval = DiseaseParameters['TransProb_AH'][day_count]*(1+float(visitrate[i])+DiseaseParameters['TransProb_intnumval'][day_count])            
                if transprobval < .001:
                    transprobval = .001
                transprobvallow = transprobval*.5
                transprobvalhigh = (transprobval - transprobvallow*.4)/.6
                TransProbC.append(transprobvalhigh)
                TransProbCLow.append(transprobvallow)
                if i >= (len(visitrate)-7):
                    lastseven.append(visitrate[i])
                unacaststdate += timedelta(days=1)   
                
            lson = 0
            lastval = 0
            day_count+=1
            while unacaststdate < Utils.dateparser('2021-03-01'):
                unacaststdate += timedelta(days=1)   
                transprobval = DiseaseParameters['TransProb_AH'][day_count]*(1+float(lastseven[lson])+DiseaseParameters['TransProb_intnumval'][day_count])            
                lastval = lastseven[lson]
                transprobvallow = transprobval*.5
                transprobvalhigh = (transprobval - transprobvallow*.4)/.6
                TransProbC.append(transprobvalhigh)
                TransProbCLow.append(transprobvallow)
                if lson >= (len(lastseven)-1):
                    lson = 0
                else:
                    lson+=1
                day_count+=1
                
            delta = lastval/15/2
            while day_count < len(DiseaseParameters['TransProb_AH']):
                unacaststdate += timedelta(days=1)
                if unacaststdate < Utils.dateparser('2021-03-15'):
                    lastval -= delta
                if unacaststdate > Utils.dateparser('2021-04-15') and unacaststdate < Utils.dateparser('2021-05-01'):
                    lastval -= delta
                transprobval = DiseaseParameters['TransProb_AH'][day_count]*(1+float(lastval)+DiseaseParameters['TransProb_intnumval'][day_count])            
                transprobvallow = transprobval*.5
                transprobvalhigh = (transprobval - transprobvallow*.4)/.6
                TransProbC.append(transprobvalhigh)
                TransProbCLow.append(transprobvallow)
                day_count+=1

            DiseaseParameters['TransProb'] = TransProbC.copy()
            DiseaseParameters['TransProbLow'] = TransProbCLow.copy()        
    
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
                                BAProportion[G]-HealthcareWorkerPercent[G],NursingCareFacilities[G]+AssistedLivingFacilities[G]+LTCF[G],newdeclinevals,newdeclinevalsLow)
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

# This is called from main
def RunDefaultModelType(ModelType,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder='',startDate=datetime(2020,2,1),fitdates=[],hospitalizations=[],deaths=[],cases=[],fitper=.3,StartInfected=-1,historyData={}):
    
    cleanUp(modelPopNames)
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters)
    
    RegionalList, timeRange, fitinfo = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,mprandomseed,startDate=startDate,stepLength=1,numregions=-1,modelPopNames=modelPopNames,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,cases=cases,fitper=fitper,burnin=False,StartInfected=StartInfected,historyData=historyData)
    

    PostProcessing.WriteParameterVals(resultsName,ModelType,ParameterVals,writefolder)
    results = PostProcessing.CompileResults(resultsName,modelPopNames,RegionalList,timeRange)
    PostProcessing.WriteAggregatedResults(results,ModelType,resultsName,modelPopNames,RegionalList,HospitalNames,endTime,writefolder)    
    
    cleanUp(modelPopNames,len(RegionalList))
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

    return fitinfo

# This is called from main
def RunSavedRegionModelType(ModelType,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder='',startDate=datetime(2020,2,1),SavedRegionFolder='',numregions=-1,FolderContainer=''):
    cleanUp(modelPopNames)
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters)
    
    RegionalList, timeRange, fitinfo = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,mprandomseed,startDate=startDate,modelPopNames=modelPopNames,SavedRegionFolder=SavedRegionFolder,numregions=numregions,FolderContainer=FolderContainer)
    
    if fitinfo['fitted']:
        PostProcessing.WriteFitvals(resultsName,ModelType,fitinfo['SLSH'], fitinfo['SLSD'], fitinfo['SLSC'], fitinfo['avgperdiffhosp'], fitinfo['avgperdiffdeaths'], fitinfo['avgperdiffcases'],writefolder)
        PostProcessing.WriteParameterVals(resultsName,ModelType,ParameterVals,writefolder)
        results = PostProcessing.CompileResults(resultsName,modelPopNames,RegionalList,timeRange)
        PostProcessing.WriteAggregatedResults(results,ModelType,resultsName,modelPopNames,RegionalList,HospitalNames,endTime,writefolder)    
    
    cleanUp(modelPopNames,len(RegionalList))
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

    return fitinfo
    
        
def RunBurnin(ModelType,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder='',startDate=datetime(2020,2,1),fitdates=[],hospitalizations=[],deaths=[],cases=[],fitper=.3,FolderContainer='',saveRun=False,historyData={},SavedRegionFolder=ParameterSet.SavedRegionFolder,burnin=True):
    
    if saveRun:
        if not os.path.exists(os.path.join(SavedRegionFolder,FolderContainer)):
            os.makedirs(os.path.join(SavedRegionFolder,FolderContainer))
            
    cleanUp(modelPopNames)
        
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(ModelType,modelvals,PopulationParameters,DiseaseParameters)
    
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
    
    RegionalList, timeRange, fitinfo = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,mprandomseed,startDate=startDate,modelPopNames=modelPopNames,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,cases=cases,fitper=fitper,burnin=burnin,FolderContainer=FolderContainer,saveRun=saveRun,historyData=historyData,SavedRegionFolder=SavedRegionFolder)

    if saveRun and fitinfo['fitted']:
        PostProcessing.WriteFitvals(resultsName,ModelType,fitinfo['SLSH'], fitinfo['SLSD'], fitinfo['SLSC'], fitinfo['avgperdiffhosp'], fitinfo['avgperdiffdeaths'], fitinfo['avgperdiffcases'],writefolder)
        Utils.PickleFileWrite(os.path.join(SavedRegionFolder,FolderContainer,"PopulationParameters.pickle"), PopulationParameters)
        Utils.PickleFileWrite(os.path.join(SavedRegionFolder,FolderContainer,"DiseaseParameters.pickle"), DiseaseParameters)
    else:
        if os.path.exists(os.path.join(SavedRegionFolder,FolderContainer)):
            os.rmdir(os.path.join(SavedRegionFolder,FolderContainer))
    cleanUp(modelPopNames,len(RegionalList))
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

    return fitinfo


            
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
    