
import multiprocessing
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
    ParameterSet.debugmodelevel = ParameterSet.debugerror 
    
    
    
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
        
    AgeCohortInteraction = {0:{0:1.39277777777778,	1:0.328888888888889,	2:0.299444444444444,	3:0.224444444444444,	4:0.108333333333333},
                                    1:{0:0.396666666666667,	1:2.75555555555556,	2:0.342407407407407,	3:0.113333333333333,	4:0.138333333333333},
                                    2:{0:0.503333333333333,	1:1.22666666666667,	2:1.035,	3:0.305185185185185,	4:0.180555555555556},
                                    3:{0:0.268888888888889,	1:0.164074074074074, 2:0.219444444444444,	3:0.787777777777778,	4:0.27},
                                    4:{0:0.181666666666667,	1:0.138888888888889, 2:0.157222222222222,	3:0.271666666666667,	4:0.703333333333333}}
    
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
    MarylandFitData[datetime(2020,4,2)] = {'hospitalized':462,'admissions':582}
    MarylandFitData[datetime(2020,4,3)] = {'hospitalized':605,'admissions':664}
    MarylandFitData[datetime(2020,4,4)] = {'hospitalized':559,'admissions':821}
    MarylandFitData[datetime(2020,4,5)] = {'hospitalized':770,'admissions':936}
    MarylandFitData[datetime(2020,4,6)] = {'hospitalized':801,'admissions':1059}
    MarylandFitData[datetime(2020,4,7)] = {'hospitalized':848,'admissions':1106}
    MarylandFitData[datetime(2020,4,8)] = {'hospitalized':924,'admissions':1210}
    #MarylandFitData[datetime(2020,4,9)] = {'hospitalized':918,'admissions':1348}
    #MarylandFitData[datetime(2020,4,10)] = {'hospitalized':1020,'admissions':1709}
    #MarylandFitData[datetime(2020,4,11)] = {'hospitalized':1019,'admissions':1860}
    #MarylandFitData[datetime(2020,4,12)] = {'hospitalized':1071,'admissions':1975}
    
    ####
       
    ### Highs and lows for variables
                            
    endTimeUL = 68 ## 
    endTimeLL = 54 ## 
    
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
    AG1849AsymptomaticRateUL = 1
    AG1849AsymptomaticRateLL = .3
    AG1849HospRateUL = 15/100
    AG1849HospRateLL = 1/100
    
    #agecohort 3 -- 50-64
    AG5064AsymptomaticRateUL = .9
    AG5064AsymptomaticRateLL = .1
    AG5064HospRateUL = 1/100
    AG5064HospRateLL = 35/100
            
    #agecohort 4 -- 65+
    AG65AsymptomaticRateUL = .9
    AG65AsymptomaticRateLL = .1
    AG65HospRateUL = .60
    AG65HospRateLL = .1

    IncubationTimeUL = 14
    IncubationTimeLL = 1
    totalContagiousTimeUL = 21
    totalContagiousTimeLL = 1
    symptomaticTimeUL = 15
    symptomaticTimeLL = 3
    hospitalSymptomaticTimeUL = 20
    hospitalSymptomaticTimeLL = 5
    ICURateUL = .6
    ICURateLL = .4
    PostICUTimeUL = 5
    PostICUTimeLL = 1
    ICUtimeUL = 15 # added to hospitalSymptomaticTime
    ICUtimeLL = 5
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
    

    ImportationRateUL = 100
    ImportationRateLL = 1
    
    AsymptomaticReducationTransUL = 2
    AsymptomaticReducationTransLL = .1
    
    householdcontactRateUL = 100
    householdcontactRateLL = 1
    
    #Initialize Parameters
    NumberMeanRuns = multiprocessing.cpu_count()
    
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
            
            if name == 'symptomaticTime':
                return random.random()*(symptomaticTimeUL - symptomaticTimeLL) + symptomaticTimeLL
                    
            if name == 'hospitalSymptomaticTime':
                return random.random()*(hospitalSymptomaticTimeUL - hospitalSymptomaticTimeLL) + hospitalSymptomaticTimeLL
                
            if name == 'ICURate':
                return random.random()*(ICURateUL - ICURateLL) + ICURateLL
                
            if name == 'ICUtime':
                return random.random()*(ICUtimeUL - ICUtimeLL) + ICUtimeLL
            
            if name == 'PostICUTime':
                return random.random()*(PostICUTimeUL - PostICUTimeLL) + PostICUTimeLL
                
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
                
            if name == 'AsymptomaticReducationTrans':    
                return random.random()*(AsymptomaticReducationTransUL - AsymptomaticReducationTransLL) + AsymptomaticReducationTransLL 
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
        symptomaticTime = random.random()*(symptomaticTimeUL - symptomaticTimeLL) + symptomaticTimeLL
        hospitalSymptomaticTime = random.random()*(hospitalSymptomaticTimeUL - hospitalSymptomaticTimeLL) + hospitalSymptomaticTimeLL
        
        ICURate = random.random()*(ICURateUL - ICURateLL) + ICURateLL
        ICUtime = random.random()*(ICUtimeUL - ICUtimeLL) + ICUtimeLL + hospitalSymptomaticTime
        PostICUTime = random.random()*(PostICUTimeUL - PostICUTimeLL) + PostICUTimeLL
        
        hospTime = random.random()*(hospTimeUL - hospTimeLL) + hospTimeLL
        EDVisit = random.random()*(EDVisitUL - EDVisitLL) + EDVisitLL
        preContagiousTime = random.random()*(preContagiousTimeUL - preContagiousTimeLL) + preContagiousTimeLL
        postContagiousTime = random.random()*(postContagiousTimeUL - postContagiousTimeLL) + postContagiousTimeLL
        householdcontactRate = random.random()*(householdcontactRateUL - householdcontactRateLL) + householdcontactRateLL
        
        ImportationRate = random.randint(ImportationRateLL,ImportationRateUL)
        AsymptomaticReducationTrans = random.random()*(AsymptomaticReducationTransUL - AsymptomaticReducationTransLL) + AsymptomaticReducationTransLL
        
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
            'symptomaticTime':symptomaticTime,
            'hospitalSymptomaticTime':hospitalSymptomaticTime,
            'ICURate':ICURate,
            'ICUtime':ICUtime,
            'PostICUTime':PostICUTime,
            'hospTime':hospTime,
            'EDVisit':EDVisit,
            'preContagiousTime':preContagiousTime,
            'postContagiousTime':postContagiousTime,
            'NumInfStart':random.randint(1,100),
            'householdcontactRate':householdcontactRate,
            'ProbabilityOfTransmissionPerContact':ProbabilityOfTransmissionPerContact,
            'symptomaticContactRateReduction':symptomaticContactRateReduction,
            'ImportationRate':ImportationRate,
            'AsymptomaticReducationTrans':AsymptomaticReducationTrans,
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
                        
        jobs = []
        for i in range(0,NumberMeanRuns):
            jobs.append(multiprocessing.Process(target=WorkerJob,
                                                    args=(i,ParameterVals[nrun],AgeCohortInteraction,Model, modelPopNames,resultsName,MarylandFitData,grun)))    
        #for nrun in range(0,):
        #    WorkerJob(nrun,ParameterVals[nrun],AgeCohortInteraction,Model, modelPopNames,resultsName,MarylandFitData)
        
        for j in jobs:
            j.start()
            	
        for j in jobs:  
            j.join()    
        for nrun in range(0,NumberMeanRuns):
            resultvals = Utils.FileRead(ParameterSet.ResultsFolder + "/FitResults_" + str(i) + "_" + resultsName + ".pickle")    
            ParameterVals[nrun]['diffC'] = math.sqrt(resultvals)
            SortCol[nrun] = math.sqrt(resultvals)
            

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
        symptomaticTimevals = []
        hospitalSymptomaticTimevals = []
        ICURatevals = []
        ICUtimevals = []
        PostICUTimevals = []
        hospTimevals = []
        EDVisitvals = []
        preContagiousTimevals = []
        postContagiousTimevals = []
        NumInfStartvals = []
        householdcontactRatevals = []
        ProbabilityOfTransmissionPerContact = []
        symptomaticContactRateReduction = []
        ImportationRate = []
        AsymptomaticReducationTrans = []
        
        
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
            symptomaticTimevals.append(NewParameterVals[i]['symptomaticTime'])
            hospitalSymptomaticTimevals.append(NewParameterVals[i]['hospitalSymptomaticTime'])
            ICURatevals.append(NewParameterVals[i]['ICURate'])
            ICUtimevals.append(NewParameterVals[i]['ICUtime'])
            PostICUTimevals.append(NewParameterVals[i]['PostICUTime'])
            hospTimevals.append(NewParameterVals[i]['hospTime'])
            EDVisitvals.append(NewParameterVals[i]['EDVisit'])
            preContagiousTimevals.append(NewParameterVals[i]['preContagiousTime'])
            postContagiousTimevals.append(NewParameterVals[i]['postContagiousTime'])
            NumInfStartvals.append(NewParameterVals[i]['NumInfStart'])
            householdcontactRatevals.append(NewParameterVals[i]['householdcontactRate'])
            ProbabilityOfTransmissionPerContact.append(NewParameterVals[i]['ProbabilityOfTransmissionPerContact'])
            symptomaticContactRateReduction.append(NewParameterVals[i]['symptomaticContactRateReduction'])
            ImportationRate.append(NewParameterVals[i]['ImportationRate'])
            AsymptomaticReducationTrans.append(NewParameterVals[i]['AsymptomaticReducationTrans'])

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
                'symptomaticTime':mutateRand('symptomaticTime',NewParameterVals[parent1]['symptomaticTime'])  if random.random() < .5 else mutateRand('symptomaticTime',NewParameterVals[parent2]['symptomaticTime']),
                'hospitalSymptomaticTime':mutateRand('hospitalSymptomaticTime',NewParameterVals[parent1]['hospitalSymptomaticTime'])  if random.random() < .5 else mutateRand('hospitalSymptomaticTime',NewParameterVals[parent2]['hospitalSymptomaticTime']),
                'ICURate':mutateRand('ICURate',NewParameterVals[parent1]['ICURate'])  if random.random() < .5 else mutateRand('ICURate',NewParameterVals[parent2]['ICURate']),
                'ICUtime':mutateRand('ICUtime',NewParameterVals[parent1]['ICUtime'])  if random.random() < .5 else mutateRand('ICUtime',NewParameterVals[parent2]['ICUtime']),
                'PostICUTime':mutateRand('PostICUTime',NewParameterVals[parent1]['PostICUTime'])  if random.random() < .5 else mutateRand('PostICUTime',NewParameterVals[parent2]['PostICUTime']),                
                'hospTime':mutateRand('hospTime',NewParameterVals[parent1]['hospTime'])  if random.random() < .5 else mutateRand('hospTime',NewParameterVals[parent2]['hospTime']),
                'EDVisit':mutateRand('EDVisit',NewParameterVals[parent1]['EDVisit'])  if random.random() < .5 else mutateRand('EDVisit',NewParameterVals[parent2]['EDVisit']),
                'preContagiousTime':mutateRand('preContagiousTime',NewParameterVals[parent1]['preContagiousTime'])  if random.random() < .5 else mutateRand('preContagiousTime',NewParameterVals[parent2]['preContagiousTime']),
                'postContagiousTime':mutateRand('postContagiousTime',NewParameterVals[parent1]['postContagiousTime'])  if random.random() < .5 else mutateRand('postContagiousTime',NewParameterVals[parent2]['postContagiousTime']),
                'NumInfStart':mutateRand('NumInfStart',NewParameterVals[parent1]['NumInfStart'])  if random.random() < .5 else mutateRand('NumInfStart',NewParameterVals[parent2]['NumInfStart']),
                'householdcontactRate':mutateRand('householdcontactRate',NewParameterVals[parent1]['householdcontactRate'])  if random.random() < .5 else mutateRand('householdcontactRate',NewParameterVals[parent2]['householdcontactRate']),
                'ProbabilityOfTransmissionPerContact':mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent1]['ProbabilityOfTransmissionPerContact'])  if random.random() < .5 else mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent2]['ProbabilityOfTransmissionPerContact']),
                'symptomaticContactRateReduction':mutateRand('symptomaticContactRateReduction',NewParameterVals[parent1]['symptomaticContactRateReduction'])  if random.random() < .5 else mutateRand('symptomaticContactRateReduction',NewParameterVals[parent2]['symptomaticContactRateReduction']),
                'ImportationRate':mutateRand('ImportationRate',NewParameterVals[parent1]['ImportationRate'])  if random.random() < .5 else mutateRand('ImportationRate',NewParameterVals[parent2]['ImportationRate']),
                'AsymptomaticReducationTrans':mutateRand('AsymptomaticReducationTrans',NewParameterVals[parent1]['AsymptomaticReducationTrans'])  if random.random() < .5 else mutateRand('AsymptomaticReducationTrans',NewParameterVals[parent2]['AsymptomaticReducationTrans']),
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
                'symptomaticTime':mutateRand('symptomaticTime',NewParameterVals[parent1]['symptomaticTime'])  if random.random() < .5 else mutateRand('symptomaticTime',NewParameterVals[parent2]['symptomaticTime']),
                'hospitalSymptomaticTime':mutateRand('hospitalSymptomaticTime',NewParameterVals[parent1]['hospitalSymptomaticTime'])  if random.random() < .5 else mutateRand('hospitalSymptomaticTime',NewParameterVals[parent2]['hospitalSymptomaticTime']),
                'ICURate':mutateRand('ICURate',NewParameterVals[parent1]['ICURate'])  if random.random() < .5 else mutateRand('ICURate',NewParameterVals[parent2]['ICURate']),
                'ICUtime':mutateRand('ICUtime',NewParameterVals[parent1]['ICUtime'])  if random.random() < .5 else mutateRand('ICUtime',NewParameterVals[parent2]['ICUtime']),
                'PostICUTime':mutateRand('PostICUTime',NewParameterVals[parent1]['PostICUTime'])  if random.random() < .5 else mutateRand('PostICUTime',NewParameterVals[parent2]['PostICUTime']),
                'hospTime':mutateRand('hospTime',NewParameterVals[parent1]['hospTime'])  if random.random() < .5 else mutateRand('hospTime',NewParameterVals[parent2]['hospTime']),
                'EDVisit':mutateRand('EDVisit',NewParameterVals[parent1]['EDVisit'])  if random.random() < .5 else mutateRand('EDVisit',NewParameterVals[parent2]['EDVisit']),
                'preContagiousTime':mutateRand('preContagiousTime',NewParameterVals[parent1]['preContagiousTime'])  if random.random() < .5 else mutateRand('preContagiousTime',NewParameterVals[parent2]['preContagiousTime']),
                'postContagiousTime':mutateRand('postContagiousTime',NewParameterVals[parent1]['postContagiousTime'])  if random.random() < .5 else mutateRand('postContagiousTime',NewParameterVals[parent2]['postContagiousTime']),
                'NumInfStart':mutateRand('NumInfStart',NewParameterVals[parent1]['NumInfStart'])  if random.random() < .5 else mutateRand('NumInfStart',NewParameterVals[parent2]['NumInfStart']),
                'householdcontactRate':mutateRand('householdcontactRate',NewParameterVals[parent1]['householdcontactRate'])  if random.random() < .5 else mutateRand('householdcontactRate',NewParameterVals[parent2]['householdcontactRate']),
                'ProbabilityOfTransmissionPerContact':mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent1]['ProbabilityOfTransmissionPerContact'])  if random.random() < .5 else mutateRand('ProbabilityOfTransmissionPerContact',NewParameterVals[parent2]['ProbabilityOfTransmissionPerContact']),
                'symptomaticContactRateReduction':mutateRand('symptomaticContactRateReduction',NewParameterVals[parent1]['symptomaticContactRateReduction'])  if random.random() < .5 else mutateRand('symptomaticContactRateReduction',NewParameterVals[parent2]['symptomaticContactRateReduction']),
                'ImportationRate':mutateRand('ImportationRate',NewParameterVals[parent1]['ImportationRate'])  if random.random() < .5 else mutateRand('ImportationRate',NewParameterVals[parent2]['ImportationRate']),
                'AsymptomaticReducationTrans':mutateRand('AsymptomaticReducationTrans',NewParameterVals[parent1]['AsymptomaticReducationTrans'])  if random.random() < .5 else mutateRand('AsymptomaticReducationTrans',NewParameterVals[parent2]['AsymptomaticReducationTrans']),
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
            'symptomaticTime':mean(symptomaticTimevals),
            'hospitalSymptomaticTime':mean(hospitalSymptomaticTimevals),
            'ICURate':mean(ICURatevals),
            'ICUtime':mean(ICUtimevals),
            'PostICUTime':mean(PostICUTimevals),
            'hospTime':mean(hospTimevals),
            'EDVisit':mean(EDVisitvals),
            'preContagiousTime':mean(preContagiousTimevals),
            'postContagiousTime':mean(postContagiousTimevals),
            'NumInfStart':mean(NumInfStartvals),
            'householdcontactRate':mean(householdcontactRatevals),
            'ProbabilityOfTransmissionPerContact':mean(ProbabilityOfTransmissionPerContact),
            'symptomaticContactRateReduction':mean(symptomaticContactRateReduction),
            'ImportationRate':mean(ImportationRate),
            'AsymptomaticReducationTrans':mean(AsymptomaticReducationTrans)
        }
        print(finalvalsw)
        if os.path.exists(ParameterSet.ResultsFolder+"/MarylandFitVals_"+resultstimeName+".pickle"):
            finalvals = Utils.FileRead(ParameterSet.ResultsFolder+"/MarylandFitVals_"+resultstimeName+".pickle")
        finalvals[grun] = finalvalsw
        Utils.FileWrite(ParameterSet.ResultsFolder+"/MarylandFitVals_"+resultstimeName+".pickle",finalvals)


def WorkerJob(i,PV,AgeCohortInteraction,Model,modelPopNames,resultsName,MarylandFitData,grun):
    print("start-",grun,"-",i)
    endTime = PV['endTime']
    AG04AsymptomaticRate = PV['AG04AsymptomaticRate']
    AG04HospRate = PV['AG04HospRate']
    AG517AsymptomaticRate = PV['AG517AsymptomaticRate']
    AG517HospRate = PV['AG517HospRate']
    AG1849AsymptomaticRate = PV['AG1849AsymptomaticRate']
    AG1849HospRate = PV['AG1849HospRate']
    AG5064AsymptomaticRate = PV['AG5064AsymptomaticRate']
    AG5064HospRate = PV['AG5064HospRate']
    AG65AsymptomaticRate = PV['AG65AsymptomaticRate']
    AG65HospRate = PV['AG65HospRate']
    IncubationTime = PV['IncubationTime']
    totalContagiousTime = PV['totalContagiousTime']
    symptomaticTime = PV['symptomaticTime']
    hospitalSymptomaticTime = PV['hospitalSymptomaticTime']
    ICURate = PV['ICURate']
    ICUtime = PV['ICUtime']
    PostICUTime = PV['PostICUTime']
    hospTime = PV['hospTime']
    EDVisit = PV['EDVisit']
    preContagiousTime = PV['preContagiousTime']
    postContagiousTime = PV['postContagiousTime']
    NumInfStart = PV['NumInfStart']
    householdcontactRate = PV['householdcontactRate']
    ProbabilityOfTransmissionPerContact = PV['ProbabilityOfTransmissionPerContact']
    symptomaticContactRateReduction = PV['symptomaticContactRateReduction']
    ImportationRate = PV['ImportationRate']
    AsymptomaticReducationTrans = PV['AsymptomaticReducationTrans']
    
    #agecohort 0 -- 0-4
    AG04GammaScale = 5
    AG04GammaShape = 2.1
    AG04MortalityRate = 0.001
      
    #agecohort 1 -- 5-17
    AG517GammaScale = 5
    AG517GammaShape = 3
    AG517MortalityRate = 0.001
    
    #agecohort 2 -- 18-49
    AG1849GammaScale = 5
    AG1849GammaShape = 2.5
    AG1849MortalityRate = 0.01
     
    #agecohort 3 -- 50-64
    AG5064GammaScale = 5
    AG5064GammaShape = 2.3
    AG5064MortalityRate = 0.08
            
    #agecohort 4 -- 65+
    AG65GammaScale = 5
    AG65GammaShape = 2.1
    AG65MortalityRate = 0.15
    
    # First set all the parameters
    PopulationParameters = {}
    
    DiseaseParameters = {}
    
    DiseaseParameters['AGHospRate'] = [AG04HospRate,AG517HospRate,AG1849HospRate,AG5064HospRate,AG65HospRate]
    DiseaseParameters['AGAsymptomaticRate'] = [AG04AsymptomaticRate, AG517AsymptomaticRate, AG1849AsymptomaticRate, AG5064AsymptomaticRate,AG65AsymptomaticRate]
    DiseaseParameters['AGMortalityRate'] = [AG04MortalityRate,AG517MortalityRate,AG1849MortalityRate,AG5064MortalityRate,AG65MortalityRate]
            
    PopulationParameters['AGGammaScale'] = [AG04GammaScale,AG517GammaScale,AG1849GammaScale,AG5064GammaScale,AG65GammaScale]
    PopulationParameters['AGGammaShape'] = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
    PopulationParameters['householdcontactRate'] = householdcontactRate
    
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    
    ## Disease Progression Parameters
    DiseaseParameters['IncubationTime'] = IncubationTime
    DiseaseParameters['totalContagiousTime'] = totalContagiousTime
    DiseaseParameters['symptomaticTime'] = symptomaticTime
    DiseaseParameters['hospitalSymptomaticTime'] = hospitalSymptomaticTime
    DiseaseParameters['ICURate'] = ICURate
    DiseaseParameters['ICUtime'] = ICUtime
    DiseaseParameters['PostICUTime'] = PostICUTime
    DiseaseParameters['hospTime'] = hospTime
    DiseaseParameters['EDVisit'] = EDVisit
    DiseaseParameters['preContagiousTime'] = preContagiousTime
    DiseaseParameters['postContagiousTime']	= postContagiousTime
    DiseaseParameters['NumInfStart'] = NumInfStart
    DiseaseParameters['ImportationRate'] = ImportationRate
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = ProbabilityOfTransmissionPerContact
    DiseaseParameters['symptomaticContactRateReduction'] = symptomaticContactRateReduction
    DiseaseParameters['AsymptomaticReducationTrans'] = AsymptomaticReducationTrans
    DiseaseParameters['symptomaticContactRateReduction'] = symptomaticContactRateReduction
    
    ## Intervention Information
    DiseaseParameters['Intervention'] = 'baseline'
    DiseaseParameters['InterventionDate'] = -1
    DiseaseParameters['InterventionEndDate'] = -1
    DiseaseParameters['InterventionReductionSchool'] = 1        
    DiseaseParameters['InterventionReduction2'] = 1
    DiseaseParameters['InterventionReduction'] = 1
                
    results = GlobalModel.RunFitModelType(Model, modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime)
    
    # aggregate the results from each Local Population for each day
    resultsVals = {}
    for day in MarylandFitData.keys():
        resultsVals[day] = {
        'Infections':0,
        'Contagious':0,
        'Hospitalized':0,
        'dead':0,
        'ICU':0,
        'admissions':0
    }
    diffC = 0
    everHosp = 0
    for day in results.keys():
        inf = 0
        col = 0
        hos = 0
        dead = 0
        totHI = 0
        totN = 0
        totR = 0
        totD = 0
        totS = 0
        totHI = 0
        totHE = 0
        totICU = 0
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
                    totHI += lpdict['HI']             
                    totICU += lpdict['ICU']
                    totN += lpdict['N']
                    totR += lpdict['R']
                    totD += lpdict['D']
                    totS += lpdict['S']
                    totHI += lpdict['HI']
                    totHE += lpdict['HE']
       
        everHosp += totHI    
        x = datetime(2020, 4, 1) - timedelta(days=round(endTime,0)-day)
        #print(x," ",round(endTime,0)-day)
        if x >= datetime(2020, 3, 22) and x <= datetime(2020, 4, 1):
            resultsVals[x]['Infections'] += inf
            resultsVals[x]['Contagious'] += col
            resultsVals[x]['Hospitalized'] += hos
            resultsVals[x]['dead'] += dead
            resultsVals[x]['admissions'] += everHosp
            diffC += (hos - MarylandFitData[x]['hospitalized'])**2
            diffC += (everHosp - MarylandFitData[x]['admissions'])**2
            #diffC += (dead - MarylandFitData[x]['dead'])**2
    
    Utils.FileWrite(ParameterSet.ResultsFolder + "/FitResults_" + str(i) + "_" + resultsName + ".pickle",diffC)
    print("end-",grun,"-",i)
     
if __name__ == "__main__":
    # execute only if run as a script
    main()
