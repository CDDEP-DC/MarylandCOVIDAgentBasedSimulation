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
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle"), region)
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"STATS.pickle"), region.getRegionStats())


def RunRegionForward(i,PopulationParameters,DiseaseParameters,R, tend, modelPopNames,RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1):
                    
    if len(RegionReconciliationEvents) > 0:
        R.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
    
    infop = []
    if infectNumAgents > 0:
        if ParameterSet.ModelRunning == 'Wuhan':
            if R.IsThisWhuhanMktRegion()==1:
                infop = R.infectRandomAgents(tend,infectNumAgents)
        else:
            infop = R.infectRandomAgents(tend,infectNumAgents,LPIDinfect)
        
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
    
    return numEvents, regionStatsX,R,offPopQueueEvents,hospOccupancyList,R0StatsList,AgeStatsList
    

def RunTimeForward(i,PopulationParameters,DiseaseParameters, tend, modelPopNames,RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1):
    
    R = Utils.FileRead(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle"))
    
    numEvents, regionStatsX,R,offPopQueueEvents,hospOccupancyList,R0StatsList,AgeStatsList = \
                RunRegionForward(i,PopulationParameters,DiseaseParameters,R, tend, modelPopNames, \
                                    RegionReconciliationEvents,infectNumAgents,LPIDinfect=-1)
    
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"), regionStatsX)
    
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle"), R)
    
    Utils.FileWrite(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"), offPopQueueEvents)
    
    if os.path.exists(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"HOSPLIST.pickle")):
        CurrentHospOccList = Utils.FileRead(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"HOSPLIST.pickle"))
    else:
        CurrentHospOccList = {}
    CurrentHospOccList[tend] = hospOccupancyList  
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"HOSPLIST.pickle"), CurrentHospOccList)
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"R0Stats.pickle"), R0StatsList)
    Utils.FileWrite(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"AgeStats.pickle"), AgeStatsList)
    
    


