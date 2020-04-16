# -----------------------------------------------------------
# Main.py is the executable that runs the entire model
# -----------------------------------------------------------


# from WorkerProcess import WorkerThread

# Main Run File


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
import agents.AgentClasses
import events.SimulationEvent as SE

               

def main():

    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
        
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
        
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
        
    endTime = 60
    stepLength = 1
    dateTimeObj = datetime.now()
    resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                  str(dateTimeObj.microsecond)

    Model = 'MDDCVAregion'  # select model

    modelPopNames = 'GermanyRegion'
    
    GlobalModel.cleanUp(modelPopNames)
        
    
    # These can be setup however needed for a specific location - could bring them in as lists   
    # However many age groups can be added here - this is specific for here - just need to add for all groups the same number
    #agecohort 0 -- 0-4
    AG04GammaScale = 5
    AG04GammaShape = 2.1
    AG04AsymptomaticRate = 0.95
    AG04HospRate = 0
    AG04MortalityRate = 0.001
      
    #agecohort 1 -- 5-17
    AG517GammaScale = 5
    AG517GammaShape = 3
    AG517AsymptomaticRate = 0.9
    AG517HospRate = 0.006830413
    AG517MortalityRate = 0.001
    
    #agecohort 2 -- 18-49
    AG1849GammaScale = 5
    AG1849GammaShape = 2.5
    AG1849AsymptomaticRate = 0.7
    AG1849HospRate = 0.011035862
    AG1849MortalityRate = 0.001
     
    #agecohort 3 -- 50-64
    AG5064GammaScale = 5
    AG5064GammaShape = 2.3
    AG5064AsymptomaticRate = 0.6
    AG5064HospRate = 0.029945799
    AG5064MortalityRate = 0.08
            
    #agecohort 4 -- 65+
    AG65GammaScale = 5
    AG65GammaShape = 2.1
    AG65AsymptomaticRate = 0.6
    AG65HospRate = 0.20
    AG65MortalityRate = 0.15
        
    householdcontactRate = 9.416669817
    
    AgeCohortInteraction = {0:{0:1.39277777777778,	1:0.328888888888889,	2:0.299444444444444,	3:0.224444444444444,	4:0.108333333333333},
                                    1:{0:0.396666666666667,	1:2.75555555555556,	2:0.342407407407407,	3:0.113333333333333,	4:0.138333333333333},
                                    2:{0:0.503333333333333,	1:1.22666666666667,	2:1.035,	3:0.305185185185185,	4:0.180555555555556},
                                    3:{0:0.268888888888889,	1:0.164074074074074, 2:0.219444444444444,	3:0.787777777777778,	4:0.27},
                                    4:{0:0.181666666666667,	1:0.138888888888889, 2:0.157222222222222,	3:0.271666666666667,	4:0.703333333333333}}

    
    PopulationParameters = {}
    
    DiseaseParameters = {}
    
    DiseaseParameters['AGHospRate'] = [AG04HospRate,AG517HospRate,AG1849HospRate,AG1849HospRate,AG1849HospRate,AG5064HospRate,AG65HospRate]
    DiseaseParameters['AGAsymptomaticRate'] = [AG04AsymptomaticRate, AG517AsymptomaticRate, AG1849AsymptomaticRate,AG1849AsymptomaticRate,AG1849AsymptomaticRate, AG5064AsymptomaticRate,AG65AsymptomaticRate]
    DiseaseParameters['AGMortalityRate'] = [AG04MortalityRate,AG517MortalityRate,AG1849MortalityRate,AG1849MortalityRate,AG1849MortalityRate,AG5064MortalityRate,AG65MortalityRate]
            
    PopulationParameters['AGGammaScale'] = [AG04GammaScale,AG517GammaScale,AG1849GammaScale,AG1849GammaScale,AG1849GammaScale,AG5064GammaScale,AG65GammaScale]
    PopulationParameters['AGGammaShape'] = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG1849GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
    PopulationParameters['householdcontactRate'] = householdcontactRate
    
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    
    ## Disease Progression Parameters
    DiseaseParameters['IncubationTime'] = 11.39840259
    DiseaseParameters['totalContagiousTime'] = 2.071929174
    DiseaseParameters['hospitalSymptomaticTime'] = 17.07879755
    DiseaseParameters['symptomaticTime'] = 6
    DiseaseParameters['hospTime'] = 7.963763528
    DiseaseParameters['EDVisit'] = 0.262533304
    DiseaseParameters['preContagiousTime'] = 1.039367955
    DiseaseParameters['postContagiousTime']	= 8.477221814
    DiseaseParameters['ImportationRate'] = 30
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = 0.029886591
    DiseaseParameters['ICURate'] = random.randint(40,60)/100
    DiseaseParameters['ICUtime'] = 10
    DiseaseParameters['PostICUTime'] = 10
    DiseaseParameters['symptomaticContactRateReduction'] = 0.620313171
    DiseaseParameters['AsymptomaticReducationTrans'] = .3
    DiseaseParameters['symptomaticContactRateReduction'] = random.randint(30,50)/100 
    
    ## Intervention Information
    DiseaseParameters['Intervention'] = 'baseline'
    DiseaseParameters['InterventionDate'] = -1
    DiseaseParameters['InterventionEndDate'] = -1
    DiseaseParameters['InterventionReductionSchool'] = 1        
    DiseaseParameters['InterventionReduction2'] = 1
    DiseaseParameters['InterventionReduction'] = 1
            
    results = GlobalModel.RunFitModelType(Model, modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime)
    print(results)
    
    
        
if __name__ == "__main__":
    # execute only if run as a script
    main()
