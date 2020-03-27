

import random
import numpy as np
import math
from statistics import mean
import time
import pickle
from datetime import datetime
from datetime import timedelta  
import os
import csv

import PostProcessing
import ParameterSet
import Utils
import GlobalModel


def main():
    
    stepLength = 1
    modelPopNames = 'Landscan'
    xRes = 20           # Landscan Resolution
    yRes = 20
    Model = 'Wuhan'  # select model
    ParameterSet.debugmodelevel = ParameterSet.debugerror 
    
    dateTimeObj = datetime.now()
    resultstimeName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                  str(dateTimeObj.microsecond)
    
    resultsName = 'WuhanRes'
    ParameterSet.ModelRunning = 'Wuhan'
    
    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)   
 
    GlobalModel.cleanUp(modelPopNames)

    # create special folder for fitting
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/WuhanFit"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
        
    ParameterSet.HHSizeDist = [4.09122,26.96588,27.77211,16.38892,14.55989,6.6061,2.06366,0.77009,0.54148,0.24065]
    ParameterSet.HHSizeAgeDist = {}
    ParameterSet.HHSizeAgeDist[1] = [0,0,0.58962,1.45599,2.04561]
    ParameterSet.HHSizeAgeDist[2] = [0.09025,0.57156,5.13808,12.37591,8.79008]
    ParameterSet.HHSizeAgeDist[3] = [0.86637,4.37399,13.20017,6.67229,2.65929]
    ParameterSet.HHSizeAgeDist[4] = [0.88442,3.31509,7.34613,2.85784,1.98544]
    ParameterSet.HHSizeAgeDist[5] = [1.07093,2.5931,6.00445,3.08044,1.81097]
    ParameterSet.HHSizeAgeDist[6] = [0.79418,1.16118,2.60513,1.50413,0.54148]
    ParameterSet.HHSizeAgeDist[7] = [0.26473,0.39709,0.81222,0.33091,0.25871]
    ParameterSet.HHSizeAgeDist[8] = [0.07821,0.15041,0.35497,0.13837,0.04813]
    ParameterSet.HHSizeAgeDist[9] = [0.09025,0.1083,0.21057,0.07821,0.05415]
    ParameterSet.HHSizeAgeDist[10] = [0.0361,0.05415,0.09626,0.03008,0.02406]
        
    ### Wuhan data to fit
    wuhandata = {
        datetime(2019,12,8):2,
        datetime(2019,12,9):0,
        datetime(2019,12,10):3,
        datetime(2019,12,11):4,
        datetime(2019,12,12):4,
        datetime(2019,12,13):0,
        datetime(2019,12,14):0,
        datetime(2019,12,15):5,
        datetime(2019,12,16):2,
        datetime(2019,12,17):7,
        datetime(2019,12,18):3,
        datetime(2019,12,19):4,
        datetime(2019,12,20):11,
        datetime(2019,12,21):7,
        datetime(2019,12,22):12,
        datetime(2019,12,23):9,
        datetime(2019,12,24):9,
        datetime(2019,12,25):6,
        datetime(2019,12,26):8,
        datetime(2019,12,27):22,
        datetime(2019,12,28):13,
        datetime(2019,12,29):14,
        datetime(2019,12,30):21,
        datetime(2019,12,31):18,
        datetime(2020,1,1):92,
        datetime(2020,1,2):111,
        datetime(2020,1,3):92,
        datetime(2020,1,4):74,
        datetime(2020,1,5):92,
        datetime(2020,1,6):74,
        datetime(2020,1,7):111,
        datetime(2020,1,8):148,
        datetime(2020,1,9):148,
        datetime(2020,1,10):258,
        datetime(2020,1,11):240,
        datetime(2020,1,12):295,
        datetime(2020,1,13):369,
        datetime(2020,1,14):406,
        datetime(2020,1,15):628,
        datetime(2020,1,16):720,
        datetime(2020,1,17):904,
        datetime(2020,1,18):997,
        datetime(2020,1,19):1218,
        datetime(2020,1,20):1920,
        datetime(2020,1,21):2104,
        datetime(2020,1,22):2695,
        datetime(2020,1,23):3248
    }
    
    ####
       
    ### Highs and lows for variables
                            
    endTimeUL = 83 ## 11/1/2019 -> 1/23/2020
    endTimeLL = 46 ## 12/8/2019 -> 1/23/2020
    
    AG04AsymptomaticRateUL = 1
    AG04AsymptomaticRateLL = .9
    AG04HospRateUL = 175/10000
    AG04HospRateLL = 75/10000
            
    #agecohort 1 -- 5-17
    AG517AsymptomaticRateUL = .98
    AG517AsymptomaticRateLL = .8
    AG517HospRateUL = 150/10000
    AG517HospRateLL = 50/10000
    
    #agecohort 2 -- 18-49
    AG1849AsymptomaticRateUL = .9
    AG1849AsymptomaticRateLL = .7
    AG1849HospRateUL = 175/10000
    AG1849HospRateLL = 75/10000
    
    #agecohort 3 -- 50-64
    AG5064AsymptomaticRateUL = .9
    AG5064AsymptomaticRateLL = .5
    AG5064HospRateUL = 200/10000
    AG5064HospRateLL = 500/10000
            
    #agecohort 4 -- 65+
    AG65AsymptomaticRateUL = .7
    AG65AsymptomaticRateLL = .3
    AG65HospRateUL = .25
    AG65HospRateLL = .04

            
    IncubationTimeUL = 14
    IncubationTimeLL = 3
    totalContagiousTimeUL = 14
    totalContagiousTimeLL = 2
    symptomaticTimeUL = 15
    symptomaticTimeLL = 3
    hospitalSymptomaticTimeUL = 20
    hospitalSymptomaticTimeLL = 5
    hospTimeUL = 8
    hospTimeLL = 1
    EDVisitUL = 1
    EDVisitLL = .25
    preContagiousTimeUL = 3
    preContagiousTimeLL = 0
    postContagiousTimeUL = 10
    postContagiousTimeLL = 0
    ProbabilityOfTransmissionPerContactUL = 0.05
    ProbabilityOfTransmissionPerContactLL = 0.01
    symptomaticContactRateReductionUL = .9
    symptomaticContactRateReductionLL = .1
    
    householdcontactRateUL = 100
    householdcontactRateLL = 1
    
    #Initialize Parameters
    NumberMeanRuns = 40
    
    ParameterVals = {}
    SortCol = {}
    for nrun in range(0,NumberMeanRuns):
        endTime = random.random()*(endTimeUL - endTimeLL)+ endTimeLL
        AG04AsymptomaticRate = random.random()*(AG04AsymptomaticRateUL - AG04AsymptomaticRateLL) + AG04AsymptomaticRateLL
        AG04HospRate = random.random()*(AG04HospRateUL - AG04HospRateLL) + AG04HospRateLL
        
        AG517AsymptomaticRate = random.random()*(AG517AsymptomaticRateUL - AG517AsymptomaticRateLL) + AG517AsymptomaticRateLL
        AG517HospRate = random.random()*(AG517HospRateUL - AG517HospRateLL) + AG517HospRateLL
        
        AG1849AsymptomaticRate = random.random()*(AG1849AsymptomaticRateUL - AG1849AsymptomaticRateLL) + AG1849AsymptomaticRateLL
        AG1849HospRate = random.random()*(AG1849HospRateUL - AG1849HospRateLL) + AG1849HospRateLL
        
        AG5064AsymptomaticRate = random.random()*(AG5064AsymptomaticRateUL - AG5064AsymptomaticRateLL) + AG5064AsymptomaticRateLL
        AG5064HospRate = random.random()*(AG5064HospRateUL - AG5064HospRateLL) + AG5064HospRateLL
        
        AG65AsymptomaticRate = random.random()*(AG65AsymptomaticRateUL - AG65AsymptomaticRateLL) + AG65AsymptomaticRateLL
        AG65HospRate = random.random()*(AG65HospRateUL - AG65HospRateLL) + AG65HospRateLL
        
        IncubationTime = random.random()*(IncubationTimeUL - IncubationTimeLL) + IncubationTimeLL
        totalContagiousTime = random.random()*(totalContagiousTimeUL - totalContagiousTimeLL) + totalContagiousTimeLL
        hospitalSymptomaticTime = random.random()*(hospitalSymptomaticTimeUL - hospitalSymptomaticTimeLL) + hospitalSymptomaticTimeLL
        hospTime = random.random()*(hospTimeUL - hospTimeLL) + hospTimeLL
        EDVisit = random.random()*(EDVisitUL - EDVisitLL) + EDVisitLL
        preContagiousTime = random.random()*(preContagiousTimeUL - preContagiousTimeLL) + preContagiousTimeLL
        postContagiousTime = random.random()*(postContagiousTimeUL - postContagiousTimeLL) + postContagiousTimeLL
        householdcontactRate = random.random()*(householdcontactRateUL - householdcontactRateLL) + householdcontactRateLL
        
        ProbabilityOfTransmissionPerContact = random.random()*(ProbabilityOfTransmissionPerContactUL - ProbabilityOfTransmissionPerContactLL) + ProbabilityOfTransmissionPerContactLL
        symptomaticContactRateReduction = random.random()*(symptomaticContactRateReductionUL - symptomaticContactRateReductionLL) + symptomaticContactRateReductionLL
    

        ParameterVals[nrun] = { 'endTime':endTime, 
            'AG04AsymptomaticRate':AG04AsymptomaticRate,
            'AG04HospRate':0,
            'AG517AsymptomaticRate':AG517AsymptomaticRate,
            'AG517HospRate':AG517HospRate,
            'AG1849AsymptomaticRate':AG1849AsymptomaticRate,
            'AG1849HospRate':AG1849HospRate,
            'AG5064AsymptomaticRate':AG5064AsymptomaticRate,
            'AG5064HospRate':AG5064HospRate,
            'AG65AsymptomaticRate':AG65AsymptomaticRate,
            'AG65HospRate':AG65HospRate,
            'IncubationTime':IncubationTime,
            'totalContagiousTime':totalContagiousTime,
            'hospitalSymptomaticTime':hospitalSymptomaticTime,
            'hospTime':hospTime,
            'EDVisit':EDVisit,
            'preContagiousTime':preContagiousTime,
            'postContagiousTime':postContagiousTime,
            'NumInfStart':random.randint(1,100),
            'householdcontactRate':householdcontactRate,
            'ProbabilityOfTransmissionPerContact':ProbabilityOfTransmissionPerContact,
            'symptomaticContactRateReduction':symptomaticContactRateReduction,
            'diffC':0
        }
        SortCol[nrun] = 0
            
    finalvals = {}
    for grun in range(0,1000):
        print("******************* ",grun)
        try:
            os.remove(ParameterSet.ResultsFolder + "/Results_" + resultsName + ".pickle")
        except:
            pass
                        
       
        resultsVals = {}
        for day in wuhandata.keys():
            resultsVals[day] = {
            'Infections':0,
            'Contagious':0,
            'Hospitalized':0,
            'dead':0,
            'R0':0
            }
            
        for nrun in range(0,NumberMeanRuns):
            print("******************* ",grun," - ",nrun)
            endTime = ParameterVals[nrun]['endTime']
            ParameterSet.AG04AsymptomaticRate = ParameterVals[nrun]['AG04AsymptomaticRate']
            ParameterSet.AG04HospRate = ParameterVals[nrun]['AG04HospRate']
            ParameterSet.AG517AsymptomaticRate = ParameterVals[nrun]['AG517AsymptomaticRate']
            ParameterSet.AG517HospRate = ParameterVals[nrun]['AG517HospRate']
            ParameterSet.AG1849AsymptomaticRate = ParameterVals[nrun]['AG1849AsymptomaticRate']
            ParameterSet.AG1849HospRate = ParameterVals[nrun]['AG1849HospRate']
            ParameterSet.AG5064AsymptomaticRate = ParameterVals[nrun]['AG5064AsymptomaticRate']
            ParameterSet.AG5064HospRate = ParameterVals[nrun]['AG5064HospRate']
            ParameterSet.AG65AsymptomaticRate = ParameterVals[nrun]['AG65AsymptomaticRate']
            ParameterSet.AG65HospRate = ParameterVals[nrun]['AG65HospRate']
            ParameterSet.IncubationTime = ParameterVals[nrun]['IncubationTime']
            ParameterSet.totalContagiousTime = ParameterVals[nrun]['totalContagiousTime']
            ParameterSet.hospitalSymptomaticTime = ParameterVals[nrun]['hospitalSymptomaticTime']
            ParameterSet.hospTime = ParameterVals[nrun]['hospTime']
            ParameterSet.EDVisit = ParameterVals[nrun]['EDVisit']
            ParameterSet.preContagiousTime = ParameterVals[nrun]['preContagiousTime']
            ParameterSet.postContagiousTime = ParameterVals[nrun]['postContagiousTime']
            NumInfStart = ParameterVals[nrun]['NumInfStart']
            ParameterSet.householdcontactRate = ParameterVals[nrun]['householdcontactRate']
            ParameterSet.ProbabilityOfTransmissionPerContact = ParameterVals[nrun]['ProbabilityOfTransmissionPerContact']
            ParameterSet.symptomaticContactRateReduction = ParameterVals[nrun]['symptomaticContactRateReduction']
            
            # First set all the parameters
            ParameterSet.AGHospRate = [ParameterSet.AG04HospRate,ParameterSet.AG517HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG5064HospRate,ParameterSet.AG65HospRate]
            ParameterSet.AGAsymptomaticRate = [ParameterSet.AG04AsymptomaticRate, ParameterSet.AG517AsymptomaticRate, ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate, ParameterSet.AG5064AsymptomaticRate,ParameterSet.AG65AsymptomaticRate]
            ParameterSet.AGMortalityRate = [ParameterSet.AG04MortalityRate,ParameterSet.AG517MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG5064MortalityRate,ParameterSet.AG65MortalityRate]

        
            #Run setup
            RegionalList, numInfList, WuhanCoordDict, HospitalTransitionRate = GlobalModel.modelSetup(Model, modelPopNames,combineLocations=True, XRes=xRes, YRes=yRes)
           
            # run the model
            GlobalModel.RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsName, numInfList,randomInfect=False, numStartingInfections=NumInfStart)
            
            # now get the results
            
            results = Utils.FileRead(ParameterSet.ResultsFolder + "/Results_" + resultsName + ".pickle")
            
            # aggregate the results from each Local Population for each day
            diffC = 0
            for day in results.keys():
                inf = 0
                col = 0
                hos = 0
                dead = 0
                R0 = 0
                In = 0
                Ai = 0
                numInfList = results[day]
                for reg in numInfList.keys():
                    rdict = numInfList[reg]
                    for rkey in rdict:
                        lpdict = rdict[rkey]
                        if len(lpdict) > 0:
                            inf += lpdict['I']
                            col += lpdict['C']
                            hos += lpdict['H']
                            dead += lpdict['D']
                            In += lpdict['In']
                            Ai += lpdict['Ai']
                if Ai > 0:
                    R0 = In / Ai
                    
                x = datetime(2020, 1, 23) - timedelta(days=round(endTime,0)-day)
                if x >= datetime(2019, 12, 8) and x <= datetime(2020, 1, 23):
                    resultsVals[x]['Infections'] += inf
                    resultsVals[x]['Contagious'] += col
                    resultsVals[x]['Hospitalized'] += hos
                    resultsVals[x]['dead'] += dead
                    resultsVals[x]['R0'] += R0    
                    diffC += (hos - wuhandata[x])**2
                    
                ParameterVals[nrun]['diffC'] = math.sqrt(diffC)
                SortCol[nrun] = math.sqrt(diffC)
                
            GlobalModel.cleanUp(modelPopNames)
            

        NewParameterVals = []
        sorted_d = sorted((value, key) for (key,value) in SortCol.items())

        fitnessVals  = []
        fitnessValsSum = 0
        for pvals in range(0,int(len(sorted_d)/2)):
            NewParameterVals.append(ParameterVals[pvals])
            fitnessVals.append(sorted_d[pvals][0])
            fitnessValsSum += sorted_d[pvals][0]
    
        ParameterVals.clear()

        endTimevals = []
        AG04AsymptomaticRatevals = []
        AG04HospRatevals = []
        AG517AsymptomaticRatevals = []
        AG517HospRatevals = []
        AG1849AsymptomaticRatevals = []
        AG1849HospRatevals = []
        AG5064AsymptomaticRatevals = []
        AG5064HospRatevals = []
        AG65AsymptomaticRatevals = []
        AG65HospRatevals = []
        IncubationTimevals = []
        totalContagiousTimevals = []
        hospitalSymptomaticTimevals = []
        hospTimevals = []
        EDVisitvals = []
        preContagiousTimevals = []
        postContagiousTimevals = []
        NumInfStartvals = []
        householdcontactRatevals = []
        ProbabilityOfTransmissionPerContact = []
        symptomaticContactRateReduction = []
        
        ChildOn = 0

        for i in range(0,len(NewParameterVals)):

            endTimevals.append(NewParameterVals[i]['endTime'])
            AG04AsymptomaticRatevals.append(NewParameterVals[i]['AG04AsymptomaticRate'])
            AG04HospRatevals.append(NewParameterVals[i]['AG04HospRate'])
            AG517AsymptomaticRatevals.append(NewParameterVals[i]['AG517AsymptomaticRate'])
            AG517HospRatevals.append(NewParameterVals[i]['AG517HospRate'])
            AG1849AsymptomaticRatevals.append(NewParameterVals[i]['AG1849AsymptomaticRate'])
            AG1849HospRatevals.append(NewParameterVals[i]['AG1849HospRate'])
            AG5064AsymptomaticRatevals.append(NewParameterVals[i]['AG5064AsymptomaticRate'])
            AG5064HospRatevals.append(NewParameterVals[i]['AG5064HospRate'])
            AG65AsymptomaticRatevals.append(NewParameterVals[i]['AG65AsymptomaticRate'])
            AG65HospRatevals.append(NewParameterVals[i]['AG65HospRate'])
            IncubationTimevals.append(NewParameterVals[i]['IncubationTime'])
            totalContagiousTimevals.append(NewParameterVals[i]['totalContagiousTime'])
            hospitalSymptomaticTimevals.append(NewParameterVals[i]['hospitalSymptomaticTime'])
            hospTimevals.append(NewParameterVals[i]['hospTime'])
            EDVisitvals.append(NewParameterVals[i]['EDVisit'])
            preContagiousTimevals.append(NewParameterVals[i]['preContagiousTime'])
            postContagiousTimevals.append(NewParameterVals[i]['postContagiousTime'])
            NumInfStartvals.append(NewParameterVals[i]['NumInfStart'])
            householdcontactRatevals.append(NewParameterVals[i]['householdcontactRate'])
            ProbabilityOfTransmissionPerContact.append(NewParameterVals[i]['ProbabilityOfTransmissionPerContact'])
            symptomaticContactRateReduction.append(NewParameterVals[i]['symptomaticContactRateReduction'])

            parent1 = Utils.multinomial(fitnessVals,fitnessValsSum)
            parent2 = Utils.multinomial(fitnessVals,fitnessValsSum)
            while(parent2==parent1):
                parent2 = Utils.multinomial(fitnessVals,fitnessValsSum)

            Child1 = {
                'endTime':NewParameterVals[parent1]['endTime'] if random.random() < .5 else NewParameterVals[parent2]['endTime'], 
                'AG04AsymptomaticRate':NewParameterVals[parent1]['AG04AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG04AsymptomaticRate'],
                'AG04HospRate':NewParameterVals[parent1]['AG04HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG04HospRate'],
                'AG517AsymptomaticRate':NewParameterVals[parent1]['AG517AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG517AsymptomaticRate'],
                'AG517HospRate':NewParameterVals[parent1]['AG517HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG517HospRate'],
                'AG1849AsymptomaticRate':NewParameterVals[parent1]['AG1849AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG1849AsymptomaticRate'],
                'AG1849HospRate':NewParameterVals[parent1]['AG1849HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG1849HospRate'],
                'AG5064AsymptomaticRate':NewParameterVals[parent1]['AG5064AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG5064AsymptomaticRate'],
                'AG5064HospRate':NewParameterVals[parent1]['AG5064HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG5064HospRate'],
                'AG65AsymptomaticRate':NewParameterVals[parent1]['AG65AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG65AsymptomaticRate'],
                'AG65HospRate':NewParameterVals[parent1]['AG65HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG65HospRate'],
                'IncubationTime':NewParameterVals[parent1]['IncubationTime'] if random.random() < .5 else NewParameterVals[parent2]['IncubationTime'],
                'totalContagiousTime':NewParameterVals[parent1]['totalContagiousTime'] if random.random() < .5 else NewParameterVals[parent2]['totalContagiousTime'],
                'hospitalSymptomaticTime':NewParameterVals[parent1]['hospitalSymptomaticTime'] if random.random() < .5 else NewParameterVals[parent2]['hospitalSymptomaticTime'],
                'hospTime':NewParameterVals[parent1]['hospTime'] if random.random() < .5 else NewParameterVals[parent2]['hospTime'],
                'EDVisit':NewParameterVals[parent1]['EDVisit'] if random.random() < .5 else NewParameterVals[parent2]['EDVisit'],
                'preContagiousTime':NewParameterVals[parent1]['preContagiousTime'] if random.random() < .5 else NewParameterVals[parent2]['preContagiousTime'],
                'postContagiousTime':NewParameterVals[parent1]['postContagiousTime'] if random.random() < .5 else NewParameterVals[parent2]['postContagiousTime'],
                'NumInfStart':NewParameterVals[parent1]['NumInfStart'] if random.random() < .5 else NewParameterVals[parent2]['NumInfStart'],
                'householdcontactRate':NewParameterVals[parent1]['householdcontactRate'] if random.random() < .5 else NewParameterVals[parent2]['householdcontactRate'],
                'ProbabilityOfTransmissionPerContact':NewParameterVals[parent1]['ProbabilityOfTransmissionPerContact'] if random.random() < .5 else NewParameterVals[parent2]['ProbabilityOfTransmissionPerContact'],
                'symptomaticContactRateReduction':NewParameterVals[parent1]['symptomaticContactRateReduction'] if random.random() < .5 else NewParameterVals[parent2]['symptomaticContactRateReduction'],
                'diffC':0
            }
            
            Child2 = {
                'endTime':NewParameterVals[parent1]['endTime'] if random.random() < .5 else NewParameterVals[parent2]['endTime'], 
                'AG04AsymptomaticRate':NewParameterVals[parent1]['AG04AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG04AsymptomaticRate'],
                'AG04HospRate':NewParameterVals[parent1]['AG04HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG04HospRate'],
                'AG517AsymptomaticRate':NewParameterVals[parent1]['AG517AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG517AsymptomaticRate'],
                'AG517HospRate':NewParameterVals[parent1]['AG517HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG517HospRate'],
                'AG1849AsymptomaticRate':NewParameterVals[parent1]['AG1849AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG1849AsymptomaticRate'],
                'AG1849HospRate':NewParameterVals[parent1]['AG1849HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG1849HospRate'],
                'AG5064AsymptomaticRate':NewParameterVals[parent1]['AG5064AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG5064AsymptomaticRate'],
                'AG5064HospRate':NewParameterVals[parent1]['AG5064HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG5064HospRate'],
                'AG65AsymptomaticRate':NewParameterVals[parent1]['AG65AsymptomaticRate'] if random.random() < .5 else NewParameterVals[parent2]['AG65AsymptomaticRate'],
                'AG65HospRate':NewParameterVals[parent1]['AG65HospRate'] if random.random() < .5 else NewParameterVals[parent2]['AG65HospRate'],
                'IncubationTime':NewParameterVals[parent1]['IncubationTime'] if random.random() < .5 else NewParameterVals[parent2]['IncubationTime'],
                'totalContagiousTime':NewParameterVals[parent1]['totalContagiousTime'] if random.random() < .5 else NewParameterVals[parent2]['totalContagiousTime'],
                'hospitalSymptomaticTime':NewParameterVals[parent1]['hospitalSymptomaticTime'] if random.random() < .5 else NewParameterVals[parent2]['hospitalSymptomaticTime'],
                'hospTime':NewParameterVals[parent1]['hospTime'] if random.random() < .5 else NewParameterVals[parent2]['hospTime'],
                'EDVisit':NewParameterVals[parent1]['EDVisit'] if random.random() < .5 else NewParameterVals[parent2]['EDVisit'],
                'preContagiousTime':NewParameterVals[parent1]['preContagiousTime'] if random.random() < .5 else NewParameterVals[parent2]['preContagiousTime'],
                'postContagiousTime':NewParameterVals[parent1]['postContagiousTime'] if random.random() < .5 else NewParameterVals[parent2]['postContagiousTime'],
                'NumInfStart':NewParameterVals[parent1]['NumInfStart'] if random.random() < .5 else NewParameterVals[parent2]['NumInfStart'],
                'householdcontactRate':NewParameterVals[parent1]['householdcontactRate'] if random.random() < .5 else NewParameterVals[parent2]['householdcontactRate'],
                'ProbabilityOfTransmissionPerContact':NewParameterVals[parent1]['ProbabilityOfTransmissionPerContact'] if random.random() < .5 else NewParameterVals[parent2]['ProbabilityOfTransmissionPerContact'],
                'symptomaticContactRateReduction':NewParameterVals[parent1]['symptomaticContactRateReduction'] if random.random() < .5 else NewParameterVals[parent2]['symptomaticContactRateReduction'],
                'diffC':0
                
                
            }    
                
            ParameterVals[ChildOn] = Child1
            ChildOn+=1 
            ParameterVals[ChildOn] = Child2
            ChildOn+=1 

        finalvalsw = {
            'endTime':mean(endTimevals), 
            'AG04AsymptomaticRate':mean(AG04AsymptomaticRatevals),
            'AG04HospRate':mean(AG04HospRatevals),
            'AG517AsymptomaticRate':mean(AG517AsymptomaticRatevals),
            'AG517HospRate':mean(AG517HospRatevals),
            'AG1849AsymptomaticRate':mean(AG1849AsymptomaticRatevals),
            'AG1849HospRate':mean(AG1849HospRatevals),
            'AG5064AsymptomaticRate':mean(AG5064AsymptomaticRatevals),
            'AG5064HospRate':mean(AG5064HospRatevals),
            'AG65AsymptomaticRate':mean(AG65AsymptomaticRatevals),
            'AG65HospRate':mean(AG65HospRatevals),
            'IncubationTime':mean(IncubationTimevals),
            'totalContagiousTime':mean(totalContagiousTimevals),
            'hospitalSymptomaticTime':mean(hospitalSymptomaticTimevals),
            'hospTime':mean(hospTimevals),
            'EDVisit':mean(EDVisitvals),
            'preContagiousTime':mean(preContagiousTimevals),
            'postContagiousTime':mean(postContagiousTimevals),
            'NumInfStart':mean(NumInfStartvals),
            'householdcontactRate':mean(householdcontactRatevals),
            'ProbabilityOfTransmissionPerContact':mean(ProbabilityOfTransmissionPerContact),
            'symptomaticContactRateReduction':mean(symptomaticContactRateReduction)
        }
        print(finalvalsw)
        if os.path.exists(ParameterSet.ResultsFolder+"/WuhanFitVals_"+resultstimeName+".pickle"):
            finalvals = Utils.FileRead(ParameterSet.ResultsFolder+"/WuhanFitVals_"+resultstimeName+".pickle")
        finalvals[grun] = finalvalsw
        Utils.FileWrite(ParameterSet.ResultsFolder+"/WuhanFitVals_"+resultstimeName+".pickle",finalvals)
         
if __name__ == "__main__":
    # execute only if run as a script
    main()
