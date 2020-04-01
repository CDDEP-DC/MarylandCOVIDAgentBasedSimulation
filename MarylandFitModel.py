

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
    modelPopNames = 'MarylandFit'
    Model = 'MarylandFit'  # select model
    #ParameterSet.debugmodelevel = ParameterSet.debugerror 
    
    dateTimeObj = datetime.now()
    resultstimeName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                  str(dateTimeObj.microsecond)
    
    resultsName = 'MarylandFit'
    ParameterSet.ModelRunning = 'Maryland'
    
    if not os.path.exists(ParameterSet.PopDataFolder):
        os.makedirs(ParameterSet.PopDataFolder)
    if not os.path.exists(ParameterSet.QueueFolder):
        os.makedirs(ParameterSet.QueueFolder)
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)   
 
    GlobalModel.cleanUp(modelPopNames)

    # create special folder for fitting
    ParameterSet.ResultsFolder = ParameterSet.ResultsFolder + "/MarylandFit"
    if not os.path.exists(ParameterSet.ResultsFolder):
        os.makedirs(ParameterSet.ResultsFolder)
        
    ParameterSet.HHSizeDist = [14.7,26.9,18.6,20.1,10.9,4.8,4]
    ParameterSet.HHSizeAgeDist = {}
    ParameterSet.HHSizeAgeDist[1] = [0,0,5.1,3.7,5.9]
    ParameterSet.HHSizeAgeDist[2] = [0.1,0.8,7.6,9.1,9.3]
    ParameterSet.HHSizeAgeDist[3] = [1.1,2.8,8.2,4.6,1.9]
    ParameterSet.HHSizeAgeDist[4] = [1.8,5.7,9,2.8,0.8]
    ParameterSet.HHSizeAgeDist[5] = [1,3.8,4.5,1.2,0.4]
    ParameterSet.HHSizeAgeDist[6] = [0.5,1.7,1.9,0.5,0.2]
    ParameterSet.HHSizeAgeDist[7] = [0.5,1.4,1.5,0.4,0.2]
        
    ###  data to fit
    MarylandFitData = {}
    MarylandFitData[datetime(2020,3,22)] = {'hospitalized':18,'admissions':25}
    MarylandFitData[datetime(2020,3,23)] = {'hospitalized':43,'admissions':64}
    MarylandFitData[datetime(2020,3,24)] = {'hospitalized':52,'admissions':98}
    MarylandFitData[datetime(2020,3,25)] = {'hospitalized':88,'admissions':140}
    MarylandFitData[datetime(2020,3,26)] = {'hospitalized':112,'admissions':182}
    MarylandFitData[datetime(2020,3,27)] = {'hospitalized':134,'admissions':218}
    MarylandFitData[datetime(2020,3,28)] = {'hospitalized':166,'admissions':226}
    MarylandFitData[datetime(2020,3,29)] = {'hospitalized':217,'admissions':277}
    MarylandFitData[datetime(2020,3,30)] = {'hospitalized':293,'admissions':353}
    MarylandFitData[datetime(2020,3,31)] = {'hospitalized':369,'admissions':429}
    MarylandFitData[datetime(2020,4,1)] = {'hospitalized':462,'admissions':522}
    
    ####
       
    ### Highs and lows for variables
                            
    endTimeUL = 72 ## 
    endTimeLL = 62 ## 
    
    AG04AsymptomaticRateUL = 1
    AG04AsymptomaticRateLL = .8
    AG04HospRateUL = 75/10000
    AG04HospRateLL = 0/10000
            
    #agecohort 1 -- 5-17
    AG517AsymptomaticRateUL = 1
    AG517AsymptomaticRateLL = .75
    AG517HospRateUL = 160/10000
    AG517HospRateLL = 80/10000
    
    #agecohort 2 -- 18-49
    AG1849AsymptomaticRateUL = .9
    AG1849AsymptomaticRateLL = .3
    AG1849HospRateUL = 15/100
    AG1849HospRateLL = 1/100
    
    #agecohort 3 -- 50-64
    AG5064AsymptomaticRateUL = .9
    AG5064AsymptomaticRateLL = .3
    AG5064HospRateUL = 5/100
    AG5064HospRateLL = 20/100
            
    #agecohort 4 -- 65+
    AG65AsymptomaticRateUL = .9
    AG65AsymptomaticRateLL = .3
    AG65HospRateUL = .50
    AG65HospRateLL = .25

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
    
    # Need to add ICU time
    
    ImportationRateUL = 1000
    ImportationRateLL = 1
    
    ImportationRatePowerUL = 10
    ImportationRatePowerLL = 1
    
    householdcontactRateUL = 100
    householdcontactRateLL = 1
    
    #Initialize Parameters
    NumberMeanRuns = 60
    
    ParameterVals = {}
    SortCol = {}
   
    def mutateRand(name,value):
        mutationRate = .05
        if random.random() < mutationRate:
            if name == 'endTime':
                return random.randint(endTimeLL,endTimeUL)
                
            if name == 'AG04AsymptomaticRate':
                return random.random()*(AG04AsymptomaticRateUL - AG04AsymptomaticRateLL) + AG04AsymptomaticRateLL
                    
            if name == 'AG04HospRate':
                return random.random()*(AG04HospRateUL - AG04HospRateLL) + AG04HospRateLL
                
            if name == 'AG517AsymptomaticRate':
                return random.random()*(AG517AsymptomaticRateUL - AG517AsymptomaticRateLL) + AG517AsymptomaticRateLL
                
            if name == 'AG517HospRate':
                return random.random()*(AG517HospRateUL - AG517HospRateLL) + AG517HospRateLL
                
            if name == 'AG1849AsymptomaticRate':
                return random.random()*(AG1849AsymptomaticRateUL - AG1849AsymptomaticRateLL) + AG1849AsymptomaticRateLL
                
            if name == 'AG1849HospRate':
                return random.random()*(AG1849HospRateUL - AG1849HospRateLL) + AG1849HospRateLL
                
            if name == 'AG5064AsymptomaticRate':
                return random.random()*(AG5064AsymptomaticRateUL - AG5064AsymptomaticRateLL) + AG5064AsymptomaticRateLL
                
            if name == 'AG5064HospRate':
                return random.random()*(AG5064HospRateUL - AG5064HospRateLL) + AG5064HospRateLL
                
            if name == 'AG65AsymptomaticRate':
                return random.random()*(AG65AsymptomaticRateUL - AG65AsymptomaticRateLL) + AG65AsymptomaticRateLL
                
            if name == 'AG65HospRate':
                return random.random()*(AG65HospRateUL - AG65HospRateLL) + AG65HospRateLL
                
            if name == 'IncubationTime':
                return random.random()*(IncubationTimeUL - IncubationTimeLL) + IncubationTimeLL
                
            if name == 'totalContagiousTime':
                return random.random()*(totalContagiousTimeUL - totalContagiousTimeLL) + totalContagiousTimeLL
                
            if name == 'hospitalSymptomaticTime':
                return random.random()*(hospitalSymptomaticTimeUL - hospitalSymptomaticTimeLL) + hospitalSymptomaticTimeLL
                
            if name == 'hospTime':
                return random.random()*(hospTimeUL - hospTimeLL) + hospTimeLL
                
            if name == 'EDVisit':
                random.random()*(EDVisitUL - EDVisitLL) + EDVisitLL
                
            if name == 'preContagiousTime':
                random.random()*(preContagiousTimeUL - preContagiousTimeLL) + preContagiousTimeLL
                
            if name == 'postContagiousTime':
                random.random()*(postContagiousTimeUL - postContagiousTimeLL) + postContagiousTimeLL
                
            if name == 'householdcontactRate':
                random.random()*(householdcontactRateUL - householdcontactRateLL) + householdcontactRateLL
                
            if name == 'ProbabilityOfTransmissionPerContact':
                random.random()*(ProbabilityOfTransmissionPerContactUL - ProbabilityOfTransmissionPerContactLL) + ProbabilityOfTransmissionPerContactLL
                
            if name == 'symptomaticContactRateReduction':
                return random.random()*(symptomaticContactRateReductionUL - symptomaticContactRateReductionLL) + symptomaticContactRateReductionLL
                
            if name == 'ImportationRate':
                return random.randint(ImportationRateLL,ImportationRateUL)
                
            if name == 'ImportationRatePower':    
                return random.random()*(ImportationRatePowerUL - ImportationRatePowerLL) + ImportationRatePowerUL 
        return value
        
    
    for nrun in range(0,NumberMeanRuns):
        endTime = random.randint(endTimeLL,endTimeUL)
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
        
        ImportationRate = random.randint(ImportationRateLL,ImportationRateUL)
        ImportationRatePower = random.random()*(ImportationRatePowerUL - ImportationRatePowerLL) + ImportationRatePowerUL
        
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
            'ImportationRate':ImportationRate,
            'ImportationRatePower':ImportationRatePower,
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
        for day in MarylandFitData.keys():
            resultsVals[day] = {
            'Infections':0,
            'Contagious':0,
            'Hospitalized':0,
            'dead':0,
            'R0':0,
            'Admissions':0
            }
            
        for nrun in range(0,NumberMeanRuns):
            print(ParameterVals)
            print("******************* ",grun," - ",nrun)
            endTime = ParameterVals[nrun]['endTime']
            ParameterSet.StopQueueDate = endTime + 2
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
            ParameterSet.ICUtime = ParameterVals[nrun]['hospitalSymptomaticTime']
            ParameterSet.PostICUTime = 3
            ParameterSet.hospTime = ParameterVals[nrun]['hospTime']
            ParameterSet.EDVisit = ParameterVals[nrun]['EDVisit']
            ParameterSet.preContagiousTime = ParameterVals[nrun]['preContagiousTime']
            ParameterSet.postContagiousTime = ParameterVals[nrun]['postContagiousTime']
            NumInfStart = ParameterVals[nrun]['NumInfStart']
            ParameterSet.householdcontactRate = ParameterVals[nrun]['householdcontactRate']
            ParameterSet.ProbabilityOfTransmissionPerContact = ParameterVals[nrun]['ProbabilityOfTransmissionPerContact']
            ParameterSet.symptomaticContactRateReduction = ParameterVals[nrun]['symptomaticContactRateReduction']
            ParameterSet.ImportationRate = ParameterVals[nrun]['ImportationRate']
            ParameterSet.ImportationRatePower = ParameterVals[nrun]['ImportationRatePower']
            
            # First set all the parameters
            ParameterSet.AGHospRate = [ParameterSet.AG04HospRate,ParameterSet.AG517HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG5064HospRate,ParameterSet.AG65HospRate]
            ParameterSet.AGAsymptomaticRate = [ParameterSet.AG04AsymptomaticRate, ParameterSet.AG517AsymptomaticRate, ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate, ParameterSet.AG5064AsymptomaticRate,ParameterSet.AG65AsymptomaticRate]
            ParameterSet.AGMortalityRate = [ParameterSet.AG04MortalityRate,ParameterSet.AG517MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG5064MortalityRate,ParameterSet.AG65MortalityRate]
        
            #Run setup
            RegionalList, numInfList, HospitalNames, LocationImportationRisk, RegionListGuide = GlobalModel.modelSetup(Model, modelPopNames,combineLocations=True)
            
            # run the model
            GlobalModel.RunModel(RegionalList, modelPopNames, endTime, stepLength, resultsName, numInfList,LocationImportationRisk=LocationImportationRisk, RegionListGuide=RegionListGuide)
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
                totHI = 0
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
                            totHI += lpdict['HI']
                            Ai += lpdict['Ai']
                if Ai > 0:
                    R0 = In / Ai
                    
                x = datetime(2020, 4, 1) - timedelta(days=round(endTime,0)-day)
                print(x," ",round(endTime,0)-day)
                if x >= datetime(2020, 3, 22) and x <= datetime(2020, 4, 1):
                    print("in here")
                    resultsVals[x]['Infections'] += inf
                    resultsVals[x]['Contagious'] += col
                    resultsVals[x]['Hospitalized'] += hos
                    resultsVals[x]['dead'] += dead
                    resultsVals[x]['R0'] += R0    
                    resultsVals[x]['Admissions'] += totHI
                    diffC += (hos - MarylandFitData[x]['hospitalized'])**2
                    #diffC += (totHI - MarylandFitData[x]['admissions'])**2
                    
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
        ImportationRate = []
        ImportationRatePower = []
        
        
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
            ImportationRate.append(NewParameterVals[i]['ImportationRate'])
            ImportationRatePower.append(NewParameterVals[i]['ImportationRatePower'])

            parent1 = Utils.multinomial(fitnessVals,fitnessValsSum)
            parent2 = Utils.multinomial(fitnessVals,fitnessValsSum)
            while(parent2==parent1):
                parent2 = Utils.multinomial(fitnessVals,fitnessValsSum)
            
            Child1 = {
                'endTime':mutateRand('endTime',NewParameterVals[parent1]['endTime'])  if random.random() < .5 else mutateRand('endTime',NewParameterVals[parent2]['endTime']), 
                'AG04AsymptomaticRate':mutateRand('AG04AsymptomaticRate',NewParameterVals[parent1]['AG04AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG04AsymptomaticRate',NewParameterVals[parent2]['AG04AsymptomaticRate']),
                'AG04HospRate':mutateRand('AG04HospRate',NewParameterVals[parent1]['AG04HospRate'])  if random.random() < .5 else mutateRand('AG04HospRate',NewParameterVals[parent2]['AG04HospRate']),
                'AG517AsymptomaticRate':mutateRand('AG517AsymptomaticRate',NewParameterVals[parent1]['AG517AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG517AsymptomaticRate',NewParameterVals[parent2]['AG517AsymptomaticRate']),
                'AG517HospRate':mutateRand('AG517HospRate',NewParameterVals[parent1]['AG517HospRate'])  if random.random() < .5 else mutateRand('AG517HospRate',NewParameterVals[parent2]['AG517HospRate']),
                'AG1849AsymptomaticRate':mutateRand('AG1849AsymptomaticRate',NewParameterVals[parent1]['AG1849AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG1849AsymptomaticRate',NewParameterVals[parent2]['AG1849AsymptomaticRate']),
                'AG1849HospRate':mutateRand('AG1849HospRate',NewParameterVals[parent1]['AG1849HospRate'])  if random.random() < .5 else mutateRand('AG1849HospRate',NewParameterVals[parent2]['AG1849HospRate']),
                'AG5064AsymptomaticRate':mutateRand('AG5064AsymptomaticRate',NewParameterVals[parent1]['AG5064AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG5064AsymptomaticRate',NewParameterVals[parent2]['AG5064AsymptomaticRate']),
                'AG5064HospRate':mutateRand('AG5064HospRate',NewParameterVals[parent1]['AG5064HospRate'])  if random.random() < .5 else mutateRand('AG5064HospRate',NewParameterVals[parent2]['AG5064HospRate']),
                'AG65AsymptomaticRate':mutateRand('AG65AsymptomaticRate',NewParameterVals[parent1]['AG65AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG65AsymptomaticRate',NewParameterVals[parent2]['AG65AsymptomaticRate']),
                'AG65HospRate':mutateRand('AG65HospRate',NewParameterVals[parent1]['AG65HospRate'])  if random.random() < .5 else mutateRand('AG65HospRate',NewParameterVals[parent2]['AG65HospRate']),
                'IncubationTime':mutateRand('IncubationTime',NewParameterVals[parent1]['IncubationTime'])  if random.random() < .5 else mutateRand('IncubationTime',NewParameterVals[parent2]['IncubationTime']),
                'totalContagiousTime':mutateRand('totalContagiousTime',NewParameterVals[parent1]['totalContagiousTime'])  if random.random() < .5 else mutateRand('totalContagiousTime',NewParameterVals[parent2]['totalContagiousTime']),
                'hospitalSymptomaticTime':mutateRand('hospitalSymptomaticTime',NewParameterVals[parent1]['hospitalSymptomaticTime'])  if random.random() < .5 else mutateRand('hospitalSymptomaticTime',NewParameterVals[parent2]['hospitalSymptomaticTime']),
                'hospTime':mutateRand('hospTime',NewParameterVals[parent1]['hospTime'])  if random.random() < .5 else mutateRand('hospTime',NewParameterVals[parent2]['hospTime']),
                'EDVisit':mutateRand('EDVisit',NewParameterVals[parent1]['EDVisit'])  if random.random() < .5 else mutateRand('EDVisit',NewParameterVals[parent2]['EDVisit']),
                'preContagiousTime':mutateRand('preContagiousTime',NewParameterVals[parent1]['preContagiousTime'])  if random.random() < .5 else mutateRand('preContagiousTime',NewParameterVals[parent2]['preContagiousTime']),
                'postContagiousTime':mutateRand('postContagiousTime',NewParameterVals[parent1]['postContagiousTime'])  if random.random() < .5 else mutateRand('postContagiousTime',NewParameterVals[parent2]['postContagiousTime']),
                'NumInfStart':mutateRand('NumInfStart',NewParameterVals[parent1]['NumInfStart'])  if random.random() < .5 else mutateRand('NumInfStart',NewParameterVals[parent2]['NumInfStart']),
                'householdcontactRate':mutateRand('householdcontactRate',NewParameterVals[parent1]['householdcontactRate'])  if random.random() < .5 else mutateRand('householdcontactRate',NewParameterVals[parent2]['householdcontactRate']),
                'ProbabilityOfTransmissionPerContact':mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent1]['ProbabilityOfTransmissionPerContact'])  if random.random() < .5 else mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent2]['ProbabilityOfTransmissionPerContact']),
                'symptomaticContactRateReduction':mutateRand('symptomaticContactRateReduction',NewParameterVals[parent1]['symptomaticContactRateReduction'])  if random.random() < .5 else mutateRand('symptomaticContactRateReduction',NewParameterVals[parent2]['symptomaticContactRateReduction']),
                'ImportationRate':mutateRand('ImportationRate',NewParameterVals[parent1]['ImportationRate'])  if random.random() < .5 else mutateRand('ImportationRate',NewParameterVals[parent2]['ImportationRate']),
                'ImportationRatePower':mutateRand('ImportationRatePower',NewParameterVals[parent1]['ImportationRatePower'])  if random.random() < .5 else mutateRand('ImportationRatePower',NewParameterVals[parent2]['ImportationRatePower']),
                'diffC':0
            }
            
            Child2 = {
                'endTime':mutateRand('endTime',NewParameterVals[parent1]['endTime'])  if random.random() < .5 else mutateRand('endTime',NewParameterVals[parent2]['endTime']), 
                'AG04AsymptomaticRate':mutateRand('AG04AsymptomaticRate',NewParameterVals[parent1]['AG04AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG04AsymptomaticRate',NewParameterVals[parent2]['AG04AsymptomaticRate']),
                'AG04HospRate':mutateRand('AG04HospRate',NewParameterVals[parent1]['AG04HospRate'])  if random.random() < .5 else mutateRand('AG04HospRate',NewParameterVals[parent2]['AG04HospRate']),
                'AG517AsymptomaticRate':mutateRand('AG517AsymptomaticRate',NewParameterVals[parent1]['AG517AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG517AsymptomaticRate',NewParameterVals[parent2]['AG517AsymptomaticRate']),
                'AG517HospRate':mutateRand('AG517HospRate',NewParameterVals[parent1]['AG517HospRate'])  if random.random() < .5 else mutateRand('AG517HospRate',NewParameterVals[parent2]['AG517HospRate']),
                'AG1849AsymptomaticRate':mutateRand('AG1849AsymptomaticRate',NewParameterVals[parent1]['AG1849AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG1849AsymptomaticRate',NewParameterVals[parent2]['AG1849AsymptomaticRate']),
                'AG1849HospRate':mutateRand('AG1849HospRate',NewParameterVals[parent1]['AG1849HospRate'])  if random.random() < .5 else mutateRand('AG1849HospRate',NewParameterVals[parent2]['AG1849HospRate']),
                'AG5064AsymptomaticRate':mutateRand('AG5064AsymptomaticRate',NewParameterVals[parent1]['AG5064AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG5064AsymptomaticRate',NewParameterVals[parent2]['AG5064AsymptomaticRate']),
                'AG5064HospRate':mutateRand('AG5064HospRate',NewParameterVals[parent1]['AG5064HospRate'])  if random.random() < .5 else mutateRand('AG5064HospRate',NewParameterVals[parent2]['AG5064HospRate']),
                'AG65AsymptomaticRate':mutateRand('AG65AsymptomaticRate',NewParameterVals[parent1]['AG65AsymptomaticRate'])  if random.random() < .5 else mutateRand('AG65AsymptomaticRate',NewParameterVals[parent2]['AG65AsymptomaticRate']),
                'AG65HospRate':mutateRand('AG65HospRate',NewParameterVals[parent1]['AG65HospRate'])  if random.random() < .5 else mutateRand('AG65HospRate',NewParameterVals[parent2]['AG65HospRate']),
                'IncubationTime':mutateRand('IncubationTime',NewParameterVals[parent1]['IncubationTime'])  if random.random() < .5 else mutateRand('IncubationTime',NewParameterVals[parent2]['IncubationTime']),
                'totalContagiousTime':mutateRand('totalContagiousTime',NewParameterVals[parent1]['totalContagiousTime'])  if random.random() < .5 else mutateRand('totalContagiousTime',NewParameterVals[parent2]['totalContagiousTime']),
                'hospitalSymptomaticTime':mutateRand('hospitalSymptomaticTime',NewParameterVals[parent1]['hospitalSymptomaticTime'])  if random.random() < .5 else mutateRand('hospitalSymptomaticTime',NewParameterVals[parent2]['hospitalSymptomaticTime']),
                'hospTime':mutateRand('hospTime',NewParameterVals[parent1]['hospTime'])  if random.random() < .5 else mutateRand('hospTime',NewParameterVals[parent2]['hospTime']),
                'EDVisit':mutateRand('EDVisit',NewParameterVals[parent1]['EDVisit'])  if random.random() < .5 else mutateRand('EDVisit',NewParameterVals[parent2]['EDVisit']),
                'preContagiousTime':mutateRand('preContagiousTime',NewParameterVals[parent1]['preContagiousTime'])  if random.random() < .5 else mutateRand('preContagiousTime',NewParameterVals[parent2]['preContagiousTime']),
                'postContagiousTime':mutateRand('postContagiousTime',NewParameterVals[parent1]['postContagiousTime'])  if random.random() < .5 else mutateRand('postContagiousTime',NewParameterVals[parent2]['postContagiousTime']),
                'NumInfStart':mutateRand('NumInfStart',NewParameterVals[parent1]['NumInfStart'])  if random.random() < .5 else mutateRand('NumInfStart',NewParameterVals[parent2]['NumInfStart']),
                'householdcontactRate':mutateRand('householdcontactRate',NewParameterVals[parent1]['householdcontactRate'])  if random.random() < .5 else mutateRand('householdcontactRate',NewParameterVals[parent2]['householdcontactRate']),
                'ProbabilityOfTransmissionPerContact':mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent1]['ProbabilityOfTransmissionPerContact'])  if random.random() < .5 else mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent2]['ProbabilityOfTransmissionPerContact']),
                'symptomaticContactRateReduction':mutateRand('symptomaticContactRateReduction',NewParameterVals[parent1]['symptomaticContactRateReduction'])  if random.random() < .5 else mutateRand('symptomaticContactRateReduction',NewParameterVals[parent2]['symptomaticContactRateReduction']),
                'ImportationRate':mutateRand('ImportationRate',NewParameterVals[parent1]['ImportationRate'])  if random.random() < .5 else mutateRand('ImportationRate',NewParameterVals[parent2]['ImportationRate']),
                'ImportationRatePower':mutateRand('ImportationRatePower',NewParameterVals[parent1]['ImportationRatePower'])  if random.random() < .5 else mutateRand('ImportationRatePower',NewParameterVals[parent2]['ImportationRatePower']),
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
            'symptomaticContactRateReduction':mean(symptomaticContactRateReduction),
            'ImportationRate':mean(ImportationRate),
            'ImportationRatePower':mean(ImportationRatePower)
        }
        print(finalvalsw)
        if os.path.exists(ParameterSet.ResultsFolder+"/MarylandFitVals_"+resultstimeName+".pickle"):
            finalvals = Utils.FileRead(ParameterSet.ResultsFolder+"/MarylandFitVals_"+resultstimeName+".pickle")
        finalvals[grun] = finalvalsw
        Utils.FileWrite(ParameterSet.ResultsFolder+"/MarylandFitVals_"+resultstimeName+".pickle",finalvals)


            
    return value        
if __name__ == "__main__":
    # execute only if run as a script
    main()
