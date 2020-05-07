# -----------------------------------------------------------
# Main.py is the executable that runs the entire model
# -----------------------------------------------------------


import sys, getopt
import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
import os
import csv
import unicodedata
import string


import PostProcessing
import ParameterSet
import Utils
import GlobalModel
import ProcessManager
#from ProcessingDataForPresentation import ProcessDataForPresentation as ProcessDataForPresentation




def JiggleParameters():
    #agecohort 0 -- 0-4
    AG04GammaScale = 6
    AG04GammaShape = 2.1
    AG04AsymptomaticRate = random.randint(990,990)/1000
    AG04HospRate = random.randint(1,1)/100
    AG04MortalityRate = random.randint(1,2)/10000
      
    #agecohort 1 -- 5-17
    AG517GammaScale = 6
    AG517GammaShape = 3
    AG517AsymptomaticRate = random.randint(990,990)/1000
    AG517HospRate = random.randint(1,1)/100
    AG517MortalityRate = random.randint(1,2)/1000
    
    #agecohort 2 -- 18-49
    AG1849GammaScale = 6
    AG1849GammaShape = 2.5
    AG1849AsymptomaticRate = random.randint(80,80)/100
    AG1849HospRate = random.randint(10,10)/100
    AG1849MortalityRate = random.randint(6,8)/1000
     
    #agecohort 3 -- 50-64
    AG5064GammaScale = 6
    AG5064GammaShape = 2.3
    AG5064AsymptomaticRate = random.randint(80,80)/100
    AG5064HospRate = random.randint(25,25)/100
    AG5064MortalityRate = random.randint(13,15)/1000


    #agecohort 4 -- 65+
    AG65GammaScale = 6
    AG65GammaShape = 2.1
    AG65AsymptomaticRate = random.randint(80,90)/100
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
    PopulationParameters['householdcontactRate'] = random.randint(36,36)
    
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    
    ## Disease Progression Parameters
    DiseaseParameters['IncubationTime'] = random.randint(3,3)
    
    # gamma1
    DiseaseParameters['mildContagiousTime'] = random.randint(5,5)
    DiseaseParameters['AsymptomaticReducationTrans'] = random.randint(80,80)/100 #20%
    
    # gamma2
    DiseaseParameters['preContagiousTime'] = random.randint(2,2)  
    DiseaseParameters['symptomaticTime'] = random.randint(9,9)  # with symptomatic contact rate reduction similar to five days
    DiseaseParameters['postContagiousTime']	= random.randint(2,2)
    DiseaseParameters['symptomaticContactRateReduction'] = 1 #random.randint(80,90)/100 #10-20%
    
    DiseaseParameters['preHospTime'] = random.randint(5,5) 
    DiseaseParameters['hospitalSymptomaticTime'] = random.randint(5,5)
    DiseaseParameters['ICURate'] = random.randint(42,42)/100
    DiseaseParameters['ICUtime'] = random.randint(10,10)
    DiseaseParameters['PostICUTime'] = random.randint(4,4)
    DiseaseParameters['hospitalSymptomaticContactRateReduction'] = 1 #random.randint(40,50)/100
    
    
    DiseaseParameters['EDVisit'] = random.randint(80,80)/100 
    
    
    DiseaseParameters['ImportationRate'] = random.randint(5,5)
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = random.randint(4021,4021)/100000
    
    DiseaseParameters['QuarantineLookBackTime'] = 5
    DiseaseParameters['CommunityTestingRate'] = random.randint(5,5)/100
   
    
   
    
    return PopulationParameters, DiseaseParameters
  

def main(argv):
    
    #### This sets up folders for running the model in
    runs, OutputResultsFolder, FolderContainer, intname, debug = Utils.ModelFolderStructureSetup(argv)
    
    if debug:
        ParameterSet.logginglevel = 'debug'
        
    generatePresentationVals = 0 # set this to 1 if this is the only run across nodes to complete analysis - set to 0 if this is run across several nodes and use ProcessingDataForPresentation file as standalone afterwards to combine
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is
    Model = 'MDDCVAregion'  # select model - defines the model type to run
    
    ## Set the interventions to run here - each intervention should have a value for reductions
    interventionnames = ['base','variablebase','quarantinepassive','quarantinetest','quarantineQ']
    
    
    interventions = {}
    
    startdate = datetime(2020,2,10)
    enddate = datetime(2020,10,31)
    
    ###########################################################################################################################################
    #
    # Base - Constant Geographic variable Intervention Rates based on BA Proportion
    #
    ###########################################################################################################################################
    interventions['distance.base'] = {}
    interventions['distance.base']['type'] = 'distance'
    interventions['distance.base']['InterventionDate'] = (datetime(2020, 3, 25) - startdate).days
    interventions['distance.base']['InterventionReduction'] = []
    interventions['distance.base']['InterventionReductionLow'] = []
    interventions['distance.base']['SchoolInterventionReduction'] = []
    
    for i in range((datetime(2020, 3, 25) - startdate).days,(datetime(2020, 3, 31) - startdate).days):
        interventions['distance.base']['InterventionReduction'].append(.31)    
        interventions['distance.base']['InterventionReductionLow'].append(.72)
    
    for i in range((datetime(2020, 4, 1) - startdate).days,(datetime(2020, 10, 31) - startdate).days):
        interventions['distance.base']['InterventionReduction'].append(.15)    
        interventions['distance.base']['InterventionReductionLow'].append(.5)
        
    interventions['distance.base']['SchoolInterventionDate'] = (datetime(2020, 3, 15) - startdate).days
    for i in range((datetime(2020, 3, 15) - startdate).days,(datetime(2020, 3, 24) - startdate).days):
        interventions['distance.base']['SchoolInterventionReduction'].append(.25)
    interventions['distance.base']['SchoolInterventionReduction'].extend(interventions['distance.base']['InterventionReduction'])
    interventions['distance.base']['InterventionMobilityEffect'] = .72
    interventions['distance.base']['QuarantineType'] = ''
    interventions['distance.base']['PerFollowQuarantine'] = 0
    interventions['distance.base']['QuarantineStartDate'] = 500
    interventions['distance.base']['ContactTracing'] = 0
    interventions['distance.base']['testExtra'] = 0

    ###########################################################################################################################################
    #
    # Household Quarantine Only - Constant Geographic variable Intervention Rates based on BA Proportion
    #
    ###########################################################################################################################################
    interventions['distance.HHQonly'] = {}
    interventions['distance.HHQonly']['type'] = 'distance'
    interventions['distance.HHQonly']['InterventionDate'] = (datetime(2020, 3, 25) - startdate).days
    interventions['distance.HHQonly']['InterventionReduction'] = []
    interventions['distance.HHQonly']['InterventionReductionLow'] = []
    interventions['distance.HHQonly']['SchoolInterventionReduction'] = []
    
    for i in range((datetime(2020, 3, 25) - startdate).days,(datetime(2020, 3, 31) - startdate).days):
        interventions['distance.HHQonly']['InterventionReduction'].append(.311)    
        interventions['distance.HHQonly']['InterventionReductionLow'].append(.727)
    
    for i in range((datetime(2020, 4, 1) - startdate).days,(datetime(2020, 10, 31) - startdate).days):
        interventions['distance.HHQonly']['InterventionReduction'].append(.15)    
        interventions['distance.HHQonly']['InterventionReductionLow'].append(.5)
        
    interventions['distance.HHQonly']['SchoolInterventionDate'] = (datetime(2020, 3, 15) - startdate).days
    for i in range((datetime(2020, 3, 15) - startdate).days,(datetime(2020, 3, 24) - startdate).days):
        interventions['distance.HHQonly']['SchoolInterventionReduction'].append(.25)
    interventions['distance.HHQonly']['SchoolInterventionReduction'].extend(interventions['distance.HHQonly']['InterventionReduction'])
    interventions['distance.HHQonly']['InterventionMobilityEffect'] = .72
    interventions['distance.HHQonly']['QuarantineType'] = 'household'
    interventions['distance.HHQonly']['PerFollowQuarantine'] = 0.9
    interventions['distance.HHQonly']['QuarantineStartDate'] = (datetime(2020, 5, 15) - startdate).days
    interventions['distance.HHQonly']['ContactTracing'] = 0
    interventions['distance.HHQonly']['testExtra'] = 0
       
    ###########################################################################################################################################
    #
    # Full Quarantine and Test - Constant Geographic variable Intervention Rates based on BA Proportion
    #
    ###########################################################################################################################################
    interventions['distance.QAll'] = {}
    interventions['distance.QAll']['type'] = 'distance'
    interventions['distance.QAll']['InterventionDate'] = (datetime(2020, 3, 25) - startdate).days
    interventions['distance.QAll']['InterventionReduction'] = []
    interventions['distance.QAll']['InterventionReductionLow'] = []
    interventions['distance.QAll']['SchoolInterventionReduction'] = []
    
    for i in range((datetime(2020, 3, 25) - startdate).days,(datetime(2020, 3, 31) - startdate).days):
        interventions['distance.QAll']['InterventionReduction'].append(.311)    
        interventions['distance.QAll']['InterventionReductionLow'].append(.727)
    
    for i in range((datetime(2020, 4, 1) - startdate).days,(datetime(2020, 10, 31) - startdate).days):
        interventions['distance.QAll']['InterventionReduction'].append(.15)    
        interventions['distance.QAll']['InterventionReductionLow'].append(.5)
        
    interventions['distance.QAll']['SchoolInterventionDate'] = (datetime(2020, 3, 15) - startdate).days
    for i in range((datetime(2020, 3, 15) - startdate).days,(datetime(2020, 3, 24) - startdate).days):
        interventions['distance.QAll']['SchoolInterventionReduction'].append(.25)
    interventions['distance.QAll']['SchoolInterventionReduction'].extend(interventions['distance.QAll']['InterventionReduction'])
    interventions['distance.QAll']['InterventionMobilityEffect'] = .72
    interventions['distance.QAll']['QuarantineType'] = 'household'
    interventions['distance.QAll']['PerFollowQuarantine'] = 0.9
    interventions['distance.QAll']['QuarantineStartDate'] = (datetime(2020, 5, 15) - startdate).days
    interventions['distance.QAll']['ContactTracing'] = 1
    interventions['distance.QAll']['testExtra'] = 0
    
    ###########################################################################################################################################
    #
    # Full Quarantine, plus extra targeted testing - Constant Geographic variable Intervention Rates based on BA Proportion
    #
    ###########################################################################################################################################
    interventions['distance.QAllPlus'] = {}
    interventions['distance.QAllPlus']['type'] = 'distance'
    interventions['distance.QAllPlus']['InterventionDate'] = (datetime(2020, 3, 25) - startdate).days
    interventions['distance.QAllPlus']['InterventionReduction'] = []
    interventions['distance.QAllPlus']['InterventionReductionLow'] = []
    interventions['distance.QAllPlus']['SchoolInterventionReduction'] = []
    
    for i in range((datetime(2020, 3, 25) - startdate).days,(datetime(2020, 3, 31) - startdate).days):
        interventions['distance.QAllPlus']['InterventionReduction'].append(.311)    
        interventions['distance.QAllPlus']['InterventionReductionLow'].append(.727)
    
    for i in range((datetime(2020, 4, 1) - startdate).days,(datetime(2020, 10, 31) - startdate).days):
        interventions['distance.QAllPlus']['InterventionReduction'].append(.15)    
        interventions['distance.QAllPlus']['InterventionReductionLow'].append(.5)
        
    interventions['distance.QAllPlus']['SchoolInterventionDate'] = (datetime(2020, 3, 15) - startdate).days
    for i in range((datetime(2020, 3, 15) - startdate).days,(datetime(2020, 3, 24) - startdate).days):
        interventions['distance.QAllPlus']['SchoolInterventionReduction'].append(.25)
    interventions['distance.QAllPlus']['SchoolInterventionReduction'].extend(interventions['distance.QAllPlus']['InterventionReduction'])
    interventions['distance.QAllPlus']['InterventionMobilityEffect'] = .72
    interventions['distance.QAllPlus']['QuarantineType'] = 'household'
    interventions['distance.QAllPlus']['PerFollowQuarantine'] = 0.9
    interventions['distance.QAllPlus']['QuarantineStartDate'] = (datetime(2020, 5, 15) - startdate).days
    interventions['distance.QAllPlus']['ContactTracing'] = 1
    interventions['distance.QAllPlus']['testExtra'] = 1
    
    ###########################################################################################################################################
    #
    # Full Quarantine, plus extra targeted testing, open June 1 - Constant Geographic variable Intervention Rates based on BA Proportion
    #
    ###########################################################################################################################################
    interventions['distance.QAllPlusJune'] = {}
    interventions['distance.QAllPlusJune']['type'] = 'distance'
    interventions['distance.QAllPlusJune']['InterventionDate'] = (datetime(2020, 3, 25) - startdate).days
    interventions['distance.QAllPlusJune']['InterventionReduction'] = []
    interventions['distance.QAllPlusJune']['InterventionReductionLow'] = []
    interventions['distance.QAllPlusJune']['SchoolInterventionReduction'] = []
    
    interventions['distance.QAllPlusJune']['SchoolInterventionDate'] = (datetime(2020, 3, 15) - startdate).days
    for i in range((datetime(2020, 3, 15) - startdate).days,(datetime(2020, 3, 24) - startdate).days):
        interventions['distance.QAllPlusJune']['SchoolInterventionReduction'].append(.25)
    
    for i in range((datetime(2020, 3, 25) - startdate).days,(datetime(2020, 3, 31) - startdate).days):
        interventions['distance.QAllPlusJune']['InterventionReduction'].append(.311)    
        interventions['distance.QAllPlusJune']['InterventionReductionLow'].append(.727)
        interventions['distance.QAllPlusJune']['SchoolInterventionReduction'].append(.25)
        
    for i in range((datetime(2020, 4, 1) - startdate).days,(datetime(2020, 5, 31) - startdate).days):
        interventions['distance.QAllPlusJune']['InterventionReduction'].append(.15)    
        interventions['distance.QAllPlusJune']['InterventionReductionLow'].append(.5)
        interventions['distance.QAllPlusJune']['SchoolInterventionReduction'].append(.25)
                
    intval = .15
    intval2 = .5
    for i in range((datetime(2020, 6, 1) - startdate).days,(datetime(2020, 6, 30) - startdate).days):
        interventions['distance.QAllPlusJune']['InterventionReduction'].append(intval)
        interventions['distance.QAllPlusJune']['InterventionReductionLow'].append(intval2)
        interventions['distance.QAllPlusJune']['SchoolInterventionReduction'].append(.25)
        intval+=.01
    for i in range((datetime(2020, 7, 1) - startdate).days,(datetime(2020, 8, 31) - startdate).days):
        interventions['distance.QAllPlusJune']['InterventionReduction'].append(intval)
        interventions['distance.QAllPlusJune']['InterventionReductionLow'].append(intval2)
        interventions['distance.QAllPlusJune']['SchoolInterventionReduction'].append(.25)    
    for i in range((datetime(2020, 9, 1) - startdate).days,(datetime(2020, 10, 31) - startdate).days):
        interventions['distance.QAllPlusJune']['InterventionReduction'].append(intval)
        interventions['distance.QAllPlusJune']['InterventionReductionLow'].append(intval2)
        interventions['distance.QAllPlusJune']['SchoolInterventionReduction'].append(1)    
        
    interventions['distance.QAllPlusJune']['InterventionMobilityEffect'] = .72
    interventions['distance.QAllPlusJune']['QuarantineType'] = 'household'
    interventions['distance.QAllPlusJune']['PerFollowQuarantine'] = 0.9
    interventions['distance.QAllPlusJune']['QuarantineStartDate'] = (datetime(2020, 5, 15) - startdate).days
    interventions['distance.QAllPlusJune']['ContactTracing'] = 1
    interventions['distance.QAllPlusJune']['testExtra'] = 1
    
    
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
            endTime = (enddate - startdate).days
            DiseaseParameters['Intervention'] = key
            DiseaseParameters['InterventionDate'] = interventions[key]['InterventionDate']
            DiseaseParameters['InterventionReduction'] = interventions[key]['InterventionReduction']
            DiseaseParameters['InterventionReductionLow'] = interventions[key]['InterventionReductionLow']
            DiseaseParameters['SchoolInterventionDate'] = interventions[key]['SchoolInterventionDate']
            DiseaseParameters['SchoolInterventionReduction'] = interventions[key]['SchoolInterventionReduction']
            DiseaseParameters['InterventionMobilityEffect'] = interventions[key]['InterventionMobilityEffect']
            DiseaseParameters['QuarantineType'] = interventions[key]['QuarantineType']
            DiseaseParameters['QuarantineLookBackTime'] = 5
            DiseaseParameters['QuarantineStartDate'] = interventions[key]['QuarantineStartDate']    
            DiseaseParameters['TestingAvailabilityDateHosp'] = (datetime(2020, 3, 6) - startdate).days
            DiseaseParameters['TestingAvailabilityDateComm'] = (datetime(2020, 3, 21) - startdate).days
            DiseaseParameters['PerFollowQuarantine'] = interventions[key]['PerFollowQuarantine']
            DiseaseParameters['testExtra'] = interventions[key]['testExtra']
            DiseaseParameters['ContactTracing'] = interventions[key]['ContactTracing']
            
            resultsNameP = key + "_" + resultsName
                        
            GlobalModel.RunDefaultModelType('MDDCVA',modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,stepLength=1,writefolder=OutputResultsFolder,startDate=startdate)
            
            #ParameterSet.debugmodelevel = ParameterSet.debugerror
            #HospitalNames = GlobalModel.RunDefaultModelType(Model, modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,startDate=startdate,writefolder=OutputResultsFolder)
            #if generatePresentationVals == 1:
            #    ProcessDataForPresentation(interventionnames,HospitalNames,readFolder=OutputResultsFolder,writefolder=OutputResultsFolder,resultsName=overallResultsName)
                
       
            
        
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])
