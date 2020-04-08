# -----------------------------------------------------------------------------
# ProcessManager.py coordinates the worker processes for the global model
# -----------------------------------------------------------------------------

import multiprocessing
import math 
import random
import pickle
import os
import time
import gc
from datetime import datetime  
from datetime import timedelta  

import Region
import WorkerProcess
import Utils
import ParameterSet


def BuildGlobalPopulations(GlobalLocations,GlobalInteractionMatrix,modelPopNames,HospitalTransitionRate,numregions=0):
    num_regions = multiprocessing.cpu_count() * 2
    
    
    if numregions > 0:
        num_regions = numregions
    n = math.ceil(len(GlobalLocations) / num_regions)
    
    # Break the global locations list and interaction matrix into separate regional lists
    RegionInteractionMatrixList = []
    RegionalLocations = []
    RegionalList = []
    RegionListGuide = []
    HospitalTransitionMatrix = []
    for i in range(0,(len(GlobalLocations) + n - 1) // n ):
        RegionInteractionMatrixList.append(GlobalInteractionMatrix[i * n:(i + 1) * n,:])
        RegionalLocations.append(GlobalLocations[i * n:(i + 1) * n])
        if(len(HospitalTransitionRate) == len(GlobalInteractionMatrix)):
            HospitalTransitionMatrix.append(HospitalTransitionRate[i * n:(i + 1) * n,:])   
        RegionalList.append(i)
        numInList = (i + 1) * n - i * n
        for R in range(0,numInList):
            RegionListGuide.append(i)
            
    numInfList = {}
    q = multiprocessing.Queue()
    
    if(len(HospitalTransitionRate) == len(GlobalInteractionMatrix)):
        jobs = [ multiprocessing.Process(target=WorkerProcess.BuildPops, args=[q,i,RegionalLocations[i],RegionInteractionMatrixList[i],RegionListGuide,modelPopNames,HospitalTransitionMatrix[i]]) for i in range(0,len(RegionalList)) ]
    else:
        jobs = [ multiprocessing.Process(target=WorkerProcess.BuildPops, args=[q,i,RegionalLocations[i],RegionInteractionMatrixList[i],RegionListGuide,modelPopNames]) for i in range(0,len(RegionalList)) ]
    
    for j in jobs:
        j.start()
    	
    for j in jobs:
        j.join()
    
    print("finished creating pops")
    
    for i in range(0,len(RegionalList)):
        regionStats = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "STATS.pickle")
        numInfList[i] = regionStats
    
    return RegionalList, numInfList, RegionListGuide
    
def AllPopsExist(RegionalList,modelPopNames):
    for i in range(0,len(RegionalList)):
        if not os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle"):
            return False
    return True        


    
def RunFullModel(RegionalList,simLength,stepLength,modelPopNames,resultsName,numInfList, randomInfect,LocationImportationRisk=[],RegionListGuide=[],fithospdatapoint=-1):
    
    totInf = 0
    totC = 0
    totH = 0
    totN = 0
    totR = 0
    totS = 0
    totD = 0
    for key in numInfList.keys():
        rdict = numInfList[key]
        for rkey in rdict:
            lpdict = rdict[rkey]
            if len(lpdict) > 0:
                totInf += lpdict['I']
                totC += lpdict['C']
                totH += lpdict['H']
                totN += lpdict['N']
                totR += lpdict['R']
                totS += lpdict['S']
                totD += lpdict['D']
            
    if(ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        print("num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," NumC:",totC," numR:",totR," numD:",totD," numH:",totH)
    totvalue = totS+totN+totInf+totC+totR+totD
    
    timeNow = 0
    timeRange = []
    
    while timeNow < simLength:
        timeNow = timeNow + stepLength
        timeRange.append(timeNow)

    results = {}
    aggregatedresults = {}

    ### data for reconciliation
    offPopQueueEvents = []
    RegionReconciliationEvents = {} 
    testRegionValues = {}     
    for i in range(0,len(RegionalList)):
        RegionReconciliationEvents[i] = []
    
    nextEventTimeList = []
    for i in range(0,len(RegionalList)):
        nextEventTimeList.append(0)    
        
    for tend in timeRange:
        
        #print("*",numInfList)
        #ParameterSet.ImportationRate = tend
        #nextEventTimeList, numInfList = InfectRandomAgents(RegionalList, ParameterSet.ImportationRate, modelPopNames, numInfList,nextEventTimeList)
        
        # Infect Random Agents - linear increase in number infected
        infect = [0]*len(RegionalList)
        LPIDinfect = -1
        if randomInfect:
            if len(LocationImportationRisk) > 0:
                LPIDinfect = Utils.multinomial(LocationImportationRisk,sum(LocationImportationRisk))
                rnum = RegionListGuide[LPIDinfect]
            else:
                rnum = random.choice(RegionalList)
            infect[rnum] = ParameterSet.ImportationRate
            nextEventTimeList[rnum] = 0
        if ParameterSet.ModelRunning == 'Wuhan':
            if tend == 1:
                infect = [numStartingInfections]*len(RegionalList)
        
        #print("**",infect)
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotice):t1 = time.time()
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("start:",tend)
        #q = multiprocessing.Queue()
        jobs = []
        for i in range(0,len(RegionalList)):
            if nextEventTimeList[i] <= tend:
                #jobs.append(multiprocessing.Process(target=WorkerProcess.RunTimeForward,
                #                                    args=(q,i,tend,nextEventTimeList[i],
                #                                          modelPopNames,RegionReconciliationEvents[i],infect[i],LPIDinfect)))
                jobs.append(multiprocessing.Process(target=WorkerProcess.RunTimeForward,
                                                    args=(i,tend,nextEventTimeList[i],
                                                          modelPopNames,RegionReconciliationEvents[i],infect[i],LPIDinfect)))
        nextEventTime = {}
        for j in jobs:
            j.start()
        	
        for j in jobs:  
            j.join()
            
        #for j in jobs:
        #    numinfVals, minEventTime = q.get()
        #    for key in numinfVals.keys():
        #        numInfList[key] = numinfVals[key]
        #    nextEventTime.update(minEventTime)
        
        for i in range(0,len(RegionalList)):
            numinfVals = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "RegionStats.pickle")
            for key in numinfVals.keys():
                numInfList[key] = numinfVals[key]
            minEventTime = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "nextEventTime.pickle")
            nextEventTime.update(minEventTime)
            
        totInf = 0
        totC = 0
        totH = 0
        totN = 0
        totR = 0
        totD = 0
        totS = 0
        totHI = 0
        totHE = 0
        x = 0
        totICU = 0
        for key in numInfList.keys():
            rdict = numInfList[key]
            for rkey in rdict:
                lpdict = rdict[rkey]
                if len(lpdict) > 0:
                    totInf += lpdict['I']
                    totC += lpdict['C']
                    totH += lpdict['H']
                    totICU += lpdict['ICU']
                    totN += lpdict['N']
                    totR += lpdict['R']
                    totD += lpdict['D']
                    totS += lpdict['S']
                    totHI += lpdict['HI']
                    totHE += lpdict['HE']
        
        for key in nextEventTime:
            if nextEventTime[key] > nextEventTimeList[key]:
                nextEventTimeList[key] = nextEventTime[key]
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotice): t2 = time.time()
        
        #if(ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
        #    print("Finished Main Run:",tend," Time:",t2-t1)
        
        #print("**",numInfList)
        
        offPopQueueEvents = []
        ### Now compile the reconcile events list for the next run
        for i in range(0,len(RegionalList)):
            testRegionValues[i] = 0
            RegionReconciliationEvents[i] = []
            try:
                OPQE = Utils.FileRead(ParameterSet.QueueFolder+"/"+str(modelPopNames)+str(i)+"Queue.pickle")
            except:
               OPQE = None 
            if OPQE:
                offPopQueueEvents.extend(OPQE)
            try:
                os.remove(ParameterSet.QueueFolder+"/"+str(modelPopNames)+str(i)+"Queue.pickle")
            except:
                if(ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("ProcessManager:ReconcileEventsProcess():File Not Found for Removal: Queues/"+str(modelPopNames)+str(i)+"Queue.pickle")
        ## Sort them by region            
        for QE in offPopQueueEvents:
            #ts = QE.getEventTime()
            R = QE.getRegionId()
            testRegionValues[R]+=1
            RegionReconciliationEvents[R].append(QE)
            #numOffPopEvents += 1
            #self.eventQueue[ts] = QE          
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): t2 = time.time()
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("Time to get queues:",t2-t1)

        #print("***",numInfList)
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
            t3 = time.time()
        if(ParameterSet.debugmodelevel >= ParameterSet.debugnotice):
            if ParameterSet.ModelRunning == 'Wuhan':
                x = datetime(2020, 1, 23) - timedelta(days=timeRange[len(timeRange)-1]-tend) 
            elif ParameterSet.ModelRunning == 'MarylandFit':
                x = datetime(2020, 4, 1) - timedelta(days=timeRange[len(timeRange)-1]-tend) 
            else:          
                x = datetime(2020, 2, 1) + timedelta(days=tend) 
            
            #print("End:",tend," (",(x.strftime('%Y-%m-%d')),") Time:",t3-t1,"(",t3-t2,") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," NumC:",totC," numR:",totR," numD:",totD," numH:",totH," R0:",round(R0,2)," R0R:",round(R0R,2)," R0HH:",round(R0HH,2)," HI:",totHI," HE:",totHE)
            
            R0Stats = [0]*101
            for i in range(0,len(RegionalList)):
                if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle"):
                    R0StatsList = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle")
                    for key in R0StatsList.keys():
                        R0Stat = R0StatsList[key]
                        for rkey in R0Stat.keys():
                            rvals = R0Stat[rkey]
                            for r in range(0,len(rvals)):
                                R0Stats[r] += rvals[r]
            rnum = 0
            rdenom = 0
            for i in range(1,len(R0Stats)):
                rdenom += R0Stats[i]
                rnum += R0Stats[i]*i            
            if rdenom > 0:
                R0Val = rnum/rdenom
            else:
                R0Val = 0
            #print("End:",tend," (",(x.strftime('%Y-%m-%d')),") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," NumC:",totC," numR:",totR," numD:",totD," numH:",totH,"(" ,totICU,") R0:",round(R0,2)," R0R:",round(R0R,2)," R0HH:",round(R0HH,2)," HI:",totHI," HE:",totHE, " A:",Ai," In:",In," InR:",InR," InH:",InH)
            print("End:",tend," (",(x.strftime('%Y-%m-%d')),") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," NumC:",totC," numR:",totR," numD:",totD," numH:",totH,"(" ,totICU,") R0:",round(R0Val,2))
            
        if totS+totN+totInf+totC+totR+totD != totvalue:
            exit()
        
        # write out results to disk in case process dies
        if os.path.exists(ParameterSet.ResultsFolder+"/Results_"+resultsName+".pickle"):
            results = Utils.FileRead(ParameterSet.ResultsFolder+"/Results_"+resultsName+".pickle")
        results[tend] = numInfList
        Utils.FileWrite(ParameterSet.ResultsFolder+"/Results_"+resultsName+".pickle",results)
        
        if fithospdatapoint > 0:
            if totHI >= fithospdatapoint:
                if os.path.exists(ParameterSet.ResultsFolder+"/FittedResults_"+resultsName+".pickle"):
                    results = Utils.FileRead(ParameterSet.ResultsFolder+"/FittedResults_"+resultsName+".pickle")
                results[tend] = numInfList
                Utils.FileWrite(ParameterSet.ResultsFolder+"/FittedResults_"+resultsName+".pickle",results)
        
        gc.collect()
        
        #input("Press Enter to continue...")

