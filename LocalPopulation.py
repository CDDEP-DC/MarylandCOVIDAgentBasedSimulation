# -----------------------------------------------------------------------------
# LocalPopulation.py builds and stores the population for each local model
# -----------------------------------------------------------------------------

import random
import time
import math

from statistics import mean
import ParameterSet
import events.SimulationEvent as SimEvent
import Utils
import agents.AgentClasses

class LocalPopulation:
    def __init__(self, LocalPopulationId, npersons, HHSizeDist, HHSizeAgeDist,
                 LocalInteractionMatrixList, RegionId, RegionListGuide,HospitalTransitionMatrixList):
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
        self.timeNow = 0
        self.RegionId = RegionId
        self.HHSizeDist = HHSizeDist
        self.HHSizeAgeDist = HHSizeAgeDist
        self.UndefinedAgents = npersons
        self.DefinedAgents = 0
        self.EphermeralAgents = 0
        self.npersons = npersons #save original pop
        self.currHouseholdIDNum = 0
        
        self.numNewRandomInfections = 0
        self.numNewHHInfections = 0
        self.numAgentsInfected = 0

        # Interaction matrix with other populations
        self.LocalInteractionMatrixList = LocalInteractionMatrixList
        self.RegionListGuide = RegionListGuide
        self.HospitalTransitionMatrixList = HospitalTransitionMatrixList
        self.HospitalInfectionList = []
        self.HospitalICUInfectionList = []
        self.HospitalNewInfectionList = []
        self.HospitalNewEDList = []
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
        
        #self.infectionEvents = []

        # Event queue is a dictionary
        self.eventQueue = {}

        # Households
        self.hhset = {}

            
    def BuildSingleHousehold(self):
        
        numtries = 0
        maxval = self.npersons - self.DefinedAgents - self.EphermeralAgents
        # this is to make sure we don't make a household that pushes over the size of the population
        HHSize = maxval + 1
        
        while (HHSize+1) > maxval:
            
            HHSize = Utils.multinomial(ParameterSet.HHSizeDist, sum(ParameterSet.HHSizeDist))
            numtries += 1
            if numtries > 100:
                #print(HHSize+1," ",maxval," ",numdefinedagents, " " , infectperson)
                print("LOOP ERROR")
                break

        # Now create household
        HH = agents.AgentClasses.Household(self.currHouseholdIDNum, HHSize, ParameterSet.HHSizeAgeDist)
        self.hhset[self.currHouseholdIDNum] = HH
        self.currHouseholdIDNum += 1
        self.UndefinedAgents -= (HHSize + 1)
        self.DefinedAgents += (HHSize + 1)
        return HH.getHouseholdId()
        
    def getNumInfected(self):
        return self.numInfected

    def getLocalId(self):
        return self.LocalPopulationId

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
        stats['In'] = self.numNewRandomInfections+self.numNewHHInfections
        stats['InR'] = self.numNewRandomInfections
        stats['InH'] = self.numNewHHInfections
        stats['Ai'] = self.numAgentsInfected
        stats['HI'] = sum(self.HospitalNewInfectionList)
        stats['HE'] = sum(self.HospitalNewEDList)
        return stats

    def getHospitalOccupancy(self):
        hospstats = {}
        hospstats['occupancy'] = self.HospitalInfectionList
        hospstats['ICU'] = self.HospitalICUInfectionList
        hospstats['admissions'] = self.HospitalNewInfectionList
        hospstats['edvisits'] = self.HospitalNewEDList
        return hospstats

    def reportNumInfected(self):
        return {self.LocalPopulationId: self.numInfected}

    def runTime(self, tend):
        if ParameterSet.debugmodelevel >= ParameterSet.debugtimer:
            t1 = time.time()
        addEvents = []
        delkeys = []
        sortedKeys = sorted(self.eventQueue.keys())
        offPopQueueEvents = []
        numevents = 0
        eventTime = ParameterSet.MAXIntVal
        ## reset the daily infection lists
        for i in range(0,len(self.HospitalNewInfectionList)):
            self.HospitalNewInfectionList[i] = 0
        for i in range(0,len(self.HospitalNewEDList)):
            self.HospitalNewEDList[i] = 0
            
        for key in sortedKeys:
            SE = self.eventQueue[key]
            eventTime = SE.getEventTime()

            if eventTime < tend:
                numevents += 1
                self.timeNow = eventTime
                # now need to add getting the type of event -- case statements etc
                if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer): t3 = time.time()
                
                if isinstance(SE,SimEvent.InfectionEvent):                
                    #print("Infection")
                    op = self.infectRandomAgent(SE.getAgeCohort())
                    # add Events to non local pop queue
                    offPopQueueEvents.extend(op)    
                elif isinstance(SE,SimEvent.PersonStatusUpdate):
                    #print("status update")
                    HHID = SE.getHouseholdId()
                    personId = SE.getPersonId()
                    currentStatus = self.hhset[HHID].getHouseholdPersonStatus(personId)
                    xbefore = "Before:"+str(currentStatus)+"-->"+str(SE.getStatus())+" S:"+str(self.numSusceptible)+" N:"+str(self.numIncubating)+" C:"+str(self.numContagious)+" I:"+str(self.numInfected)+" R:"+str(self.numRecovered)+" H:"+str(self.numHospitalized)
                    checkval = self.numSusceptible+self.numIncubating+self.numContagious+self.numInfected+self.numRecovered+self.numDead
                    
                    
                    #print(currentStatus,SE.getStatus())
                    # If updating to incubating -- patient could only be susceptible
                    if SE.getStatus() == ParameterSet.Incubating:
                        self.numIncubating += 1                
                        self.numSusceptible -= 1
                    
                    # If updating to Contagious
                        # could have been incubating or been symptomatic                        
                    elif SE.getStatus() == ParameterSet.Contagious:
                        if currentStatus == ParameterSet.Incubating:
                            self.numIncubating -= 1
                        elif currentStatus == ParameterSet.Symptomatic:
                            self.numInfected -= 1
                        elif currentStatus == ParameterSet.Susceptible:
                            self.numSusceptible -= 1
                        self.numContagious += 1
                        
                    # if updating to symptomatic could only have been contagious (added incubating for possible later change)
                    elif SE.getStatus() == ParameterSet.Symptomatic:
                        if currentStatus == ParameterSet.Incubating:
                            self.numIncubating -= 1
                        elif currentStatus == ParameterSet.Contagious:    
                            self.numContagious -= 1
                        self.numInfected += 1
                        
                    # if updating to recovered could have come from symptomatic or contagious
                    elif SE.getStatus() == ParameterSet.Recovered or SE.getStatus() == ParameterSet.Dead:
                        
                        if currentStatus == ParameterSet.Symptomatic:
                            self.numInfected -= 1
                        elif currentStatus == ParameterSet.Contagious:    
                            self.numContagious -= 1
                        elif currentStatus == ParameterSet.Incubating:    
                            self.numIncubating -= 1
                        if SE.getStatus() == ParameterSet.Dead:
                            self.numDead += 1                      
                        else:
                            self.numRecovered += 1
                        # we assume if they recover/died and they were in the hospital, they leave the hospital
                        if(self.hhset[HHID].getHouseholdPersonHospStatus(personId)==1):
                            HospId = self.hhset[HHID].getPersonHospital(personId)
                            self.hhset[HHID].setHouseholdPersonHospStatus(personId,0)
                            self.numHospitalized -= 1
                            #print("Patient left " + str(HospId),self.numHospitalized,self.HospitalInfectionList)
                            self.HospitalInfectionList[HospId]-=1
                            
                            
                        # check if everyone is recovered, if so delete household
                        if self.hhset[HHID].deleteHousehold():
                            HHSize = self.hhset[HHID].getHouseholdSize()
                            #print("all infected ",HHSize)
                            self.DefinedAgents -= HHSize
                            self.EphermeralAgents += HHSize
                            del self.hhset[HHID]
                            print(npersons," = ",numnotdefinedagents," + ",numdefinedagents," + ",numrecovereddeadagents)
                    else:
                        print("Need to throw error here2 ... something went wrong")
                        
                    self.hhset[HHID].setHouseholdPersonStatus(personId,SE.getStatus())
                        
                        
                    checkval2 = self.numSusceptible+self.numIncubating+self.numContagious+self.numInfected+self.numRecovered+self.numDead
                    if checkval != checkval2:
                        print(xbefore)
                        print("After S:",self.numSusceptible," N:",self.numIncubating," C:",self.numContagious," I:",self.numInfected," R:",self.numRecovered," H:",self.numHospitalized)
                        exit()
                    
                elif isinstance(SE,SimEvent.PersonHospEvent): 
                    #print("hosp")
                    HHID = SE.getHouseholdId() 
                    personId = SE.getPersonId()
                    Hospital = SE.getHospital()
                    if isinstance(SE,SimEvent.PersonHospCritEvent) or isinstance(SE,SimEvent.PersonHospICUEvent): 
                        self.HospitalInfectionList[Hospital]+=1
                        self.HospitalICUInfectionList[Hospital]+=1
                        self.HospitalNewInfectionList[Hospital]+=1
                        self.hhset[HHID].setHouseholdPersonHospStatus(personId,1,Hospital)
                        self.numHospitalized += 1
                        self.numHospitalizedICU += 1
                    elif isinstance(SE,SimEvent.PersonHospExitICUEvent):
                        self.HospitalICUInfectionList[Hospital]-=1
                        self.numHospitalizedICU -= 1
                    else:
                        self.HospitalNewEDList[Hospital]+=1
                    #print("Patient went to " + str(Hospital)," right: ",testHHid," nuhhosp:",self.numHospitalized,self.HospitalInfectionList)
                elif isinstance(SE,SimEvent.HouseholdInfectionEvent):
                        #print("house")
                        HHID = SE.getHouseholdId()
                        agentId = SE.getPersonId()
                        op = self.infectAgent(HHID,agentId=agentId)
                else:
                    print("error",SE)
                if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer): t4 = time.time()
                if (ParameterSet.debugmodelevel >= ParameterSet.debugtimer): addEvents.append(t4 - t3)
                
                delkeys.append(key)
            else:
                self.timeNow = tend
                break

        for i in range(0, len(delkeys)):
            del self.eventQueue[delkeys[i]]

        if ParameterSet.debugmodelevel >= ParameterSet.debugtimer:
            t2 = time.time()
        if ParameterSet.debugmodelevel >= ParameterSet.debugtimer:
            if len(addEvents) > 0:
                print("LocalPopultion:runTime()>>",self.RegionId,"-",self.LocalPopulationId,"(",numevents,"):",t2-t1," - ",sum(addEvents)/len(addEvents))
        return offPopQueueEvents, numevents, eventTime

    
    def infectRandomAgent(self,ageCohort=-1):
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
           
        offPopQueueEvents = self.infectAgent(HHID,ageCohort=ageCohort)
                      
        return offPopQueueEvents

    def infectAgent(self, HHID, agentId=-1,ageCohort=-1):
        #print("Before infection S:",self.numSusceptible," N:",self.numIncubating," C:",self.numContagious," I:",self.numInfected," R:",self.numRecovered," H:",self.numHospitalized)
        queueEvents = \
            self.hhset[HHID].infectHousehouldMember(self.timeNow,
                                    self.LocalInteractionMatrixList,
                                    self.RegionListGuide,
                                    self.LocalPopulationId,self.HospitalTransitionMatrixList,
                                                  agentId,ageCohort)
        offPopQueueEvents = []
        # if they were infected then queue events will be returned
        if queueEvents:
            
            self.numSusceptible -= 1
            self.numIncubating += 1 
            self.numAgentsInfected += 1
            susnum = self.hhset[HHID].numHouseholdMembersSusceptible()
            #agentEvents = { 'agent':agentId,'household':HHID,'numInfections':0,'numHHinf':0,'numRinf':0}
            for QE in queueEvents:
                if isinstance(QE,SimEvent.NonLocalInfectionEvent):
                    self.numNewRandomInfections += 1
                    #agentEvents['numInfections'] +=1
                    #agentEvents['numRinf'] +=1
                    offPopQueueEvents.append(QE)
                else:
                    if isinstance(QE,SimEvent.HouseholdInfectionEvent):
                        numtries = 0
                        while susnum > 0:
                            self.numNewHHInfections += 1
                            susnum -= 1
                            numtries += 1
                            if numtries > 100:
                                #print(HHSize+1," ",maxval," ",numdefinedagents, " " , infectperson)
                                print("LOOP ERROR")
                                break
                        #agentEvents['numInfections'] +=1
                        #agentEvents['numHHinf'] +=1
                        
                    if isinstance(QE,SimEvent.LocalInfectionEvent):
                        self.numNewRandomInfections += 1
                        #agentEvents['numInfections'] += 1
                        #agentEvents['numRinf'] += 1
                    ts = QE.getEventTime()
                    self.eventQueue[ts] = QE
            #self.infectionEvents.append(agentEvents)
            #print(agentEvents)
            #print("InfAgents:",self.numAgentsInfected," RInf:",self.numNewRandomInfections," HInf:",self.numNewHHInfections," Inf:",self.numNewRandomInfections+self.numNewHHInfections," R0:",(self.numNewRandomInfections+self.numNewHHInfections) / self.numAgentsInfected, " HHSize:",self.hhset[HHID].getHouseholdSize())
        #print("After infection S:",self.numSusceptible," N:",self.numIncubating," C:",self.numContagious," I:",self.numInfected," R:",self.numRecovered," H:",self.numHospitalized)            
        return offPopQueueEvents

    def getInfectionEvents(self):
        return self.infectionEvents
        
    def addEventsFromOtherLocalPopulations(self, QE):
        ts = QE.getEventTime()
        self.eventQueue[ts] = QE
        return ts

    def getNextEventTime(self):
        eventTime = ParameterSet.MAXIntVal
        if len(self.eventQueue) > 0:
            sortedKeys = sorted(self.eventQueue.keys())
            SE = self.eventQueue[sortedKeys[0]]
            eventTime = SE.getEventTime()
        return eventTime
        