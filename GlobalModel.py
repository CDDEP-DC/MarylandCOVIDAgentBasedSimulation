# -----------------------------------------------------------------------------
# GlobalModel.py builds the entire model and partitions the model into
# designated processes and local models
# -----------------------------------------------------------------------------

# System Imports
import numpy as np
import random
import os
import gc
import math
import time
import pandas as pd

## Model Imports
import ProcessManager
import GlobalLocationSetup
import ParameterSet
import data.ConstructInteractionMatrix
import data.Maryland.ProcessDataMD
import data.Maryland.ProcessDataMDED
import data.landscan.GridExtraction
import data.MDDCVAregion.ProcessDataMDDCVAED
import Utils
import PostProcessing


def USHRRRegionInteractionMatrix():
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice): print("Loading HRR Centroid ...")
    HrrPop = pd.read_csv('data/hrr/HRRCentroidPopulation.csv')
    HrrPop = HrrPop.dropna(subset=['population'])
    HrrPop = HrrPop[HrrPop.population != 0].copy()
    PopulationData = np.asarray(HrrPop['population'])
    LongCentroid = np.asarray(HrrPop['Longitude'])
    LatCentroid = np.asarray(HrrPop['Latitude'])

    numpops = len(PopulationData)  # number of HRRs
    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Loaded: ", numpops, " Populations, with a total population of ", sum(PopulationData), " (mean:",
              sum(PopulationData) / len(PopulationData), " max:", max(PopulationData), " min:", min(PopulationData))

    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Creating Interaction Matrix ...")
    InteractionMatrix = data.ConstructInteractionMatrix. \
        CreateInteractionMatrix(LongCentroid, LatCentroid, PopulationData)

    return PopulationData, InteractionMatrix


def TestVersionRandomMatrix(numpops=10,hospitals=5):
    PopulationData = []
    PopulationDensity = []
    DistanceMatrix = np.empty([numpops, numpops], np.single)
    CalcPopDistMatrix = np.empty([numpops, numpops], np.single)
    GlobalInteractionMatrix = np.empty([numpops, numpops], np.single)
    HospitalInteractionMatrix = np.empty([numpops, hospitals], np.single)
    HospitalTransitionRate = np.empty([numpops, hospitals], np.single)

    for i in range(0, numpops):
        PopulationData.append(random.randint(3000, 20000))
        PopulationDensity.append(random.randint(300, 2000))
        
    for i in range(0, numpops):
        for j in range(0, numpops):
            DistanceMatrix[i][j] = (random.randint(300, 3000))

    for i in range(0, numpops):
        for j in range(0, numpops):
            if i == j:
                CalcPopDistMatrix[i, j] = PopulationData[i] * PopulationData[j]
            else:
                CalcPopDistMatrix[i, j] = PopulationData[i] * PopulationData[j] / DistanceMatrix[i][j]
    
    for i in range(0, numpops):
        rowSum = 0.0
        for j in range(0, numpops):
            rowSum = rowSum + CalcPopDistMatrix[i, j]
        for j in range(0, numpops):
            GlobalInteractionMatrix[i][j] = CalcPopDistMatrix[i, j] / rowSum

    for i in range(0, numpops):
        for j in range(0, hospitals):
            HospitalInteractionMatrix[i][j] = (random.random())

    for i in range(0, numpops):
        rowSum = 0.0
        for j in range(0, hospitals):
            rowSum = rowSum + HospitalInteractionMatrix[i, j]
        for j in range(0, hospitals):
            HospitalTransitionRate[i][j] = HospitalInteractionMatrix[i, j] / rowSum

    HospitalColNames = []
    for i in range(0,hospitals):
        HospitalColNames.append(str(i))
        
    return PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalColNames, PopulationDensity

def IndiaInteractionMatrix():
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Loading Inda Centroid ...")
    iPop = pd.read_csv('data/India/IndiaCentroid.csv')
    iPop = iPop.dropna(subset=['POPULATION'])
    iPop = iPop[iPop.POPULATION != 0].copy()
    # delete all rows not in ED Matrix
    PopulationData = np.asarray(iPop['POPULATION'])
    LongCentroid = np.asarray(iPop['Longitude'])
    LatCentroid = np.asarray(iPop['Latitude'])
    
    numpops = len(PopulationData)  # number of HRRs
    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Loaded: ", numpops, " Populations, with a total population of ", sum(PopulationData), " (mean:",
              sum(PopulationData) / len(PopulationData), " max:", max(PopulationData), " min:", min(PopulationData))

    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Creating Interaction Matrix ...")
    
    InteractionMatrix = data.ConstructInteractionMatrix. \
        CreateInteractionMatrix(LongCentroid, LatCentroid, PopulationData)
    # fake data don't care about hospitals
    HospitalInteractionMatrix = np.empty([numpops, hospitals], np.single)
    HospitalTransitionRate = np.empty([numpops, hospitals], np.single)

    for i in range(0, numpops):
        PopulationData.append(random.randint(3000, 20000))

    for i in range(0, numpops):
        for j in range(0, hospitals):
            HospitalInteractionMatrix[i][j] = (random.random())

    for i in range(0, numpops):
        rowSum = 0.0
        for j in range(0, hospitals):
            rowSum = rowSum + HospitalInteractionMatrix[i, j]
        for j in range(0, hospitals):
            HospitalTransitionRate[i][j] = HospitalInteractionMatrix[i, j] / rowSum

    HospitalColNames = []
    for i in range(0,hospitals):
        HospitalColNames.append(str(i))
        
    return PopulationData, InteractionMatrix, HospitalTransitionRate, HospitalColNames    
    
    
def MDVADCInteractionMatrix():
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
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
    MDHospitalData = data.MDDCVAregion.ProcessDataMDDCVAED.InputData('data/MDDCVAregion', MDPop) # Process movement network
    HospitalTransitionRate = MDHospitalData.TranCH
    HospitalColNames = MDHospitalData.ProviderNamesColumn # Dictionary of hospital names to adj matrix column

    numpops = len(PopulationData)  # number of HRRs
    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Loaded: ", numpops, " Populations, with a total population of ", sum(PopulationData), " (mean:",
              sum(PopulationData) / len(PopulationData), " max:", max(PopulationData), " min:", min(PopulationData))

    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Creating Interaction Matrix ...")
    
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
                                                     HHSizeAgeDist, PopulationDensity[i], Zipcodes[i],States[i])
        GlobalLocations.append(GL)
    
    
    return PopulationData, InteractionMatrix, HospitalTransitionRate, HospitalColNames,GlobalLocations
    
def MarylandInteractionMatrix():
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Loading Maryland Zipcode Centroid ...")
    MDPop = pd.read_csv('data/Maryland/MDZipCentroidPop.csv')
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
    Zipcodes = np.asarray(MDPop['ZIP_CODE'])
    States = np.asarray(MDPop['STATE'])
    PopulationDensity = np.asarray(MDPop['POPULATION']/MDPop['SQMI'])
    LongCentroid = np.asarray(MDPop['Longitude'])
    LatCentroid = np.asarray(MDPop['Latitude'])
    MDHospitalData = data.Maryland.ProcessDataMDED.InputData('data/Maryland', MDPop) # Process movement network
    HospitalTransitionRate = MDHospitalData.TranCH
    HospitalColNames = MDHospitalData.ProviderNamesColumn # Dictionary of hospital names to adj matrix column
    
    numpops = len(PopulationData)  # number of HRRs
    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Loaded: ", numpops, " Populations, with a total population of ", sum(PopulationData), " (mean:",
              sum(PopulationData) / len(PopulationData), " max:", max(PopulationData), " min:", min(PopulationData))

    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Creating Interaction Matrix ...")
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
                                                     HHSizeAgeDist, PopulationDensity[i], Zipcodes[i],States[i])
        GlobalLocations.append(GL)
    
    
    return PopulationData, InteractionMatrix, HospitalTransitionRate, HospitalColNames,GlobalLocations

def WuhanInteractionMatrix(xRes,yRes,hospitals=1):
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Loading Wuhan Landscan Data ...")
    WuhanGrid = pd.read_csv('data/landscan/wuhan.asc',skiprows=6,sep=" ",header=None)
    WuhanGrid = WuhanGrid.drop(columns=WuhanGrid.shape[1]-1, axis=1)    # get rid of last col of NAs
    WuhanGrid = np.array(WuhanGrid)
    WuhanXcoord, WuhanYcoord, WuhanPop, WuhanMap = data.landscan.GridExtraction.\
        GridExtraction(WuhanGrid,xRes,yRes)

    numpops = len(WuhanPop)  # number of local pops
    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Loaded: ", numpops, " Populations, with a total population of ", sum(WuhanPop), " (mean:",
              sum(WuhanPop) / len(WuhanPop), " max:", max(WuhanPop), " min:", min(WuhanPop), ")")

    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Creating Interaction Matrix ...")
    InteractionMatrix = data.landscan.GridExtraction. \
        CreateInteractionMatrixFromLandscan(WuhanXcoord, WuhanYcoord, WuhanPop)

    # Create surrogate hospital transition matrix
    HospitalInteractionMatrix = np.empty([numpops, hospitals], np.single)
    HospitalTransitionRate = np.empty([numpops, hospitals], np.single)
    for i in range(0, numpops):
        for j in range(0, hospitals):
            HospitalInteractionMatrix[i][j] = (random.random())

    for i in range(0, numpops):
        rowSum = 0.0
        for j in range(0, hospitals):
            rowSum = rowSum + HospitalInteractionMatrix[i, j]
        for j in range(0, hospitals):
            HospitalTransitionRate[i][j] = HospitalInteractionMatrix[i, j] / rowSum

    HospitalColNames = []
    for i in range(0,hospitals):
        HospitalColNames.append(str(i))

    return WuhanPop, InteractionMatrix, HospitalTransitionRate, WuhanMap

def modelSetup(version, modelPopNames=None, combineLocations=False, TestNumPops = 10,
               XRes = None, YRes = None):

    ## Need error check here to make sure that modelpopnames is a valid system name
    if modelPopNames is None:
        modelPopNames = 'region'

    GlobalInteractionMatrix = []

    HospitalTransitionRate = []
    PopulationDensity = []
    
    WuhanCoordDict = {}
    
    GlobalLocations = []
    
    if version == 'USHRR':
        PopulationData, GlobalInteractionMatrix = USHRRRegionInteractionMatrix()
    elif version == 'test':
        PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, PopulationDensity = TestVersionRandomMatrix(TestNumPops)
    elif version == 'Maryland' or version == 'MarylandFit':
        PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations = MarylandInteractionMatrix()
    elif version == 'MDDCVAregion':
        PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames, GlobalLocations = MDVADCInteractionMatrix()
    elif version == 'IndiaSIM':
        PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, HospitalNames = IndiaInteractionMatrix()
    elif version == 'Wuhan':
        PopulationData, GlobalInteractionMatrix, HospitalTransitionRate, WuhanCoordDict = WuhanInteractionMatrix(XRes,YRes)
    else:
        print('ERROR: No valid model version specified! Available versions are: `USHRR`, `Maryland`, and `test` ')
        return
   
         
    numpops = len(PopulationData)
    
    if len(GlobalLocations) == 0:
        if len(PopulationDensity) == 0:
            for i in range(numpops):
                PopulationDensity.append(1)
                           
        if len(LocalIdentification) == 0:
            for i in range(numpops):
                LocalIdentification.append(1)
            
        for i in range(0, numpops):
            if len(WuhanCoordDict) > 0:
                if list(WuhanCoordDict.keys())[i] == 'Market':
                    ParameterSet.WuhanMktLocalPopId = i
    
            GL = GlobalLocationSetup.\
                GlobalLocationSetup(i, PopulationData[i], ParameterSet.HHSizeDist,
                                                         ParameterSet.HHSizeAgeDist, PopulationDensity[i], LocalIdentification[i])
            GlobalLocations.append(GL)
        
    
    
    # generate a matrix of population size proportional for importation risk
    LocationImportationRisk = []
    popsum = sum(PopulationData)
    for i in range(0,len(PopulationData)):
        LocationImportationRisk.append(PopulationData[i]/popsum)
       
    if ParameterSet.debugmodelevel >= ParameterSet.debugnotice:
        print("Generating ",numpops," local populations with ",sum(PopulationData)," agents")

    
    
    
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Completed Setup!")

    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Building populations ...")

    ## create regional blocks and store them to disk
    if combineLocations:
        RegionalList, numInfList, RegionListGuide = ProcessManager.BuildGlobalPopulations(GlobalLocations, GlobalInteractionMatrix, modelPopNames, HospitalTransitionRate)
    else:
        RegionalList, numInfList, RegionListGuide = ProcessManager.BuildGlobalPopulations(GlobalLocations, GlobalInteractionMatrix, modelPopNames, HospitalTransitionRate, 
                                                             numpops)
    
    
                                                                 
    del GlobalLocations
    del GlobalInteractionMatrix

    # make sure all other unneeded memory objects are dropped
    gc.collect()
    if version == 'Wuhan':
        setupOutput = RegionalList, numInfList, WuhanCoordDict, HospitalTransitionRate
    else:
        setupOutput = RegionalList, numInfList, HospitalNames, LocationImportationRisk, RegionListGuide

    return setupOutput

def RunDefaultModelType(ModelType,modelPopNames,resultsName,endTime,stepLength=1,writefolder=''):
    
    ParameterVals = { 
        'AG04AsymptomaticRate':ParameterSet.AG04AsymptomaticRate,
        'AG04HospRate':ParameterSet.AG04HospRate,
        'AG517AsymptomaticRate':ParameterSet.AG517AsymptomaticRate,
        'AG517HospRate':ParameterSet.AG517HospRate,
        'AG1849AsymptomaticRate':ParameterSet.AG1849AsymptomaticRate,
        'AG1849HospRate':ParameterSet.AG1849HospRate,
        'AG5064AsymptomaticRate':ParameterSet.AG5064AsymptomaticRate,
        'AG5064HospRate':ParameterSet.AG5064HospRate,
        'AG65AsymptomaticRate':ParameterSet.AG65AsymptomaticRate,
        'AG65HospRate':ParameterSet.AG65HospRate,
        'IncubationTime':ParameterSet.IncubationTime,
        'totalContagiousTime':ParameterSet.totalContagiousTime,
        'hospitalSymptomaticTime':ParameterSet.hospitalSymptomaticTime,
        'hospTime':ParameterSet.hospTime,
        'symptomaticTime':ParameterSet.symptomaticTime,
        'EDVisit':ParameterSet.EDVisit,
        'preContagiousTime':ParameterSet.preContagiousTime,
        'postContagiousTime':ParameterSet.postContagiousTime,
        'householdcontactRate':ParameterSet.householdcontactRate,
        'ProbabilityOfTransmissionPerContact':ParameterSet.ProbabilityOfTransmissionPerContact,
        'symptomaticContactRateReduction':ParameterSet.symptomaticContactRateReduction,
        'ImportationRate':ParameterSet.ImportationRate,
        'AsymptomaticReducationTrans':ParameterSet.AsymptomaticReducationTrans,
        'InterventionDate':ParameterSet.InterventionDate,
        'ImportationRatePower':ParameterSet.ImportationRatePower
    }
    
    RegionalList, numInfList, HospitalNames, LocationImportationRisk, RegionListGuide = modelSetup(ModelType, modelPopNames,combineLocations=True,TestNumPops=10)
    RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsName, numInfList,LocationImportationRisk=LocationImportationRisk, RegionListGuide=RegionListGuide)
    results = Utils.FileRead(ParameterSet.ResultsFolder + "/Results_" + resultsName + ".pickle")
    
    PostProcessing.WriteAggregatedResults(results,ModelType,resultsName,modelPopNames,RegionalList,ParameterVals,HospitalNames,endTime,writefolder)    
    cleanUp(modelPopNames)
    return HospitalNames


def RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsName, numInfList, randomInfect=True,LocationImportationRisk=[],RegionListGuide=[]):
                   
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Starting Full Model Run")
    t = time.time()
    ProcessManager.RunFullModel(RegionalList, endTime, stepLength, modelPopNames, resultsName, numInfList,randomInfect,LocationImportationRisk,RegionListGuide)
    t2 = time.time()
    if (ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("Completed in: ", t2 - t)

   


            
def cleanUp(modelPopNames):
    # Cleanup population data
    i = 0
    RegionalList = []
    for filename in os.listdir(ParameterSet.PopDataFolder):
        if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle"):
            RegionalList.append(i)
            i += 1
    for i in range(0, len(RegionalList)):
        try:
            os.remove(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle")
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Removed "+ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle")
        except:
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Pop ", i, " did not exist")
        try:
            os.remove(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "STATS.pickle")
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Removed "+ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "STATS.pickle")
        except:
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Pop ", i, " STATS did not exist")
            
        try:
            os.remove(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Removed "+ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
        except:
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Pop ", i, " HOSPLIST did not exist")
            
        try:
            os.remove(ParameterSet.QueueFolder+"/"+str(modelPopNames)+str(i)+"Queue.pickle")
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Removed "+ParameterSet.QueueFolder+"/"+str(modelPopNames)+str(i)+"Queue.pickle")
        except:
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Queue ", i, " did not exist")                
            
        try:
            os.remove(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle")
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Removed "+ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle")
        except:
            if (ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Pop ", i, " R0Stats did not exist")