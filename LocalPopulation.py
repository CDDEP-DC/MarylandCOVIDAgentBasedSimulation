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
import numpy as np
import traceback
from statistics import mean
import ParameterSet
import events.SimulationEvent as SimEvent
import Utils
import agents.AgentClasses
import copy

class LocalPopulation:
    def __init__(self, LocalPopulationId, npersons, HHSizeDist, HHSizeAgeDist,
                 LocalInteractionMatrixList, RegionId, RegionListGuide,HospitalTransitionMatrixList,LocalIdentification,
                    RegionalIdentification,PopulationParameters,DiseaseParameters,SimEndDate,ProportionLowIntReduction,
                    NursingFacilities,TransProb,TransProbLow):
        """
        initalize class and builds synthetic population for local point

        :param LocalPopulationId: local coordinates
        :type LocalPopulationId: tuple
        :param npersons: number of agents
        :type npersons: int
        :param agedist: [avg num of children, avg num of adults]
        :type agedist: list

        """
        self.LocalPopulationId = LocalPopulationId
        self.LocalIdentification = str(LocalIdentification)
        self.RegionalIdentification = RegionalIdentification
        self.timeNow = 0
        self.RegionId = RegionId
        self.HHSizeDist = HHSizeDist
        self.HHSizeAgeDist = HHSizeAgeDist
        self.SimEndDate = SimEndDate
        self.ProportionLowIntReduction = ProportionLowIntReduction
        self.NursingFacilities = NursingFacilities
        self.NursingFacilitiesAdded = 0

        self.PopulationParameters = PopulationParameters
        self.DiseaseParameters = DiseaseParameters
        self.TransProb = TransProb
        self.TransProbLow = TransProbLow
        
        
        self.UndefinedAgents = npersons
        self.DefinedAgents = 0
        self.EphermeralAgents = 0
        self.npersons = npersons #save original pop
        self.currHouseholdIDNum = 0
        
        # Interaction matrix with other populations
        self.LocalInteractionMatrixList = LocalInteractionMatrixList
        self.RegionListGuide = RegionListGuide
        self.HospitalTransitionMatrixList = HospitalTransitionMatrixList
        self.HospitalInfectionList = []
        self.HospitalICUInfectionList = []
        self.HospitalNewInfectionList = []
        self.HospitalNewEDList = []
        self.ageInfectionHosp = []
        self.ageMortality = []
        self.ageInfection = []
        for i in range(0,5):
            self.ageInfection.append(0)
            self.ageInfectionHosp.append(0)
            self.ageMortality.append(0)

        if ParameterSet.SaveHospitalData:    
            for i in range(0,len(HospitalTransitionMatrixList)):
                self.HospitalInfectionList.append(0)
                self.HospitalNewInfectionList.append(0)
                self.HospitalNewEDList.append(0)
                self.HospitalICUInfectionList.append(0)
        
        self.numSusceptible = npersons
        self.numInfected = 0
        self.numContagious = 0
        self.numIncubating = 0
        self.numRecovered = 0
        self.numHospitalized = 0
        self.numHospitalizedICU = 0
        self.numDead = 0
        self.numTests = 0
        
        self.numQuarantined = 0
        self.InfectiousEventsPrevented = 0
        self.InfectiousEventsCleared = 0
        self.confirmedcases = 0
        
        self.R0Calc = [0]*101
            
        #self.infectionEvents = []
        # Event queue is a dictionary
        self.eventQueue = {}

        # Households
        self.hhset = {}
        
    def BuildSingleHousehold(self):
        
        numtries = 0
        maxval = self.npersons - self.DefinedAgents - self.EphermeralAgents

        addNF = False
        if self.NursingFacilities > 0 and self.NursingFacilitiesAdded < self.NursingFacilities and maxval > 130:
            if random.random() < ((self.NursingFacilities*130) / self.npersons):
                addNF = True
                HHSize = 130
        
        if not addNF:
            # this is to make sure we don't make a household that pushes over the size of the population
            HHSize = maxval + 1
            
            while (HHSize+1) > maxval:
                
                HHSize = Utils.multinomial(self.HHSizeDist, sum(self.HHSizeDist))
                numtries += 1
                if numtries > 100:
                    #print(HHSize+1," ",maxval," ",numdefinedagents, " " , infectperson)
                    print("BuildSingleHousehold: LOOP ERROR")
                    break

        # Now create household
        HH = agents.AgentClasses.Household(self.currHouseholdIDNum, HHSize, self.HHSizeAgeDist,self.PopulationParameters,Facility=addNF)
        self.hhset[self.currHouseholdIDNum] = HH
        self.currHouseholdIDNum += 1
        self.UndefinedAgents -= (HHSize + 1)
        self.DefinedAgents += (HHSize + 1)
        
        return HH.HouseholdId
    
    def reportPopulationStats(self):
        stats = {}
        stats['S'] = self.numSusceptible
        stats['N'] = self.numIncubating
        stats['I'] = self.numInfected
        stats['C'] = self.numContagious
        stats['R'] = self.numRecovered
        stats['H'] = self.numHospitalized
        stats['D'] = self.numDead
        stats['ICU'] = self.numHospitalizedICU
        if ParameterSet.SaveHospitalData:
            stats['HI'] = sum(self.HospitalNewInfectionList)
            stats['HE'] = sum(self.HospitalNewEDList)
        else:    
            stats['HI'] = -1
            stats['HE'] = -1
        stats['localpopid'] = self.LocalIdentification
        stats['regionalid'] = self.RegionalIdentification
        stats['numTests'] = self.numTests
        stats['numQ'] = self.numQuarantined
        stats['numInfPrev'] = self.InfectiousEventsPrevented
        stats['InfEvtClear'] = self.InfectiousEventsCleared
        stats['CC'] = self.confirmedcases
        return stats

    def getHospitalOccupancy(self):
        hospstats = {}
        hospstats['occupancy'] = self.HospitalInfectionList
        hospstats['ICU'] = self.HospitalICUInfectionList
        hospstats['admissions'] = self.HospitalNewInfectionList
        hospstats['edvisits'] = self.HospitalNewEDList
        return hospstats
        
    def getR0Stats(self):
        return self.R0Calc    

    def getAgeStats(self):
        ageStats = {}
        ageStats['ageInfection'] = self.ageInfection
        ageStats['ageInfectionHosp'] = self.ageInfectionHosp
        ageStats['ageMortality'] = self.ageMortality
        return ageStats
        

    def runTime(self, tend,testExtra):
        addEvents = []
        delkeys = []
        
 
        sortedKeys = sorted(self.eventQueue.keys())
        offPopQueueEvents = []
        localQevents = []
        numevents = 0
        eventTime = tend
        ## reset the daily infection lists
        if ParameterSet.SaveHospitalData:
            for i in range(0,len(self.HospitalNewInfectionList)):
                self.HospitalNewInfectionList[i] = 0
            for i in range(0,len(self.HospitalNewEDList)):
                self.HospitalNewEDList[i] = 0
        
        if len(sortedKeys) == 0:
            self.timeNow = tend
            
        for key in sortedKeys:
            SE = self.eventQueue[key]
            eventTime = SE.timestamp

            if eventTime < tend:
                numevents += 1
                self.timeNow = eventTime
                # now need to add getting the type of event -- case statements etc
                                
                if isinstance(SE,SimEvent.InfectionEvent):                
                    #print("Infection")
                    infectingAgent = {}
                    infectingAgent['personId'] = SE.infectingAgentId
                    infectingAgent['HHID'] = SE.infectingAgentHHID
                    if isinstance(SE,SimEvent.NonLocalInfectionEvent):
                        infectingAgent['LPID'] = SE.LocalPopulationId
                        infectingAgent['RegionId'] = SE.RegionId
                    else:
                        infectingAgent['LPID'] = self.LocalPopulationId
                        infectingAgent['RegionId'] = self.RegionId
                    
                    op = self.infectRandomAgent(self.timeNow,SE.ageCohort,infectingAgent)
                    
                    # add Events to non local pop queue
                    offPopQueueEvents.extend(op)    
                elif isinstance(SE,SimEvent.PersonStatusUpdate):
                    #print("status update")
                    HHID = SE.HouseholdId
                    personId = SE.PersonId
                    currentStatus = self.hhset[HHID].getHouseholdPersonStatus(personId)
                    xbefore = "Before:"+str(currentStatus)+"-->"+str(SE.Status)+" S:"+str(self.numSusceptible)+" N:"+str(self.numIncubating)+" C:"+str(self.numContagious)+" I:"+str(self.numInfected)+" R:"+str(self.numRecovered)+" H:"+str(self.numHospitalized)
                    checkval = self.numSusceptible+self.numIncubating+self.numContagious+self.numInfected+self.numRecovered+self.numDead
                    
                    
                    # If updating to incubating -- patient could only be susceptible
                    if SE.Status == ParameterSet.Incubating:
                        self.numIncubating += 1                
                        self.numSusceptible -= 1
                    
                    # If updating to Contagious
                        # could have been incubating or been symptomatic                        
                    elif SE.Status == ParameterSet.Contagious:
                        if currentStatus == ParameterSet.Incubating:
                            self.numIncubating -= 1
                        elif currentStatus == ParameterSet.Symptomatic:
                            self.numInfected -= 1
                        elif currentStatus == ParameterSet.Susceptible:
                            self.numSusceptible -= 1
                        self.numContagious += 1
                        
                    # if updating to symptomatic could only have been contagious (added incubating for possible later change)
                    elif SE.Status == ParameterSet.Symptomatic:
                        if currentStatus == ParameterSet.Incubating:
                            self.numIncubating -= 1
                        elif currentStatus == ParameterSet.Contagious:    
                            self.numContagious -= 1
                        self.numInfected += 1
                        
                    # if updating to recovered could have come from symptomatic or contagious
                    elif SE.Status == ParameterSet.Recovered or SE.Status == ParameterSet.Dead:
                        
                        if currentStatus == ParameterSet.Symptomatic:
                            self.numInfected -= 1
                        elif currentStatus == ParameterSet.Contagious:    
                            self.numContagious -= 1
                        elif currentStatus == ParameterSet.Incubating:    
                            self.numIncubating -= 1
                        if SE.Status == ParameterSet.Dead:
                            self.ageMortality[self.hhset[HHID].getPersonAgeCohort(personId)]+=1
                            self.numDead += 1                      
                        else:
                            self.numRecovered += 1
                        # we assume if they recover/died and they were in the hospital, they leave the hospital
                        if(self.hhset[HHID].getHouseholdPersonHospStatus(personId)==1):
                            HospId = self.hhset[HHID].getPersonHospital(personId)
                            self.hhset[HHID].setHouseholdPersonHospStatus(personId,0)
                            self.numHospitalized -= 1
                            #print("Patient left " + str(HospId),self.numHospitalized,self.HospitalInfectionList)
                            if ParameterSet.SaveHospitalData:
                                self.HospitalInfectionList[HospId]-=1
                            
                            
                        # check if everyone is recovered, if so delete household
                        if self.hhset[HHID].deleteHousehold():
                            HHSize = self.hhset[HHID].getHouseholdSize()
                            #print("all infected ",HHSize)
                            self.DefinedAgents -= HHSize
                            self.EphermeralAgents += HHSize
                            del self.hhset[HHID]
                            #print(npersons," = ",numnotdefinedagents," + ",numdefinedagents," + ",numrecovereddeadagents)
                    else:
                        print("Need to throw error here2 ... something went wrong")
                        
                    self.hhset[HHID].setHouseholdPersonStatus(personId,SE.Status)
                        
                        
                    checkval2 = self.numSusceptible+self.numIncubating+self.numContagious+self.numInfected+self.numRecovered+self.numDead
                    if checkval != checkval2:
                        print(xbefore)
                        print(self.timeNow,"After S:",self.numSusceptible," N:",self.numIncubating," C:",self.numContagious," I:",self.numInfected," R:",self.numRecovered," H:",self.numHospitalized)
                        exit()
                    
                elif isinstance(SE,SimEvent.PersonHospEvent): 
                    #print("hosp")
                    # Person went to the hospital/er/doctor
                    HHID = SE.HouseholdId
                    personId = SE.PersonId
                    Hospital = SE.Hospital
                    # First check if they were hospitalized
                    # if they were then assign them to a hospital and update their status
                    # for quarantine check that they quarantine or now
                    if isinstance(SE,SimEvent.PersonHospCritEvent) or isinstance(SE,SimEvent.PersonHospICUEvent): 
                        if self.timeNow > self.DiseaseParameters['TestingAvailabilityDateHosp']:
                            self.numTests += 1
                            self.confirmedcases += 1
                        self.ageInfectionHosp[self.hhset[HHID].getPersonAgeCohort(personId)]+=1
                        if ParameterSet.SaveHospitalData:
                            self.HospitalInfectionList[Hospital]+=1
                        if isinstance(SE,SimEvent.PersonHospICUEvent):
                            if ParameterSet.SaveHospitalData:
                                self.HospitalICUInfectionList[Hospital]+=1
                            self.numHospitalizedICU += 1
                        if ParameterSet.SaveHospitalData:
                            self.HospitalNewInfectionList[Hospital]+=1
                            self.hhset[HHID].setHouseholdPersonHospStatus(personId,1,Hospital)
                        self.numHospitalized += 1
                        ### Add contact tracing / quarantine if started
                        if self.timeNow > self.DiseaseParameters['QuarantineStartDate']:
                            # If intervention includes tracing contacts and testing them
                            if self.DiseaseParameters['ContactTracing'] == 1:
                                localQevents,offPopQueueEvents = self.addContactTracing(tend,HHID,personId,localQevents,offPopQueueEvents)
                                
                            if self.DiseaseParameters['QuarantineType'] == 'household':
                                if random.random() < self.DiseaseParameters['PerFollowQuarantine']:
                                    PIDs = self.hhset[HHID].getPersonIDs()
                                    for pp in range(0,len(PIDs)):
                                        if pp != personId:
                                            offPopQueueEvents,delkeys = self.clearForwardInfections(tend,HHID,pp,offPopQueueEvents,delkeys) 
                                            self.numQuarantined += 1
                                            # If intervention includes tracing contacts and testing them, then test household
                                            if self.DiseaseParameters['ContactTracing'] == 1:
                                                localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,pp,localQevents,offPopQueueEvents,delkeys,clearInfections=False) ### adds quarantine events if positive / already cleared events so no need to do so again
                                    
                    elif isinstance(SE,SimEvent.PersonHospExitICUEvent):
                        if ParameterSet.SaveHospitalData:
                            self.HospitalICUInfectionList[Hospital]-=1
                        self.numHospitalizedICU -= 1
                    else:
                        if ParameterSet.SaveHospitalData:
                            self.HospitalNewEDList[Hospital]+=1
                        if isinstance(SE,SimEvent.PersonHospTestEvent):
                            testdate = self.DiseaseParameters['TestingAvailabilityDateComm']
                        else:
                            testdate = self.DiseaseParameters['TestingAvailabilityDateHosp']
                        
                        if self.timeNow > testdate:
                            localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,personId,localQevents,offPopQueueEvents,delkeys) ### adds quarantine events if positive
                            # if detected then if they                                 
                            if detected and self.DiseaseParameters['QuarantineType'] == 'household' and self.timeNow > self.DiseaseParameters['QuarantineStartDate'] and followQuarantine:
                                PIDs = self.hhset[HHID].getPersonIDs()
                                for pp in range(0,len(PIDs)):
                                    if pp != personId:
                                        offPopQueueEvents,delkeys = self.clearForwardInfections(tend,HHID,pp,offPopQueueEvents,delkeys) 
                                        self.numQuarantined += 1
                                        # If intervention includes tracing contacts and testing them, then test household
                                        if self.DiseaseParameters['ContactTracing'] == 1:
                                            localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,pp,localQevents,offPopQueueEvents,delkeys,clearInfections=False) ### adds quarantine events if positive / already cleared events so no need to do so again
                        
                elif isinstance(SE,SimEvent.HouseholdInfectionEvent):
                    #print("house")
                    HHID = SE.HouseholdId
                    agentId = SE.PersonId
                    op = self.infectAgent(self.timeNow,HHID,agentId=agentId)
                        
                elif isinstance(SE,SimEvent.ContactTraceEvent):
                    #1. get the number of infections by this person
                    #2. if > 0 then clear the local ones and set flags to clear the non-local
                    infectingAgentId = SE.infectingAgentId
                    infectingAgentHHID = SE.infectingAgentHHID
                    infectingAgentRegionId = SE.RegionId
                    infectingAgentLPID = SE.LocalPopulationId
                    NumPeopleToLookFor = SE.NumPeopleToLookFor
                    HHIDSToQ = []
                    PersonIdsToQ = []
                    numPFound = 0
                    PContactRate = self.hhset[infectingAgentHHID].getPersonRandomContactRate(infectingAgentId)
                    if PContactRate > ParameterSet.MaxQuarantinePeople:
                        PContactRate = ParameterSet.MaxQuarantinePeople
                        
                    # Quarantine everyone they had contact with
                    if NumPeopleToLookFor > 0:
                        for HHID in range(0,self.currHouseholdIDNum):
                            if HHID in self.hhset.keys():
                                personId = self.hhset[HHID].WasInfectedByThisPerson(infectingAgentId,infectingAgentHHID,infectingAgentLPID,infectingAgentRegionId)
                                if personId >= 0:
                                    HHIDSToQ.append(HHID)
                                    PersonIdsToQ.append(personId)
                                    numPFound += 1
                                    if numPFound == NumPeopleToLookFor or numPFound == PContactRate:
                                        break                
                                        
                    # then randomly quarantine some additional people if we haven't made it to the persons contacts yet
                    while numPFound < PContactRate:
                        rperson = random.randint(0,self.npersons-1) 
                        numPFound += 1                           
                        if rperson < self.DefinedAgents:
                            HHID = random.choice(list(self.hhset.keys())) # should these be weighted by size?
                            personId = self.hhset[HHID].getRandomAgent()        
                            HHIDSToQ.append(HHID)
                            PersonIdsToQ.append(personId)
                    
                    # now actually test contacts - if they are positive then         
                    for i in range(0,len(HHIDSToQ)):
                        HHID = HHIDSToQ[i]
                        personId = PersonIdsToQ[i]
                        localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,personId,localQevents,offPopQueueEvents,delkeys) ### adds quarantine events if positive
                        if detected and self.timeNow > self.DiseaseParameters['QuarantineStartDate'] and followQuarantine:
                            self.numQuarantined += 1
                            if self.DiseaseParameters['QuarantineType'] == 'household':       
                                PIDs = self.hhset[HHID].getPersonIDs()
                                for pp in range(0,len(PIDs)):
                                    if pp != personId:
                                        offPopQueueEvents,delkeys = self.clearForwardInfections(tend,HHID,pp,offPopQueueEvents,delkeys)
                                        self.numQuarantined += 1
                                        localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,pp,localQevents,offPopQueueEvents,delkeys) ### adds quarantine events if positive
                                
                                    
                            
                else:
                    print("error",SE)
                
                delkeys.append(key)
            else:
                self.timeNow = tend
                break
                    

        if self.timeNow > self.DiseaseParameters['TestingAvailabilityDateComm']:
            qshow = self.DiseaseParameters['CommunityTestingRate']
            numShowingUpforTesting=int(math.ceil(self.numContagious*qshow))
            # This is deprecated for now
            if self.timeNow > self.DiseaseParameters['QuarantineStartDate'] and self.DiseaseParameters['testExtra'] == 1:
                if testExtra:                            
                    numShowingUpforTesting+=int(self.npersons*qshow)
            x = []
            for i in range(0,int(max(self.DefinedAgents-1,numShowingUpforTesting))):
                x.append(i)        
            samplevals = random.sample(x,numShowingUpforTesting)
            for i in range(0,len(samplevals)):
                rperson = samplevals[i]
                # found existing person so can test them otherwise - assume test is negative
                if rperson < self.DefinedAgents:
                    HHID = random.choice(list(self.hhset.keys())) # should these be weighted by size?
                    personId = self.hhset[HHID].getRandomAgent()
                    localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,personId,localQevents,offPopQueueEvents,delkeys)
                    # If they are detected and they follow quarantine - then quarantince household
                    if detected and self.DiseaseParameters['QuarantineType'] == 'household' and self.timeNow > self.DiseaseParameters['QuarantineStartDate'] and followQuarantine:
                        PIDs = self.hhset[HHID].getPersonIDs()
                        for pp in range(0,len(PIDs)):
                            offPopQueueEvents,delkeys = self.clearForwardInfections(tend,HHID,pp,offPopQueueEvents,delkeys)
                            self.numQuarantined += 1
                            # If intervention includes tracing contacts and testing them, then test household
                            if self.DiseaseParameters['ContactTracing'] == 1:
                                localQevents,offPopQueueEvents,delkeys, detected, followQuarantine = self.testAgent(tend,HHID,pp,localQevents,offPopQueueEvents,delkeys) ### adds quarantine events if positive
                        
                        
                                                                            
        for i in range(0, len(delkeys)):
            try:
                del self.eventQueue[delkeys[i]]
            except KeyError:
                # could happen if the key is added twice due to testing
                pass

        # add the quarantine events
        for i in range(0,len(localQevents)):
            QE = localQevents[i]
            ts = QE.timestamp
            self.eventQueue[ts] = QE
        
        return offPopQueueEvents, numevents 

        
    def infectRandomAgent(self,infectionTime,ageCohort=-1,infectingAgent={}):
        #first determine if we are infecting someone already defined or creating new household
        infectperson = random.randint(0,self.npersons-1)
        if infectperson < (self.DefinedAgents+self.EphermeralAgents):
            if infectperson < self.DefinedAgents:
                HHID = random.choice(list(self.hhset.keys())) # should these be weighted by size?
            else:
                HHID = -1
                # the household is all recovered so don't care
        else:
            HHID = self.BuildSingleHousehold()

        offPopQueueEvents = self.infectAgent(infectionTime,HHID,ageCohort=ageCohort,infectingAgent=infectingAgent)
                          
        return offPopQueueEvents

    def infectAgent(self,infectionTime, HHID, agentId=-1,ageCohort=-1,infectingAgent={}):
        #print("Before infection S:",self.numSusceptible," N:",self.numIncubating," C:",self.numContagious," I:",self.numInfected," R:",self.numRecovered," H:",self.numHospitalized)
        queueEvents, acout, outcome, infAgentId = self.hhset[HHID].infectHousehouldMember(infectionTime,self.DiseaseParameters,self.LocalInteractionMatrixList,
                                                                self.RegionListGuide,self.LocalPopulationId,
                                                                self.HospitalTransitionMatrixList,self.TransProb,self.TransProbLow,
                                                                agentId,ageCohort,infectingAgent,self.ProportionLowIntReduction)
        offPopQueueEvents = []
        numinfR = 0
                
        if outcome == 'quarantined':
            self.InfectiousEventsPrevented += 1
        # if they were infected then queue events will be returned
        if queueEvents:
            self.numSusceptible -= 1
            self.numIncubating += 1 
            self.ageInfection[acout]+=1
            susnum = self.hhset[HHID].numHouseholdMembersSusceptible()
            tsvaltot = 0
            for QE in queueEvents:
                ts = QE.timestamp
                if isinstance(QE,SimEvent.NonLocalInfectionEvent):
                    numinfR += 1
                    if ts <= self.SimEndDate:
                        offPopQueueEvents.append(QE)
                else:
                    if isinstance(QE,SimEvent.HouseholdInfectionEvent):
                        if susnum > 0:
                            numinfR += 1
                            susnum -= 1
                            tsvaltot += ts - self.timeNow 
                            
                    if isinstance(QE,SimEvent.LocalInfectionEvent):
                        numinfR += 1
                        tsvaltot += ts - self.timeNow 
                    if ts <= self.SimEndDate:
                        self.eventQueue[ts] = QE
 
        if numinfR > 100:
            self.R0Calc[100]+=1
        else:
            self.R0Calc[numinfR]+=1
        
        #if numinfR > 0:
        #    print(tsvaltot/numinfR)
        
        return offPopQueueEvents

    def getInfectionEvents(self):
        return self.infectionEvents
        
    def addEventsFromOtherLocalPopulations(self, QE):
        ts = QE.timestamp
        self.eventQueue[ts] = QE
        return 
        
    def addContactTracing(self,tend,HHID,personId,localQevents,offPopQueueEvents):
        if self.timeNow > self.DiseaseParameters['QuarantineStartDate']:
            self.numQuarantined += 1    
            timeToFindContacts = random.triangular(self.DiseaseParameters['TimeToFindContactsLow'],self.DiseaseParameters['TimeToFindContactsHigh'])/24
            t = tend+.001 + timeToFindContacts
            numLocalInfections = self.hhset[HHID].getLocalInfections(personId)
            numNonLocalInfections, NonLocalRegionsInfected, NonLocalPopsInfected = self.hhset[HHID].getNonLocalInfections(personId)
            localQevents.append(SimEvent.LocalContactTraceEvent(t,self.RegionId,self.LocalPopulationId, HHID,personId,numLocalInfections))
            if numNonLocalInfections > 0:
                for nlp in range(0,len(NonLocalRegionsInfected)):   
                    offPopQueueEvents.append(SimEvent.NonLocalContactTraceEvent(tend+.001, NonLocalRegionsInfected[nlp],NonLocalPopsInfected[nlp], HHID, personId,numNonLocalInfections ))
                
        return localQevents,offPopQueueEvents,

    # Function to test agents
    # If the agent is detected then adds contact tracing (if started) and if they follow quarantine then clears off potential infections                
    def testAgent(self,tend,HHID,personId,localQevents,offPopQueueEvents,delkeys,clearInfections=True):
        detected = False
        followQuarantine = False
        self.numTests += 1
        if self.hhset[HHID].getHouseholdPersonStatus(personId) == ParameterSet.Contagious:
            # did the test detect positive
            if random.random() < ParameterSet.TestEfficacy:
                self.confirmedcases += 1
                detected = True
                if random.random() < self.DiseaseParameters['PerFollowQuarantine'] and clearInfections == True:
                    followQuarantine = True
                    offPopQueueEvents,delkeys = self.clearForwardInfections(tend,HHID,personId,offPopQueueEvents,delkeys)        
                if self.timeNow > self.DiseaseParameters['QuarantineStartDate']:
                    if self.DiseaseParameters['ContactTracing'] == 1:
                        localQevents,offPopQueueEvents = self.addContactTracing(tend,HHID,personId,localQevents,offPopQueueEvents)
        return localQevents,offPopQueueEvents,delkeys, detected, followQuarantine
    
    # function to clear future infections
    # gets the future infection events to be cleared    
    def clearForwardInfections(self,tend,HHID,personId,offPopQueueEvents,delkeys):
        self.hhset[HHID].setPersonQuarantine(personId,self.timeNow,self.timeNow+ParameterSet.QuarantineTime)
        numLocalInfections = self.hhset[HHID].getLocalInfections(personId)
        numNonLocalInfections, NonLocalRegionsInfected, NonLocalPopsInfected = self.hhset[HHID].getNonLocalInfections(personId)
        if numLocalInfections > 0:
            dk = self.getEventsToBeCleared(tend,HHID,personId,numLocalInfections)
            delkeys.extend(dk)    
            self.InfectiousEventsCleared += len(dk)
        if numNonLocalInfections > 0:
            for nlp in range(0,len(NonLocalRegionsInfected)):   
                offPopQueueEvents.append(SimEvent.ClearInfectionEvents(tend+.001, NonLocalRegionsInfected[nlp],NonLocalPopsInfected[nlp], HHID, personId,numNonLocalInfections,self.RegionId,self.LocalPopulationId ))   
                #print( tend+.001, NonLocalRegionsInfected[nlp],NonLocalPopsInfected[nlp], HHID, personId,numNonLocalInfections,self.RegionId,self.LocalPopulationId)
        return offPopQueueEvents,delkeys
            
    # function to search queue for infection events (only clears them with some probability)
    def getEventsToBeCleared(self,tend,HHID,personId,numLocalInfections):
        foundthem = 0
        dekeys = []
        for key2 in self.eventQueue.keys():
            SE2 = self.eventQueue[key2]
            if isinstance(SE2,SimEvent.LocalInfectionEvent):
                ts2 = SE2.timestamp
                if ts2 > tend:
                    if SE2.IsInfectionBy(HHID,personId):
                        foundthem+=1
                        if random.random() < ParameterSet.ProbTransmissionCleared:
                            dekeys.append(key2)
            if foundthem == numLocalInfections:
                break
                    
        return dekeys

                
    def clearInfectionEvents(self,QE):
        delkeys = []

        for key in self.eventQueue.keys():
            SE = self.eventQueue[key]
            if isinstance(SE,SimEvent.NonLocalInfectionEvent):
                if SE.IsNonLocalInfectionBy(QE.infectingRegionId,QE.infectingLocalPopulationId,QE.infectingAgentHHID,QE.infectingAgentId):
                    delkeys.append(key)
                    break
        
        for i in range(0, len(delkeys)):
            del self.eventQueue[delkeys[i]]
        self.InfectiousEventsCleared += len(delkeys)
        
    def initializeHistory(self,LPHistory):
        if self.LocalIdentification == '21208':
            #print(LPHistory)
            for reportdate in LPHistory.keys():
                if reportdate != 'currentHospitalData':
                    print(LPHistory[reportdate]['timeval'],LPHistory[reportdate]['ReportedNewCases'],LPHistory[reportdate]['EstimatedMildCases'])
        confirmedcases = 0
        offPopQueueEvents = []
        numpriorcases = 0
        numnewcases = 0
        for reportdate in LPHistory.keys():
            numinfected = int(LPHistory[reportdate]['ReportedNewCases'])+int(float(LPHistory[reportdate]['EstimatedMildCases'])*1.5)
            if LPHistory[reportdate]['live'] == 0:            
                numpriorcases += numinfected
                confirmedcases += int(LPHistory[reportdate]['ReportedNewCases'])
                while numinfected > 0:
                    HHID = -1
                    while HHID < 0:
                        person = random.randint(0,self.npersons-1)
                        if person < (self.DefinedAgents+self.EphermeralAgents):
                            if person < self.DefinedAgents:
                                HHID = random.choice(list(self.hhset.keys())) # should these be weighted by size?
                        else:
                            HHID = self.BuildSingleHousehold()
                        pid = self.hhset[HHID].getRandomAgent()
                        if self.hhset[HHID].getHouseholdPersonStatus(pid) != ParameterSet.Susceptible:
                            HHID=-1
                    
                    
                    if random.random() < .005:
                        self.hhset[HHID].setHouseholdPersonStatus(pid,ParameterSet.Dead)
                        self.numDead += 1
                    else:
                        self.hhset[HHID].setHouseholdPersonStatus(pid,ParameterSet.Recovered)
                        self.numRecovered += 1
                    
                    self.numSusceptible -= 1
                    numinfected -= 1
            else:
                numnewcases += numinfected
                op = self.setCurrentCases(numinfected,LPHistory[reportdate]['timeval'])
                offPopQueueEvents.extend(op)       
            
        self.confirmedcases += confirmedcases
        return numpriorcases,numnewcases,offPopQueueEvents
        
    def setCurrentCases(self,CurrentCases,timeval):
        try:
            offPopQueueEvents = []
            for i in range(0,CurrentCases):
                op = self.infectRandomAgent(timeval)
                offPopQueueEvents.extend(op)    
                
            return offPopQueueEvents
            
        except Exception as e:
            print("InitializeHistoryError")
            print(traceback.format_exc())
    
    def resetParameters(self,PopulationParameters,DiseaseParameters,SimEndDate,ProportionLowIntReduction,TransProb,TransProbLow):
                                
        self.PopulationParameters = copy.deepcopy(PopulationParameters)
        self.DiseaseParameters = copy.deepcopy(DiseaseParameters)
        self.TransProb = copy.deepcopy(TransProb)
        self.TransProbLow = copy.deepcopy(TransProbLow)
        self.SimEndDate = SimEndDate
        
        
                                