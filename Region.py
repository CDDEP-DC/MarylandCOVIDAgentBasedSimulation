"""

Copyright (C) 2020  Eili Klein

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
    

"""

import random
import time
import math

import LocalPopulation
import events.SimulationEvent as SimEvent
import ParameterSet


class Region:
    def __init__(self, RegionalLocations, RegionalInteractionMatrixList,
                 RegionId, RegionListGuide,HospitalTransitionMatrixList,PopulationParameters,DiseaseParameters,SimEndDate):
        """
        class represents a local location for the agent

        :param localgriddata: spatial 2D array with population density of local
        :type localgriddata: array
        :param agedist: age distribution [number of child, number of adults]
        :type agedist: list
        """
        # self.RegionalLocations = RegionalLocations
        # self.RegionalInteractionMatrixList = RegionalInteractionMatrixList
        self.RegionId = RegionId
        self.Locations = {}
        self.IsWhuhanMktRegion = 0
        
        # create local population for each point in the local block
        for i in range(0, len(RegionalLocations)):
            GLP = RegionalLocations[i]
            HTM = []
            if len(HospitalTransitionMatrixList) > 0:
                HTM = HospitalTransitionMatrixList[i]
                    
            if(GLP.globalId==ParameterSet.WuhanMktLocalPopId):
                self.IsWhuhanMktRegion = 1
                
            LP = LocalPopulation. \
                LocalPopulation(GLP.globalId, GLP.populationAmt,
                                GLP.HHSizeDist, GLP.HHSizeAgeDist,
                                RegionalInteractionMatrixList[i], self.RegionId,
                                RegionListGuide,HTM,GLP.LocalIdentification,GLP.RegionalIdentification,PopulationParameters,DiseaseParameters,SimEndDate,
                                GLP.ProportionLowIntReduction,GLP.NursingFacilities,GLP.TransProb,GLP.TransProbLow)
            self.Locations[GLP.globalId] = LP
            
    def IsThisWhuhanMktRegion(self):
        return self.IsWhuhanMktRegion
    
    def runTimePeriod(self, tend,testlpvals=[]):
        #print(testlpvals)
        offPopQueueEvents = []
        regionStats = {}
        R0Stats = {}
        hospitalStats = {}
        numEvents = 0
        fitdeaths = 0
        fithospitalizations = 0
        fitcases = 0
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            op, NE = LP.runTime(tend,LP.LocalPopulationId in testlpvals)
            numEvents += NE
            offPopQueueEvents.extend(op)
            regionStats[LPKey] = LP.reportPopulationStats()
            if ParameterSet.FitMD:
                if regionStats[LPKey]['regionalid'] == 'MD':
                    fithospitalizations += regionStats[LPKey]['H']        
                    fitdeaths += regionStats[LPKey]['D']
                    fitcases += regionStats[LPKey]['CC']        
            else:
                fithospitalizations += regionStats[LPKey]['H']        
                fitdeaths += regionStats[LPKey]['D']        
                fitcases += regionStats[LPKey]['CC']        
        fitval = [fithospitalizations,fitdeaths,fitcases]
        return regionStats, offPopQueueEvents, numEvents, fitval

    def getInfectedNums(self):
        infectedNums = {}
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            #infectedNums.update(LP.reportNumInfected())
            infectedNums.update({LP.LocalPopulationId: LP.numInfected})

        return infectedNums

    def getInfectionEvents(self):
        infEvents = []
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            agentEvents = LP.getInfectionEvents()
            infEvents.extend(agentEvents)
        print(infEvents)
        
    def infectRandomAgents(self,tend,numInfect,OneLocalOnly=True,LPID =-1):
        # Create off popqueue
        offPopQueueEvents = []
        # If we are only infecting on region
        if OneLocalOnly:
            if LPID < 0:
                if ParameterSet.WuhanMktLocalPopId >= 0:
                    LPID = ParameterSet.WuhanMktLocalPopId
                else:
                    LPID = random.choice(list(self.Locations.keys()))
                
            LP = self.Locations[LPID]
            for i in range(0,numInfect):
                op = LP.infectRandomAgent(tend)
                offPopQueueEvents.extend(op)
            
        else:
            LPIDs = []
            for i in range(0,numInfect):
                LPIDs.append(random.choice(list(self.Locations.keys())))
            
            LPIDs.sort()
            LPID = -1
            for i in range(0,len(LPIDs)):
                LPID = LPIDs[i]
                LP = self.Locations[LPID]
                op = LP.infectRandomAgent(tend)
                offPopQueueEvents.extend(op)
                    
        return offPopQueueEvents


    def addEventsFromOtherLocalPopulations(self,RegionReconciliationEvents):
        for QE in RegionReconciliationEvents:
            if isinstance(QE,SimEvent.NonLocalInfectionEvent):
                LPID = QE.LocalPopulationId
                LP = self.Locations[LPID]
                LP.addEventsFromOtherLocalPopulations(QE)
            elif isinstance(QE,SimEvent.ClearInfectionEvents):
                LPID = QE.LocalPopulationId
                LP = self.Locations[LPID]
                LP.clearInfectionEvents(QE)
                
        return self.getRegionStats()
                    
    def initializeHistory(self,historyData):
        numpriorcases = 0
        numnewcases = 0 
        for zipcode in historyData.keys():
            for LPKey in self.Locations.keys():
                
                LP = self.Locations[LPKey]
                if LP.LocalIdentification == zipcode:
                    LP.initializeHistory(historyData[zipcode]['PriorCases'])
                    numpriorcases += int(historyData[zipcode]['PriorCases'])
                    op = LP.setCurrentCases(historyData[zipcode]['NewCases'])
                    numnewcases += int(historyData[zipcode]['NewCases'])
                    offPopQueueEvents.extend(op)
                    break
        return offPopQueueEvents, numpriorcases, numnewcases
                    
    def getRegionStats(self):
        regionStats = {}
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            regionStats[LPKey] = LP.reportPopulationStats()
        return regionStats

    def getHospitalOccupancy(self):
        hospLists = {}
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            hospLists[LPKey] = LP.getHospitalOccupancy()
        return hospLists
        
    def getR0Stats(self):
        R0Lists = {}
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            R0Lists[LPKey] = LP.getR0Stats()
        return R0Lists  
        
    def getAgeStats(self):
        AgeLists = {}
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            AgeLists[LPKey] = LP.getAgeStats()
        return AgeLists    
        
    def getLastTime(self):
        maxTime = 0
        for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            LPtime = LP.timeNow
            if LPtime > maxTime:
                maxTime = LPtime
        return maxTime
        
    def resetParameters(self,GlobalLocations,PopulationParameters,DiseaseParameters,SimEndDate):
                 
         for LPKey in self.Locations.keys():
            LP = self.Locations[LPKey]
            LPID = LP.LocalPopulationId
            GLP = GlobalLocations[LPID]    
                    
            LP.resetParameters(PopulationParameters,DiseaseParameters,SimEndDate,
                                GLP.ProportionLowIntReduction,GLP.TransProb,GLP.TransProbLow)
             