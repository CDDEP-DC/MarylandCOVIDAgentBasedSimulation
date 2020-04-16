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


def BuildPops(i,PopulationParameters,DiseaseParameters,SimEndDate, RegionalLocations, RegionInteractionMatrixList, RegionListGuide, modelPopNames,HospitalTransitionMatrix=[]):
    region = Region.Region(RegionalLocations, RegionInteractionMatrixList, i, RegionListGuide,HospitalTransitionMatrix,PopulationParameters,DiseaseParameters,SimEndDate)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle", region)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "STATS.pickle", region.getRegionStats())


def RunRegionForward(i,PopulationParameters,DiseaseParameters,R, tend, modelPopNames,RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1):
                    
    saveRegion = False
    if len(RegionReconciliationEvents) > 0:
        R.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
        saveRegion = True

    infop = []
    if infectNumAgents > 0:
        if ParameterSet.ModelRunning == 'Wuhan':
            if R.IsThisWhuhanMktRegion()==1:
                infop, regionStats = R.infectRandomAgents(infectNumAgents)
        else:
            infop, regionStats = R.infectRandomAgents(infectNumAgents,LPIDinfect)
        saveRegion = True
        
    regionStats, offPopQueueEvents, numEvents = R.runTimePeriod(tend)
    
    if len(infop) > 0:
        offPopQueueEvents.extend(infop)
        
    regionStatsX = {}
    regionStatsX[i] = regionStats
        
    hospOccupancyList = R.getHospitalOccupancy()
    
    R0Stats = R.getR0Stats()
    R0StatsList = {}
    R0StatsList[i] = R0Stats
    
    LPAgeStats = R.getAgeStats()
    AgeStatsList = {}
    AgeStatsList[i] = LPAgeStats
    
    return numEvents,saveRegion, regionStatsX,R,offPopQueueEvents,hospOccupancyList,R0StatsList,AgeStatsList
    

def RunTimeForward(i,PopulationParameters,DiseaseParameters, tend, modelPopNames,RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1):
    
    R = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle")
    
    numEvents,saveRegion, regionStatsX,R,offPopQueueEvents,hospOccupancyList,R0StatsList,AgeStatsList = RunRegionForward(i,PopulationParameters,DiseaseParameters,R, tend, modelPopNames,RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1)
    
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "RegionStats.pickle", regionStatsX)
    
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + ".pickle", R)
    
    Utils.FileWrite(ParameterSet.QueueFolder + "/" + str(modelPopNames) + str(i) + "Queue.pickle", offPopQueueEvents)
    
    if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle"):
        CurrentHospOccList = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
    else:
        CurrentHospOccList = {}
    CurrentHospOccList[tend] = hospOccupancyList  
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle", CurrentHospOccList)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "R0Stats.pickle", R0StatsList)
    Utils.FileWrite(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "AgeStats.pickle", AgeStatsList)
    
    


