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

## Model Imports
import ProcessManager
import GlobalLocationSetup
import ParameterSet
import data.ConstructInteractionMatrix
import data.MDDCVAregion.ProcessDataMDDCVAED
import Utils
import PostProcessing


def MDVADCInteractionMatrix():
    print("Loading Maryland/DC/Virgina Zipcode Centroid ...")
    MDPop = pd.read_csv('data/MDDCVAregion/MDDCVAregionCentroid.csv')
    MDPop = MDPop.dropna(subset=['POPULATION'])
    MDPop = MDPop[MDPop.POPULATION != 0].copy()
    # delete all rows not in ED Matrix
    NoEDZip = MDPop[(MDPop['ZIP_CODE'] == 20656) |
                    (MDPop['ZIP_CODE'] == 20701) |
                    (MDPop['ZIP_CODE'] == 20771) |
                    (MDPop['ZIP_CODE'] == 21031) |
                    (MDPop['ZIP_CODE'] == 21240)].index
    MDPop = MDPop.drop(NoEDZip)
    # ZipNames = np.asarray(MDPop['ZIP_CODE'])
    PopulationData = np.asarray(MDPop['POPULATION'])
    PopulationDensity = np.asarray(MDPop['POPULATION']/MDPop['SQMI'])
    Zipcodes = np.asarray(MDPop['ZIP_CODE'])
    Zipcodes = np.asarray(MDPop['ZIP_CODE'])
    States = np.asarray(MDPop['STATE'])
    LongCentroid = np.asarray(MDPop['Longitude'])
    LatCentroid = np.asarray(MDPop['Latitude'])
    BAProportion = np.asarray(MDPop['BAProportion'])
    NursingCareFacilities = np.asarray(MDPop['NursingCareFacilities'])
    AssistedLivingFacilities = np.asarray(MDPop['AssistedLivingFacilities'])
    LTCF = np.asarray(MDPop['LTCF'])
    HealthcareWorkerPercent = np.asarray(MDPop['HealthcareWorkerPercent'])

    MDHospitalData = data.MDDCVAregion.ProcessDataMDDCVAED.InputData('data/MDDCVAregion', MDPop) # Process movement network
    HospitalTransitionRate = MDHospitalData.TranCH
    
    # This makes sure it runs on all unix systems
    HospitalColNamesRaw = MDHospitalData.ProviderNamesColumn # Dictionary of hospital names to adj matrix column
    HospitalColNames = []
    for i in range(0,len(HospitalColNamesRaw)):
        HospitalColNames.append(HospitalColNamesRaw[i].encode("ascii",errors="ignore").decode())

    numpops = len(PopulationData)  # number of HRRs
    print("Loaded: ", numpops, " Populations, with a total population of ", sum(PopulationData), " (mean:",
          sum(PopulationData) / len(PopulationData), " max:", max(PopulationData), " min:", min(PopulationData))

    
    InteractionMatrix = data.ConstructInteractionMatrix. \
        CreateInteractionMatrix(LongCentroid, LatCentroid, PopulationData)
    
    HHSizeDist = [14.7,26.9,18.6,20.1,10.9,4.8,4]
    HHSizeAgeDist = {}
    HHSizeAgeDist[1] = [0,0,5.1,3.7,5.9]
    HHSizeAgeDist[2] = [0.1,0.8,7.6,9.1,9.3]
    HHSizeAgeDist[3] = [1.1,2.8,8.2,4.6,1.9]
    HHSizeAgeDist[4] = [1.8,5.7,9,2.8,0.8]
    HHSizeAgeDist[5] = [1,3.8,4.5,1.2,0.4]
    HHSizeAgeDist[6] = [0.5,1.7,1.9,0.5,0.2]
    HHSizeAgeDist[7] = [0.5,1.4,1.5,0.4,0.2]    
        
    GlobalLocations = []
    for i in range(0, numpops):
        GL = GlobalLocationSetup.\
            GlobalLocationSetup(i, PopulationData[i], HHSizeDist,
                                                     HHSizeAgeDist, PopulationDensity[i], Zipcodes[i],States[i],(1-BAProportion[i])+HealthcareWorkerPercent[i],NursingCareFacilities[i]+AssistedLivingFacilities[i]+LTCF[i])
        GlobalLocations.append(GL)
    
    
    return PopulationData, InteractionMatrix, HospitalTransitionRate, HospitalColNames,GlobalLocations


def modelSetup(PopulationParameters,DiseaseParameters):

    ## Need error check here to make sure that modelpopnames is a valid system name
    #if modelPopNames is None:
    #    modelPopNames = 'region'

    GlobalInteractionMatrix = []

    HospitalTransitionRate = []
    PopulationDensity = []
    
    WuhanCoordDict = {}
    
    GlobalLocations = []
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations = MDVADCInteractionMatrix()
    LocationImportationRisk = []
    popsum = sum(PopulationData)
    for i in range(0,len(PopulationData)):
        LocationImportationRisk.append(PopulationData[i]/popsum)     
   
    return PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk


def RunDefaultModelType(ModelType,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,stepLength=1,writefolder='',startDate=datetime(2020,2,1)):
    
    cleanUp(modelPopNames)
    ParameterVals = PopulationParameters
    ParameterVals.update(DiseaseParameters)
       
    PostProcessing.WriteParameterVals(resultsName,ModelType,ParameterVals,writefolder)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(PopulationParameters,DiseaseParameters)
    
    RegionalList = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,startDate=startDate,modelPopNames=modelPopNames)
    results = Utils.PickleFileRead(os.path.join(ParameterSet.ResultsFolder,"Results_" + resultsName + ".pickle"))
    PostProcessing.WriteAggregatedResults(results,ModelType,resultsName,modelPopNames,RegionalList,HospitalNames,endTime,writefolder)    
    cleanUp(modelPopNames)
    if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):    
        os.remove(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))

def RunFitModelType(ModelType,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,startDate):
    
    cleanUp(modelPopNames)
    
    PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations, LocationImportationRisk = modelSetup(PopulationParameters,DiseaseParameters)
    
    RegionalList = ProcessManager.RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,modelPopNames=modelPopNames,startDate=startDate)
    
    results = Utils.PickleFileRead(os.path.join(ParameterSet.ResultsFolder,"Results_" + resultsName + ".pickle"))
    return results
            
def cleanUp(modelPopNames=''):
    
    # Cleanup population data
    i = 0
    RegionalList = []
    for filename in os.listdir(ParameterSet.PopDataFolder):
        if os.path.exists(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle")):
            RegionalList.append(i)
            i += 1

    for i in range(0, len(RegionalList)):
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle"))
        except:
            pass
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"STATS.pickle"))
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"AgeStats.pickle"))
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"))
        except:
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"HOSPLIST.pickle"))
        except:
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"))
        except:
            pass
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"R0Stats.pickle"))
        except:
            pass
    