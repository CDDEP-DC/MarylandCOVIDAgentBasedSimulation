


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

def JiggleParameters(case='low'):
    #agecohort 0 -- 0-4
    AG04GammaScale = 4.5
    AG04GammaShape = 2.1
    AG04AsymptomaticRate = random.randint(98,99)/100
    AG04HospRate = random.randint(8,10)/100
    AG04MortalityRate = random.randint(1,2)/10000
    
      
    #agecohort 1 -- 5-17
    AG517GammaScale = 4.5
    AG517GammaShape = 3
    AG517AsymptomaticRate = random.randint(98,99)/100
    AG517HospRate = random.randint(8,10)/100
    AG517MortalityRate = random.randint(1,2)/1000
        
    #agecohort 2 -- 18-49
    AG1849GammaScale = 4.5
    AG1849GammaShape = 2.5
    if case == 'low':
        AG1849AsymptomaticRate = random.randint(70,80)/100
    else:
        AG1849AsymptomaticRate = random.randint(90,94)/100
    AG1849HospRate = random.randint(10,12)/100
    AG1849MortalityRate = random.randint(6,8)/1000
         
    #agecohort 3 -- 50-64
    AG5064GammaScale = 4.5
    AG5064GammaShape = 2.3
    if case == 'low':
        AG5064AsymptomaticRate = random.randint(55,65)/100
    else:
        AG5064AsymptomaticRate = random.randint(85,90)/100
    AG5064HospRate = random.randint(20,30)/100
    AG5064MortalityRate = random.randint(2,10)/1000

    #agecohort 4 -- 65+
    AG65GammaScale = 4.5
    AG65GammaShape = 2.1
    if case == 'low':
        AG65AsymptomaticRate = random.randint(55,65)/100
    else:
        AG65AsymptomaticRate = random.randint(85,90)/100
    AG65HospRate = random.randint(45,55)/100
    AG65MortalityRate = random.randint(5,7)/100

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
    DiseaseParameters['IncubationTime'] = random.randint(5,7)
    DiseaseParameters['totalContagiousTime'] = random.randint(8,10)
    DiseaseParameters['hospitalSymptomaticTime'] = random.randint(12,14)
    DiseaseParameters['symptomaticTime'] = random.randint(5,7)
    DiseaseParameters['hospTime'] = random.randint(4,6) 
    DiseaseParameters['EDVisit'] = random.randint(60,80)/100 
    DiseaseParameters['preContagiousTime'] = random.randint(40,60)/100
    DiseaseParameters['postContagiousTime']	= random.randint(1,2)
    DiseaseParameters['ImportationRate'] = random.randint(1,3)
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = random.randint(90,100)/1000
    DiseaseParameters['ICURate'] = random.randint(40,50)/100
    DiseaseParameters['ICUtime'] = random.randint(9,11)
    DiseaseParameters['PostICUTime'] = random.randint(2,4)
    DiseaseParameters['symptomaticContactRateReduction'] = random.randint(30,40)/100 
    DiseaseParameters['AsymptomaticReducationTrans'] = random.randint(70,80)/100
    DiseaseParameters['symptomaticContactRateReduction'] = random.randint(55,65)/100
    
    
    return PopulationParameters, DiseaseParameters
  

def main():
    
    generatePresentationVals = 0 # set this to 1 if this is the only run across nodes to complete analysis - set to 0 if this is run across several nodes and use ProcessingDataForPresentation file as standalone afterwards to combine
    runs = 10000 # sets the number of times to run model - results print after each run to ensure that if the job fails the data is still there
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is
    Model = 'MDDCVAregion'  # select model - defines the model type to run
    
    ## Set the interventions to run here - each intervention should have a value for reductions
    #interventionnames = ['distance.9','distance.75','distance.5','distance.25','worse','altdistance.9','altdistance.5']
    #interventionnames = ['distance.95','distance.75','distance.5','distance.25','altdistance.9']
    interventionnames = ['baseline','distance.75','distance.50','distance.40','seasonalitydistance.75','seaonalitydistance.50']
    intervenionreduction1 = [1,.25,.5,.60,.25,.5]
    intervenionreduction2 = [0,0,0,0,0,0,0]
    intervenionreductionSchool = [1,.25,.5,.60,.25,.5]
    
    ## alter values related to transmission in Utils file
    
    ### Below here is model runs and should not be altered
    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
        
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
        
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
        
    OutputResultsFolder = ParameterSet.ResultsFolder + "/MDDCVAregionInt"
    if not os.path.exists(OutputResultsFolder):
        os.makedirs(OutputResultsFolder)
    else:
        for filename in os.listdir(OutputResultsFolder):
            if ".csv" in filename or ".pickle" in filename:
                os.remove(OutputResultsFolder+"/"+filename)
                
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MDDCVAregionInt/Results"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
    else:
        for filename in os.listdir(ParameterSet.ResultsFolder):
            if ".csv" in filename or ".pickle" in filename:
                os.remove(ParameterSet.ResultsFolder+"/"+filename)    
           
    
    GlobalModel.cleanUp(modelPopNames)
    
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
        
        caseval = 'high'
        if run % 2 == 0:
            caseval = 'low'
        PopulationParameters, DiseaseParameters = JiggleParameters(caseval)
            
        for intnum in range(0,len(interventionnames)):
            
            if 'seasonality' in interventionnames[intnum]:
                endTime = 300
            else:
                endTime = 300
            DiseaseParameters['Intervention'] = interventionnames[intnum]
            if 'distance' in interventionnames[intnum]:
                DiseaseParameters['InterventionDate'] = random.randint(46,50)
                DiseaseParameters['InterventionEndDate'] = ParameterSet.InterventionDate + 60
            else:
                DiseaseParameters['InterventionDate'] = -1
                DiseaseParameters['InterventionEndDate'] = -1
            DiseaseParameters['InterventionReduction'] = intervenionreduction1[intnum]
            DiseaseParameters['InterventionReduction2'] = intervenionreduction2[intnum]
            DiseaseParameters['InterventionReductionSchool'] = intervenionreductionSchool[intnum]
            DiseaseParameters['InterventionMobilityEffect'] = random.randint(10,20)
            
            resultsNameP = interventionnames[intnum] + "." + caseval + "_" + resultsName
            
            ParameterSet.debugmodelevel = ParameterSet.debugerror
            HospitalNames = GlobalModel.RunDefaultModelType(Model, modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,writefolder=OutputResultsFolder)
            
            if generatePresentationVals == 1:
                ProcessDataForPresentation(interventionnames,HospitalNames,readFolder=OutputResultsFolder,writefolder=OutputResultsFolder,resultsName=overallResultsName)
            
if __name__ == "__main__":
    # execute only if run as a script
    main()
