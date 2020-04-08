# -----------------------------------------------------------------------------
# WorkerProcess.py collects the local model(s) and creates a Priority Queue for
# each processing unit
# -----------------------------------------------------------------------------

import sys
import pickle
import time
import math
import os

import Region
import Utils
import ParameterSet


def BuildPops(q,i, RegionalLocations, RegionInteractionMatrixList, RegionListGuide, modelPopNames,HospitalTransitionMatrix=[]):
    region = Region.Region(RegionalLocations, RegionInteractionMatrixList, i, RegionListGuide,HospitalTransitionMatrix)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle", region)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "STATS.pickle", region.getRegionStats())




def RunTimeForward(i, tend, nextEventTime, modelPopNames,RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1):
    if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer):
        t1 = time.time()
    R = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle")
    if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer):
        t2 = time.time()

    saveRegion = False
    if len(RegionReconciliationEvents) > 0:
        R.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
        saveRegion = True

    infop = []
    if infectNumAgents > 0:
        if ParameterSet.ModelRunning == 'Wuhan':
            if R.IsThisWhuhanMktRegion()==1:
                infop, nextEventTime, regionStats = R.infectRandomAgents(infectNumAgents)
        else:
            infop, nextEventTime, regionStats = R.infectRandomAgents(infectNumAgents,LPIDinfect)
        saveRegion = True
        
    regionStats, offPopQueueEvents, numEvents, minEventTime = R.runTimePeriod(tend)
    #print(R.getInfectionEvents())
    
    if len(infop) > 0:
        offPopQueueEvents.extend(infop)
        
    if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer):
        t3 = time.time()
    regionStatsX = {}
    regionStatsX[i] = regionStats
    nextEventTime = {}
    nextEventTime[i] = minEventTime
    
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "RegionStats.pickle", regionStatsX)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "nextEventTime.pickle", nextEventTime)
    
    #q.put((regionStatsX, nextEventTime))
    
    if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer):
        t4 = time.time()
    if numEvents > 0 or saveRegion == True:
        Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle", R)
    if ParameterSet.debugmodelevel >= ParameterSet.debugtimer:
        t5 = time.time()
    Utils.FileWrite(ParameterSet.QueueFolder + "/" + str(modelPopNames) + str(i) + "Queue.pickle", offPopQueueEvents)
    
    hospOccupancyList = R.getHospitalOccupancy()
    if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle"):
        CurrentHospOccList = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
    else:
        CurrentHospOccList = {}
    CurrentHospOccList[tend] = hospOccupancyList  
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle", CurrentHospOccList)
    
    R0Stats = R.getR0Stats()
    R0StatsList = {}
    R0StatsList[i] = R0Stats
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle", R0StatsList)
    
    LPAgeStats = R.getAgeStats()
    AgeStatsList = {}
    AgeStatsList[i] = LPAgeStats
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "AgeStats.pickle", AgeStatsList)
    
    if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer):
        t6 = time.time()
    if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer):
        print(str(modelPopNames), i, ": load:", t2 - t1, " run:",
              t3 - t2, " loadQ:", t4 - t3, " write:", t5 - t4,  
              " writeQ:", t6 - t5, " Total:", t6 - t1)
    
    

def ReconcileInfectionEvents(q, i, RegionReconciliationEvents, modelPopNames):
    minEventTime = ParameterSet.MAXIntVal
    #print("Reconciling ",len(RegionReconciliationEvents)," events for ",i)
    #t = time.time()
    regionStatsX = {}
    if len(RegionReconciliationEvents) > 0:
        R = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle")
        nextEventTime, regionStats = R.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
        regionStatsX[i] = regionStats    
        if nextEventTime < minEventTime:
            minEventTime = nextEventTime
        Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle", R)
    minEventAdded = {i: math.floor(minEventTime)}
    #t2 = time.time()
    #print("Done Reconciling events for ",i," ",t2-t)
    
    
    q.put((regionStatsX,minEventAdded))


