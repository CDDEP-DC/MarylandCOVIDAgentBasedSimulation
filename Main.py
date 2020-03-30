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
        


    endTime = 181
    stepLength = 1
    dateTimeObj = datetime.now()
    resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                  str(dateTimeObj.microsecond)

    Model = 'Maryland'  # select model

    modelPopNames = 'Region'
    
    GlobalModel.cleanUp(modelPopNames)
    
    
    #Utils.JiggleParameters()

    ParameterSet.Intervention = 'baseline'
    
    ParameterSet.householdcontactRate = 9.416669817
    
    ParameterSet.AG04AsymptomaticRate = 0.956928299
    ParameterSet.AG04HospRate = 0
       
    #agecohort 1 -- 5-17
    ParameterSet.AG517AsymptomaticRate = 0.971991192
    ParameterSet.AG517HospRate = 0.006830413
            
    ParameterSet.AG1849AsymptomaticRate = 0.782286401
    ParameterSet.AG1849HospRate = 0.011035862
    
    #agecohort 3 -- 50-64
    ParameterSet.AG5064AsymptomaticRate = 0.591035463
    ParameterSet.AG5064HospRate = 0.029945799
    ParameterSet.AG5064MortalityRate = 0.08
    
    ParameterSet.AG65AsymptomaticRate = 0.687555538
    ParameterSet.AG65HospRate = 0.116097147
    ParameterSet.AG65MortalityRate = 0.15
    
    ParameterSet.IncubationTime = 11.39840259
    
    ParameterSet.totalContagiousTime = 2.071929174
    ParameterSet.hospitalSymptomaticTime = 17.07879755
    ParameterSet.hospTime = 7.963763528
    ParameterSet.EDVisit = 0.262533304
    ParameterSet.preContagiousTime = 1.039367955
    ParameterSet.postContagiousTime	= 8.477221814
    ParameterSet.householdcontactRate= 9.416669817
    ParameterSet.ImportationRate = 957
    ParameterSet.ImportationRatePower = 12.5904758


    ParameterSet.ProbabilityOfTransmissionPerContact = 0.029886591
    ParameterSet.ICURate = random.randint(40,60)/100
    ParameterSet.symptomaticContactRateReduction = 0.620313171
       
    ParameterSet.symptomaticContactRateReduction = random.randint(30,50)/100 
    
    ParameterSet.AGHospRate = [ParameterSet.AG04HospRate,ParameterSet.AG517HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG5064HospRate,ParameterSet.AG65HospRate]
    ParameterSet.AGAsymptomaticRate = [ParameterSet.AG04AsymptomaticRate, ParameterSet.AG517AsymptomaticRate, ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate, ParameterSet.AG5064AsymptomaticRate,ParameterSet.AG65AsymptomaticRate]
    ParameterSet.AGMortalityRate = [ParameterSet.AG04MortalityRate,ParameterSet.AG517MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG5064MortalityRate,ParameterSet.AG65MortalityRate]

    IncubationTime = 6.1
    totalContagiousTime = 9
    symptomaticTime = 6
    hospitalSymptomaticTime = 12
    hospTime = 4
    EDVisit = .8
    preContagiousTime = 2
    postContagiousTime = 6
    ICURate = .6
    ICUtime = 12
    PostICUTime = 5
    
    #ProbabilityOfTransmissionPerContact = .015 ## 0.015 --> 1.3-1.6
    ProbabilityOfTransmissionPerContact = 0.02
    
    
    RegionalList, numInfList, HospitalNames, LocationImportationRisk, RegionListGuide = GlobalModel.modelSetup(Model, modelPopNames,combineLocations=True)
    #ParameterSet.Intervention='SCHOOL'
    #ParameterSet.InterventionDate=44 #3/16 --> assumes 2/1 start
    #ParameterSet.InterventionReduction=.5

    GlobalModel.RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsName, numInfList,LocationImportationRisk=LocationImportationRisk, RegionListGuide=RegionListGuide)


    results = Utils.FileRead(ParameterSet.ResultsFolder + "/Results_" + resultsName + ".pickle")
    PostProcessing.WriteAggregatedResults(results,Model,resultsName,modelPopNames,RegionalList,HospitalNames,endTime)
    GlobalModel.cleanUp(modelPopNames)
        
if __name__ == "__main__":
    # execute only if run as a script
    main()
