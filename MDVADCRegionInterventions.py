


import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv

import PostProcessing
import ParameterSet
import Utils
import GlobalModel
from ProcessingDataForPresentation import ProcessDataForPresentation as ProcessDataForPresentation

import unicodedata
import string
import sys, getopt

def JiggleParameters():
    #agecohort 0 -- 0-4
    AG04GammaScale = 6
    AG04GammaShape = 2.1
    AG04AsymptomaticRate = random.randint(98,99)/100
    AG04HospRate = random.randint(1,1)/100
    AG04MortalityRate = random.randint(1,2)/10000
      
    #agecohort 1 -- 5-17
    AG517GammaScale = 6
    AG517GammaShape = 3
    AG517AsymptomaticRate = random.randint(98,99)/100
    AG517HospRate = random.randint(1,1)/100
    AG517MortalityRate = random.randint(1,2)/1000
    
    #agecohort 2 -- 18-49
    AG1849GammaScale = 6
    AG1849GammaShape = 2.5
    AG1849AsymptomaticRate = random.randint(90,90)/100
    AG1849HospRate = random.randint(9,11)/100
    AG1849MortalityRate = random.randint(6,8)/1000
     
    #agecohort 3 -- 50-64
    AG5064GammaScale = 6
    AG5064GammaShape = 2.3
    AG5064AsymptomaticRate = random.randint(90,90)/100
    AG5064HospRate = random.randint(25,25)/100
    AG5064MortalityRate = random.randint(13,15)/1000


    #agecohort 4 -- 65+
    AG65GammaScale = 6
    AG65GammaShape = 2.1
    AG65AsymptomaticRate = random.randint(90,90)/100
    AG65HospRate = random.randint(50,50)/100
    AG65MortalityRate = random.randint(36,37)/100

    AgeCohortInteraction = {0:{0:1.39277777777778,	1:0.328888888888889,	2:0.299444444444444,	3:0.224444444444444,	4:0.108333333333333},
                                    1:{0:0.396666666666667,	1:2.75555555555556,	2:0.342407407407407,	3:0.113333333333333,	4:0.138333333333333},
                                    2:{0:0.503333333333333,	1:1.22666666666667,	2:1.035,	3:0.305185185185185,	4:0.180555555555556},
                                    3:{0:0.268888888888889,	1:0.164074074074074, 2:0.219444444444444,	3:0.787777777777778,	4:0.27},
                                    4:{0:0.181666666666667,	1:0.138888888888889, 2:0.157222222222222,	3:0.271666666666667,	4:0.703333333333333}}
                                    
    PopulationParameters = {}
    
    DiseaseParameters = {}
    
    DiseaseParameters['AGHospRate'] = [AG04HospRate,AG517HospRate,AG1849HospRate,AG5064HospRate,AG65HospRate]
    DiseaseParameters['AGAsymptomaticRate'] = [AG04AsymptomaticRate, AG517AsymptomaticRate, AG1849AsymptomaticRate, AG5064AsymptomaticRate,AG65AsymptomaticRate]
    DiseaseParameters['AGMortalityRate'] = [AG04MortalityRate,AG517MortalityRate,AG1849MortalityRate,AG5064MortalityRate,AG65MortalityRate]
            
    PopulationParameters['AGGammaScale'] = [AG04GammaScale,AG517GammaScale,AG1849GammaScale,AG5064GammaScale,AG65GammaScale]
    PopulationParameters['AGGammaShape'] = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
    PopulationParameters['householdcontactRate'] = random.randint(35,42)
    
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    
    ## Disease Progression Parameters
    DiseaseParameters['IncubationTime'] = random.randint(2,2)
    
    # gamma1
    DiseaseParameters['mildContagiousTime'] = random.randint(4,5)
    DiseaseParameters['AsymptomaticReducationTrans'] = random.randint(80,80)/100 #20%
    
    # gamma2
    DiseaseParameters['preContagiousTime'] = random.randint(2,2)  
    DiseaseParameters['symptomaticTime'] = random.randint(9,9)  # with symptomatic contact rate reduction similar to five days
    DiseaseParameters['postContagiousTime']	= random.randint(1,2)
    DiseaseParameters['symptomaticContactRateReduction'] = 1 #random.randint(80,90)/100 #10-20%
    
    DiseaseParameters['preHospTime'] = random.randint(4,6) 
    DiseaseParameters['hospitalSymptomaticTime'] = random.randint(6,8)
    DiseaseParameters['ICURate'] = random.randint(40,50)/100
    DiseaseParameters['ICUtime'] = random.randint(8,10)
    DiseaseParameters['PostICUTime'] = random.randint(2,4)
    DiseaseParameters['hospitalSymptomaticContactRateReduction'] = 1 #random.randint(40,50)/100
    
    
    DiseaseParameters['EDVisit'] = random.randint(60,80)/100 
    
    
    DiseaseParameters['ImportationRate'] = random.randint(25,25)
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = random.randint(30,50)/1000
    
    
    return PopulationParameters, DiseaseParameters
  

def main(argv):
    
    #### This sets up folders for running the model in
    runs, OutputResultsFolder = Utils.ModelFolderStructureSetup(argv)
    
    generatePresentationVals = 0 # set this to 1 if this is the only run across nodes to complete analysis - set to 0 if this is run across several nodes and use ProcessingDataForPresentation file as standalone afterwards to combine
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is
    Model = 'MDDCVAregion'  # select model - defines the model type to run
    
    ## Set the interventions to run here - each intervention should have a value for reductions
    #interventionnames = ['distance.9','distance.75','distance.5','distance.25','worse','altdistance.9','altdistance.5']
    #interventionnames = ['distance.95','distance.75','distance.5','distance.25','altdistance.9']
    interventions = {}
    #baseline
    #interventions['baseline'] = {}
    #interventions['baseline']['reduction'
    interventions['distance.50'] = {}
    interventions['distance.50']['type'] = 'distance'
    interventions['distance.50']['InterventionDate'] = 35
    interventions['distance.50']['InterventionReduction'] = []
    interventions['distance.50']['SchoolInterventionReduction'] = []
    for i in range(35,39):
        interventions['distance.50']['InterventionReduction'].append(.50)
    for i in range(41,60):
        interventions['distance.50']['InterventionReduction'].append(.40)
    for i in range(60,73):
        interventions['distance.50']['InterventionReduction'].append(.45)
    for i in range(74,88):
        interventions['distance.50']['InterventionReduction'].append(.48)
    for i in range(89,111):
        interventions['distance.50']['InterventionReduction'].append(.50)
        
    interventions['distance.50']['SchoolInterventionDate'] = 27
    for i in range(27,34):
        interventions['distance.50']['SchoolInterventionReduction'].append(.75)
    interventions['distance.50']['SchoolInterventionReduction'].extend(interventions['distance.50']['InterventionReduction'])
    
    interventions['distance.50']['InterventionMobilityEffect'] = 1
    
    
    interventions['distance.alt50'] = {}
    interventions['distance.alt50']['type'] = 'distance'
    interventions['distance.alt50']['InterventionDate'] = 35
    interventions['distance.alt50']['InterventionReduction'] = []
    interventions['distance.alt50']['SchoolInterventionReduction'] = []
    for i in range(35,111):
        interventions['distance.alt50']['InterventionReduction'].append(.50)
        
    interventions['distance.alt50']['SchoolInterventionDate'] = 27
    for i in range(27,34):
        interventions['distance.alt50']['SchoolInterventionReduction'].append(.75)
    interventions['distance.alt50']['SchoolInterventionReduction'].extend(interventions['distance.alt50']['InterventionReduction'])
    
    interventions['distance.alt50']['InterventionMobilityEffect'] = 1
    
    interventions['distance.alt40'] = {}
    interventions['distance.alt40']['type'] = 'distance'
    interventions['distance.alt40']['InterventionDate'] = 35
    interventions['distance.alt40']['InterventionReduction'] = []
    interventions['distance.alt40']['SchoolInterventionReduction'] = []
    for i in range(35,111):
        interventions['distance.alt40']['InterventionReduction'].append(.40)
        
    interventions['distance.alt40']['SchoolInterventionDate'] = 27
    for i in range(27,34):
        interventions['distance.alt40']['SchoolInterventionReduction'].append(.75)
    interventions['distance.alt40']['SchoolInterventionReduction'].extend(interventions['distance.alt40']['InterventionReduction'])
    
    interventions['distance.alt40']['InterventionMobilityEffect'] = 1
    
    interventions['distance.alt30'] = {}
    interventions['distance.alt30']['type'] = 'distance'
    interventions['distance.alt30']['InterventionDate'] = 35
    interventions['distance.alt30']['InterventionReduction'] = []
    interventions['distance.alt30']['SchoolInterventionReduction'] = []
    for i in range(35,111):
        interventions['distance.alt30']['InterventionReduction'].append(.30)
        
    interventions['distance.alt30']['SchoolInterventionDate'] = 27
    for i in range(27,34):
        interventions['distance.alt30']['SchoolInterventionReduction'].append(.75)
    interventions['distance.alt30']['SchoolInterventionReduction'].extend(interventions['distance.alt30']['InterventionReduction'])
    
    interventions['distance.alt30']['InterventionMobilityEffect'] = 1
    #interventionnames = ['distance.5','distance.75','distance.65','baseline'] #,'seasonalitydistance.75','seaonalitydistance.50']
    #intervenionreduction1 = [.5,.25,.35] #,.25,.5]
    #intervenionreduction2 = [0,0,0,0,0] #,0,0]
    #intervenionreductionSchool = [.5,.25,.25] #,.25,.5]
    
    ## alter values related to transmission in Utils file
        
            
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
    
    
                      
    for run in range(0,runs):
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        
        PopulationParameters, DiseaseParameters = JiggleParameters()
            
        #for intnum in range(0,len(interventionnames)):
        for key in interventions.keys():
            print(key)
            endTime = 111
            DiseaseParameters['Intervention'] = key
            DiseaseParameters['InterventionDate'] = interventions[key]['InterventionDate']
            DiseaseParameters['InterventionReduction'] = interventions[key]['InterventionReduction']
            DiseaseParameters['SchoolInterventionDate'] = interventions[key]['SchoolInterventionDate']
            DiseaseParameters['SchoolInterventionReduction'] = interventions[key]['SchoolInterventionReduction']
            DiseaseParameters['InterventionMobilityEffect'] = interventions[key]['InterventionMobilityEffect']
            
            resultsNameP = key + "_" + resultsName
            
            #ParameterSet.debugmodelevel = ParameterSet.debugerror
            HospitalNames = GlobalModel.RunDefaultModelType(Model, modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,writefolder=OutputResultsFolder)
            
            if generatePresentationVals == 1:
                ProcessDataForPresentation(interventionnames,HospitalNames,readFolder=OutputResultsFolder,writefolder=OutputResultsFolder,resultsName=overallResultsName)
                
    if os.path.exists(FolderContainer):
        GlobalModel.cleanUp()        
        
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])
