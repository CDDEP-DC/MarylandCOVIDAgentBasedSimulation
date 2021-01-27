
import sys, getopt
import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
from datetime import date
import os
import csv
import unicodedata
import string
import pandas as pd
import traceback
import copy


import PostProcessing
import ParameterSet
import Utils
import GlobalModel


def createParametersFile(Model,ParametersRunFileName,NumberMeanRuns = 5000):
    ParameterVals = getFitModelParameters(Model,NumberMeanRuns)
    csvFile = os.path.join('data',Model,ParametersRunFileName)
    try:
        with open(csvFile, 'a+') as f:
            f.write("key,")
            lpvals = ParameterVals[0]
            for key2 in lpvals.keys():
                f.write(key2+",")
            f.write("\n")
            for key in ParameterVals.keys():
                f.write(str(key)+",")
                lpvals = ParameterVals[key]
                for key2 in lpvals.keys():
                    f.write(str(lpvals[key2])+",")
                f.write("\n")

    except Exception as e:
        print("I/O Error writing CurrentFittingParams.")
        if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
            print(traceback.format_exc())
        exit()    
        
        
def getFitModelParameters(Model,NumberMeanRuns = 5000, append=False):
    
    

    # Load the parameters
    input_df = None
    try:
        ParametersFileName = os.path.join('data','Parameters.csv')
        with open(ParametersFileName, mode='r') as infile:
            reader = csv.reader(infile)
            ParametersInputData = {}
            for rows in reader:
                minmaxvals = {}                    
                minmaxvals['min'] = rows[1]
                minmaxvals['max'] = rows[2]
                ParametersInputData[rows[0]] = minmaxvals
                
    except Exception as e:
        print("Parameter input error. Please confirm the parameter file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
            print(traceback.format_exc())
        exit() 
        
    

    ### Range for Start Date
                            
    startDateUL = 29
    startDateLL = 1
    
    AG04AsymptomaticRateUL = float(ParametersInputData['AG04AsymptomaticRate']['max'])
    AG04AsymptomaticRateLL = float(ParametersInputData['AG04AsymptomaticRate']['min'])
    AG04HospRateUL = float(ParametersInputData['AG04HospRate']['max'])
    AG04HospRateLL = float(ParametersInputData['AG04HospRate']['min'])
    
    
    AG517AsymptomaticRateUL = float(ParametersInputData['AG517AsymptomaticRate']['max'])
    AG517AsymptomaticRateLL = float(ParametersInputData['AG517AsymptomaticRate']['min'])
    AG517HospRateUL = float(ParametersInputData['AG517HospRate']['max'])
    AG517HospRateLL = float(ParametersInputData['AG517HospRate']['min'])
    
    
    AG1849AsymptomaticRateUL = float(ParametersInputData['AG1849AsymptomaticRate']['max'])
    AG1849AsymptomaticRateLL = float(ParametersInputData['AG1849AsymptomaticRate']['min'])
    AG1849HospRateUL = float(ParametersInputData['AG1849HospRate']['max'])
    AG1849HospRateLL = float(ParametersInputData['AG1849HospRate']['min'])
    
    
    AG5064AsymptomaticRateUL = float(ParametersInputData['AG5064AsymptomaticRate']['max'])
    AG5064AsymptomaticRateLL = float(ParametersInputData['AG5064AsymptomaticRate']['min'])
    AG5064HospRateUL = float(ParametersInputData['AG5064HospRate']['max'])
    AG5064HospRateLL = float(ParametersInputData['AG5064HospRate']['min'])
    
    
    AG65AsymptomaticRateUL = float(ParametersInputData['AG65AsymptomaticRate']['max'])
    AG65AsymptomaticRateLL = float(ParametersInputData['AG65AsymptomaticRate']['min'])
    AG65HospRateUL = float(ParametersInputData['AG65HospRate']['max'])
    AG65HospRateLL = float(ParametersInputData['AG65HospRate']['min'])
    
    
    AG04MortalityRateUL = float(ParametersInputData['AG04MortalityRate']['max'])
    AG04MortalityRateLL = float(ParametersInputData['AG04MortalityRate']['min'])
    AG517MortalityRateUL = float(ParametersInputData['AG517MortalityRate']['max'])
    AG517MortalityRateLL = float(ParametersInputData['AG517MortalityRate']['min'])
    AG1849MortalityRateUL = float(ParametersInputData['AG1849MortalityRate']['max'])
    AG1849MortalityRateLL = float(ParametersInputData['AG1849MortalityRate']['min'])
    AG5064MortalityRateUL = float(ParametersInputData['AG5064MortalityRate']['max'])
    AG5064MortalityRateLL = float(ParametersInputData['AG5064MortalityRate']['min'])
    AG65MortalityRateUL = float(ParametersInputData['AG65MortalityRate']['max'])
    AG65MortalityRateLL = float(ParametersInputData['AG65MortalityRate']['min'])
    
    IncubationTimeUL = float(ParametersInputData['IncubationTime']['max'])
    IncubationTimeLL = float(ParametersInputData['IncubationTime']['min'])
    mildContagiousTimeUL = float(ParametersInputData['mildContagiousTime']['max'])
    mildContagiousTimeLL = float(ParametersInputData['mildContagiousTime']['min'])
    symptomaticTimeUL = float(ParametersInputData['symptomaticTime']['max'])
    symptomaticTimeLL = float(ParametersInputData['symptomaticTime']['min'])
    hospitalSymptomaticTimeUL = float(ParametersInputData['hospitalSymptomaticTime']['max'])
    hospitalSymptomaticTimeLL = float(ParametersInputData['hospitalSymptomaticTime']['min'])
    ICURateUL = float(ParametersInputData['ICURate']['max'])
    ICURateLL = float(ParametersInputData['ICURate']['min'])
    PostICUTimeUL = float(ParametersInputData['PostICUTime']['max'])
    PostICUTimeLL = float(ParametersInputData['PostICUTime']['min'])
    ICUtimeUL = float(ParametersInputData['ICUtime']['max'])
    ICUtimeLL = float(ParametersInputData['ICUtime']['min'])
    
    preHospTimeUL = float(ParametersInputData['preHospTime']['max'])
    preHospTimeLL = float(ParametersInputData['preHospTime']['min'])
    EDVisitUL = float(ParametersInputData['EDVisit']['max'])
    EDVisitLL = float(ParametersInputData['EDVisit']['min'])
    preContagiousTimeUL = float(ParametersInputData['preContagiousTime']['max'])
    preContagiousTimeLL = float(ParametersInputData['preContagiousTime']['min'])
    postContagiousTimeUL = float(ParametersInputData['postContagiousTime']['max'])
    postContagiousTimeLL = float(ParametersInputData['postContagiousTime']['min'])
    ProbabilityOfTransmissionPerContactUL = float(ParametersInputData['ProbabilityOfTransmissionPerContact']['max'])
    ProbabilityOfTransmissionPerContactLL = float(ParametersInputData['ProbabilityOfTransmissionPerContact']['min'])
    symptomaticContactRateReductionUL = float(ParametersInputData['symptomaticContactRateReduction']['max'])
    symptomaticContactRateReductionLL = float(ParametersInputData['symptomaticContactRateReduction']['min'])
    hospitalSymptomaticContactRateReductionUL = float(ParametersInputData['hospitalSymptomaticContactRateReduction']['max'])
    hospitalSymptomaticContactRateReductionLL = float(ParametersInputData['hospitalSymptomaticContactRateReduction']['min'])
    
    ImportationRateUL = 10
    ImportationRateLL = 1
    
    InterventionRateUL = 39
    InterventionRateLL = 9
    
    InterventionRateLowUL = 65
    InterventionRateLowLL = 40
    
    InterventionMobilityEffectUL = 90
    InterventionMobilityEffectLL = 70
    
    InterventionPerIncreaseUL = 50
    InterventionPerIncreaseLL = 10
    
    AsymptomaticReducationTransUL = float(ParametersInputData['AsymptomaticReducationTrans']['max'])
    AsymptomaticReducationTransLL = float(ParametersInputData['AsymptomaticReducationTrans']['min'])
    
    householdcontactRateUL = float(ParametersInputData['householdcontactRate']['max'])
    householdcontactRateLL = float(ParametersInputData['householdcontactRate']['min'])

    TestIncreaseUL = float(ParametersInputData['TestIncrease']['max'])
    TestIncreaseLL = float(ParametersInputData['TestIncrease']['min'])
    
    
    #Initialize Parameters
    ParameterVals = {}
    startnum = 0
    if append:
        csvFile = os.path.join('data',Model,"CurrentFittingParams.csv")
        csvFile2 = os.path.join('data',Model,"CurrentFittingParamsShuffle.csv")
        if os.path.exists(csvFile):
            with open(csvFile,'r') as ip:
                data=ip.readlines()
            header, rest=data[0], data[1:]
            random.shuffle(rest)
            with open(csvFile2,'w') as out:
                out.write(''.join([header]+rest))
     
            file1 = open(csvFile2, 'r') 
            csv_reader = csv.reader(file1)
            headers = next(csv_reader)
            
            for row in csv_reader:
                ParameterVals[startnum] = { 'startDate':row[headers.index('startdate')], 
                    'AG04AsymptomaticRate':row[headers.index('AG04AsymptomaticRate')],
                    'AG04HospRate':row[headers.index('AG04HospRate')],
                    'AG04MortalityRate':row[headers.index('AG04MortalityRate')],
                    'AG517AsymptomaticRate':row[headers.index('AG517AsymptomaticRate')],
                    'AG517HospRate':row[headers.index('AG517HospRate')],
                    'AG517MortalityRate':row[headers.index('AG517MortalityRate')],
                    'AG1849AsymptomaticRate':row[headers.index('AG1849AsymptomaticRate')],
                    'AG1849HospRate':row[headers.index('AG1849HospRate')],
                    'AG1849MortalityRate':row[headers.index('AG1849MortalityRate')],
                    'AG5064AsymptomaticRate':row[headers.index('AG5064AsymptomaticRate')],
                    'AG5064HospRate':row[headers.index('AG5064HospRate')],
                    'AG5064MortalityRate':row[headers.index('AG5064MortalityRate')],
                    'AG65AsymptomaticRate':row[headers.index('AG65AsymptomaticRate')],
                    'AG65HospRate':row[headers.index('AG65HospRate')],
                    'AG65MortalityRate':row[headers.index('AG65MortalityRate')],
                    'IncubationTime':row[headers.index('IncubationTime')],
                    'mildContagiousTime':row[headers.index('mildContagiousTime')],
                    'symptomaticTime':row[headers.index('symptomaticTime')],
                    'hospitalSymptomaticTime':row[headers.index('hospitalSymptomaticTime')],
                    'ICURate':row[headers.index('ICURate')],
                    'ICUtime':row[headers.index('ICUtime')],
                    'PostICUTime':row[headers.index('PostICUTime')],
                    'preHospTime':row[headers.index('preHospTime')],
                    'EDVisit':row[headers.index('EDVisit')],
                    'preContagiousTime':row[headers.index('preContagiousTime')],
                    'postContagiousTime':row[headers.index('postContagiousTime')],
                    'NumInfStart':row[headers.index('NumInfStart')],
                    'householdcontactRate':row[headers.index('householdcontactRate')],
                    'ProbabilityOfTransmissionPerContact':row[headers.index('ProbabilityOfTransmissionPerContact')],
                    'symptomaticContactRateReduction':row[headers.index('symptomaticContactRateReduction')],
                    'hospitalSymptomaticContactRateReduction':row[headers.index('hospitalSymptomaticContactRateReduction')],
                    'ImportationRate':row[headers.index('ImportationRate')],
                    'InterventionRate':row[headers.index('InterventionRate')],
                    'InterventionRateLow':row[headers.index('InterventionRateLow')],
                    'InterventionMobilityEffect':row[headers.index('InterventionMobilityEffect')],
                    'AsymptomaticReducationTrans':row[headers.index('AsymptomaticReducationTrans')],
                    'InterventionPerIncrease':row[headers.index('InterventionPerIncrease')],
                    'locked':0,
                    'InterventionEndPerIncrease':row[headers.index('InterventionEndPerIncrease')],
                    'TestIncrease':row[headers.index('TestIncrease')]
                }
                startnum += 1
                
        print(len(ParameterVals))
    
    for nrun in range(startnum,startnum+NumberMeanRuns):
        startDate = date(2020,2,random.randint(startDateLL,startDateUL))
        AG04AsymptomaticRate = random.random()*(AG04AsymptomaticRateUL - AG04AsymptomaticRateLL) + AG04AsymptomaticRateLL
        AG04HospRate = random.random()*(AG04HospRateUL - AG04HospRateLL) + AG04HospRateLL
        AG04MortalityRate = random.random()*(AG04MortalityRateUL - AG04MortalityRateLL) + AG04MortalityRateLL
        
        AG517AsymptomaticRate = random.random()*(AG517AsymptomaticRateUL - AG517AsymptomaticRateLL) + AG517AsymptomaticRateLL
        AG517HospRate = random.random()*(AG517HospRateUL - AG517HospRateLL) + AG517HospRateLL
        AG517MortalityRate = random.random()*(AG517MortalityRateUL - AG517MortalityRateLL) + AG517MortalityRateLL
        
        AG1849AsymptomaticRate = random.random()*(AG1849AsymptomaticRateUL - AG1849AsymptomaticRateLL) + AG1849AsymptomaticRateLL
        AG1849HospRate = random.random()*(AG1849HospRateUL - AG1849HospRateLL) + AG1849HospRateLL
        AG1849MortalityRate = random.random()*(AG1849MortalityRateUL - AG1849MortalityRateLL) + AG1849MortalityRateLL
        
        AG5064AsymptomaticRate = random.random()*(AG5064AsymptomaticRateUL - AG5064AsymptomaticRateLL) + AG5064AsymptomaticRateLL
        AG5064HospRate = random.random()*(AG5064HospRateUL - AG5064HospRateLL) + AG5064HospRateLL
        AG5064MortalityRate = random.random()*(AG5064MortalityRateUL - AG5064MortalityRateLL) + AG5064MortalityRateLL
        
        AG65AsymptomaticRate = random.random()*(AG65AsymptomaticRateUL - AG65AsymptomaticRateLL) + AG65AsymptomaticRateLL
        AG65HospRate = random.random()*(AG65HospRateUL - AG65HospRateLL) + AG65HospRateLL
        AG65MortalityRate = random.random()*(AG65MortalityRateUL - AG65MortalityRateLL) + AG65MortalityRateLL
        
        IncubationTime = random.random()*(IncubationTimeUL - IncubationTimeLL) + IncubationTimeLL
        mildContagiousTime = random.random()*(mildContagiousTimeUL - mildContagiousTimeLL) + mildContagiousTimeLL
        symptomaticTime = random.random()*(symptomaticTimeUL - symptomaticTimeLL) + symptomaticTimeLL
        hospitalSymptomaticTime = random.random()*(hospitalSymptomaticTimeUL - hospitalSymptomaticTimeLL) + hospitalSymptomaticTimeLL
        
        ICURate = random.random()*(ICURateUL - ICURateLL) + ICURateLL
        ICUtime = random.random()*(ICUtimeUL - ICUtimeLL) + ICUtimeLL 
        PostICUTime = random.random()*(PostICUTimeUL - PostICUTimeLL) + PostICUTimeLL
        
        preHospTime = random.random()*(preHospTimeUL - preHospTimeLL) + preHospTimeLL
        EDVisit = random.random()*(EDVisitUL - EDVisitLL) + EDVisitLL
        preContagiousTime = random.random()*(preContagiousTimeUL - preContagiousTimeLL) + preContagiousTimeLL
        postContagiousTime = random.random()*(postContagiousTimeUL - postContagiousTimeLL) + postContagiousTimeLL
        householdcontactRate = random.random()*(householdcontactRateUL - householdcontactRateLL) + householdcontactRateLL
        
        ImportationRate = random.randint(ImportationRateLL,ImportationRateUL)
        InterventionRate = random.randint(InterventionRateLL,InterventionRateUL)/100
        InterventionRateLow = random.randint(InterventionRateLowLL,InterventionRateLowUL)/100
        
        InterventionPerIncrease = random.randint(InterventionPerIncreaseLL,InterventionPerIncreaseUL)/100
        
        InterventionMobilityEffect = random.randint(InterventionMobilityEffectLL,InterventionMobilityEffectUL)/100
                
        AsymptomaticReducationTrans = random.random()*(AsymptomaticReducationTransUL - AsymptomaticReducationTransLL) + AsymptomaticReducationTransLL
        
        InterventionEndPerIncrease = random.random()*(1 - .1) + .1
        
        ProbabilityOfTransmissionPerContact = random.random()*(ProbabilityOfTransmissionPerContactUL - ProbabilityOfTransmissionPerContactLL) + ProbabilityOfTransmissionPerContactLL
        symptomaticContactRateReduction = random.random()*(symptomaticContactRateReductionUL - symptomaticContactRateReductionLL) + symptomaticContactRateReductionLL
        hospitalSymptomaticContactRateReduction = random.random()*(hospitalSymptomaticContactRateReductionUL - hospitalSymptomaticContactRateReductionLL) + hospitalSymptomaticContactRateReductionLL
        
        TestIncrease = random.random()*(TestIncreaseUL - TestIncreaseLL) + TestIncreaseLL

        ParameterVals[nrun] = { 'startDate':startDate, 
            'AG04AsymptomaticRate':AG04AsymptomaticRate,
            'AG04HospRate':AG04HospRate,
            'AG04MortalityRate':AG04MortalityRate,
            'AG517AsymptomaticRate':AG517AsymptomaticRate,
            'AG517HospRate':AG517HospRate,
            'AG517MortalityRate':AG517MortalityRate,
            'AG1849AsymptomaticRate':AG1849AsymptomaticRate,
            'AG1849HospRate':AG1849HospRate,
            'AG1849MortalityRate':AG1849MortalityRate,
            'AG5064AsymptomaticRate':AG5064AsymptomaticRate,
            'AG5064HospRate':AG5064HospRate,
            'AG5064MortalityRate':AG5064MortalityRate,
            'AG65AsymptomaticRate':AG65AsymptomaticRate,
            'AG65HospRate':AG65HospRate,
            'AG65MortalityRate':AG65MortalityRate,
            'IncubationTime':IncubationTime,
            'mildContagiousTime':mildContagiousTime,
            'symptomaticTime':symptomaticTime,
            'hospitalSymptomaticTime':hospitalSymptomaticTime,
            'ICURate':ICURate,
            'ICUtime':ICUtime,
            'PostICUTime':PostICUTime,
            'preHospTime':preHospTime,
            'EDVisit':EDVisit,
            'preContagiousTime':preContagiousTime,
            'postContagiousTime':postContagiousTime,
            'NumInfStart':random.randint(1,100),
            'householdcontactRate':householdcontactRate,
            'ProbabilityOfTransmissionPerContact':ProbabilityOfTransmissionPerContact,
            'symptomaticContactRateReduction':symptomaticContactRateReduction,
            'hospitalSymptomaticContactRateReduction':hospitalSymptomaticContactRateReduction,
            'ImportationRate':ImportationRate,
            'InterventionRate':InterventionRate,
            'InterventionRateLow':InterventionRateLow,
            'InterventionMobilityEffect':InterventionMobilityEffect,
            'AsymptomaticReducationTrans':AsymptomaticReducationTrans,
            'InterventionPerIncrease':InterventionPerIncrease,
            'locked':0,
            'InterventionEndPerIncrease':InterventionEndPerIncrease,
            'TestIncrease':TestIncrease
        }
    print(len(ParameterVals))    
    return ParameterVals
    

