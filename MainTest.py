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
    AG04MortalityRate = random.randint(1,1)/10000
      
    #agecohort 1 -- 5-17
    AG517GammaScale = 6
    AG517GammaShape = 3
    AG517AsymptomaticRate = random.randint(990,990)/1000
    AG517HospRate = random.randint(1,1)/100
    AG517MortalityRate = random.randint(1,1)/1000
    
    #agecohort 2 -- 18-49
    AG1849GammaScale = 6
    AG1849GammaShape = 2.5
    AG1849AsymptomaticRate = random.randint(80,80)/100
    AG1849HospRate = random.randint(10,10)/100
    AG1849MortalityRate = random.randint(6,6)/1000
     
    #agecohort 3 -- 50-64
    AG5064GammaScale = 6
    AG5064GammaShape = 2.3
    AG5064AsymptomaticRate = random.randint(80,80)/100
    AG5064HospRate = random.randint(25,25)/100
    AG5064MortalityRate = random.randint(13,13)/1000


    #agecohort 4 -- 65+
    AG65GammaScale = 6
    AG65GammaShape = 2.1
    AG65AsymptomaticRate = random.randint(80,80)/100
    AG65HospRate = random.randint(50,50)/100
    AG65MortalityRate = random.randint(36,36)/100

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
    PopulationParameters['householdcontactRate'] = random.randint(37,37)
    
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
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = random.randint(35,42)/1000
    
    DiseaseParameters['QuarantineLookBackTime'] = 5
    DiseaseParameters['CommunityTestingRate'] = random.randint(5,5)/100
   
    
   
    
    return PopulationParameters, DiseaseParameters
  

def main(argv):
    
    #### This sets up folders for running the model in
    runs, OutputResultsFolder, FolderContainer, intname, debug = Utils.ModelFolderStructureSetup(argv)
    
    if debug:
        ParameterSet.logginglevel = 'debug'
    ParameterSet.logginglevel = 'test'    
    generatePresentationVals = 0 # set this to 1 if this is the only run across nodes to complete analysis - set to 0 if this is run across several nodes and use ProcessingDataForPresentation file as standalone afterwards to combine
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is
    Model = 'MDDCVAregion'  # select model - defines the model type to run
    
    ## Set the interventions to run here - each intervention should have a value for reductions
    interventionnames = ['base','variablebase','quarantinepassive','quarantinetest','quarantineQ']
    
    
    interventions = {}
    
    startdate = datetime(2020,2,10)
    enddate = datetime(2020,5,15)
    
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
    
    for i in range((datetime(2020, 3, 25) - startdate).days,(datetime(2020, 10, 31) - startdate).days):
        interventions['distance.base']['InterventionReduction'].append(.15)    
        interventions['distance.base']['InterventionReductionLow'].append(.6)
        
    interventions['distance.base']['SchoolInterventionDate'] = (datetime(2020, 3, 15) - startdate).days
    for i in range((datetime(2020, 3, 15) - startdate).days,(datetime(2020, 3, 24) - startdate).days):
        interventions['distance.base']['SchoolInterventionReduction'].append(.25)
    interventions['distance.base']['SchoolInterventionReduction'].extend(interventions['distance.base']['InterventionReduction'])
    interventions['distance.base']['InterventionMobilityEffect'] = .5
    interventions['distance.base']['QuarantineType'] = ''
    interventions['distance.base']['PerFollowQuarantine'] = 0
    interventions['distance.base']['QuarantineStartDate'] = 500
    interventions['distance.base']['ContactTracing'] = 0
    interventions['distance.base']['testExtra'] = 0

    
    ## alter values related to transmission in Utils file
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
    
    dateTimeObj = datetime.now()
    resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                  str(dateTimeObj.microsecond)
    
    finalvals = {}               
    for run in range(0,runs):
        stepLength = 1
        
        PopulationParameters, DiseaseParameters = JiggleParameters()
            
        #for intnum in range(0,len(interventionnames)):
        for key in interventions.keys():
            print(key)
            endTime = (enddate - startdate).days
            DiseaseParameters['Intervention'] = key
            DiseaseParameters['InterventionDate'] = interventions[key]['InterventionDate']
            intredval = random.randint(10,30)/100
            intredvallow = random.randint(50,70)/100
            for x in range(0,len(interventions[key]['InterventionReduction'])):
                interventions[key]['InterventionReduction'][x] = intredval
                interventions[key]['InterventionReductionLow'][x] = intredvallow
                
            DiseaseParameters['InterventionReduction'] = interventions[key]['InterventionReduction']
            DiseaseParameters['InterventionReductionLow'] = interventions[key]['InterventionReductionLow']
            DiseaseParameters['SchoolInterventionDate'] = interventions[key]['SchoolInterventionDate']
            DiseaseParameters['SchoolInterventionReduction'] = interventions[key]['SchoolInterventionReduction']
            DiseaseParameters['InterventionMobilityEffect'] = random.randint(50,100)/100 #interventions[key]['InterventionMobilityEffect']
            DiseaseParameters['QuarantineType'] = interventions[key]['QuarantineType']
            DiseaseParameters['QuarantineLookBackTime'] = 5
            DiseaseParameters['QuarantineStartDate'] = interventions[key]['QuarantineStartDate']    
            DiseaseParameters['TestingAvailabilityDateHosp'] = (datetime(2020, 3, 6) - startdate).days
            DiseaseParameters['TestingAvailabilityDateComm'] = (datetime(2020, 3, 21) - startdate).days
            DiseaseParameters['PerFollowQuarantine'] = interventions[key]['PerFollowQuarantine']
            DiseaseParameters['testExtra'] = interventions[key]['testExtra']
            DiseaseParameters['ContactTracing'] = interventions[key]['ContactTracing']
            
            resultsNameP = key + "_" + resultsName
                        
            results = GlobalModel.RunFitModelType('MDDCVA',modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,startDate=startdate)

                        
            keyvals = ['H','numTests','CC']
            colvals = ['Hospitalized','Tests','confirmedcases']
            
            HMD = [0]*len(results.keys())
            MDTests = [0]*len(results.keys())
            MDCC = [0]*len(results.keys())
            # now go through the results and add the results as totals to each bucket
            print(results.keys())
            for day in results.keys():
                numInfList = results[day]
                for reg in numInfList.keys():
                    rdict = numInfList[reg]
                    for rkey in rdict:
                        lpdict = rdict[rkey]
                        regionalval = lpdict['regionalid']
                        if regionalval == "MD":
                            HMD[day-1] += lpdict['H']
                            MDTests[day-1] += lpdict['numTests']
                            MDCC[day-1] += lpdict['CC']            
            
            finalvalsw = {
                'ProbabilityOfTransmissionPerContact':DiseaseParameters['ProbabilityOfTransmissionPerContact'],
                'InterventionReduction':intredval,
                'InterventionReductionLow':intredvallow,
                'ImportationRate':DiseaseParameters['ImportationRate'],
                'InterventionMobilityEffect':DiseaseParameters['InterventionMobilityEffect'],
                'Hospitalized':HMD,
                'Tests':MDTests,
                'MDCC':MDCC
            }
            print(finalvalsw)
            if os.path.exists(os.path.join(OutputResultsFolder,"MarylandFitVals_"+resultsNameP+".pickle")):
                finalvals = Utils.PickleFileRead(os.path.join(OutputResultsFolder,"MarylandFitVals_"+resultsNameP+".pickle"))
            finalvals[run] = finalvalsw
            print(os.path.join(OutputResultsFolder,"MarylandFitVals_"+resultsNameP+".pickle"))
            Utils.PickleFileWrite(os.path.join(OutputResultsFolder,"MarylandFitVals_"+resultsNameP+".pickle"),finalvals)
            #ParameterSet.debugmodelevel = ParameterSet.debugerror
            #HospitalNames = GlobalModel.RunDefaultModelType(Model, modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,startDate=startdate,writefolder=OutputResultsFolder)
            #if generatePresentationVals == 1:
            #    ProcessDataForPresentation(interventionnames,HospitalNames,readFolder=OutputResultsFolder,writefolder=OutputResultsFolder,resultsName=overallResultsName)
                
       
            
        
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])
