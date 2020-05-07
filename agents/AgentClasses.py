# -----------------------------------------------------------------------------
# AgentClasses.py stores the class objects
# -----------------------------------------------------------------------------

import random
import numpy as np
import math

import events.SimulationEvent as SimulationEvent
import ParameterSet
import Utils
import disease.DiseaseProgression


class Household:
    def __init__(self, HouseholdId, HHSize, HHSizeAgeDist,PopulationDensity,PopulationParameters,DiseaseParameters,Facility=False,FacilitySize=100):
        """
        Initialize household class representing a single family/household in
        a location and stores household-specific information

        """

        self.HouseholdId = HouseholdId
        self.persons = {}
        self.Facility = Facility
        self.FacilitySize = FacilitySize

        self.PopulationParameters = PopulationParameters
        pdscale = 1/(1+ .25*math.exp(-.001*PopulationDensity))
        
        if self.Facility:
            ageCohort = len(HHSizeAgeDist[1])-1
            for x in range(0, self.FacilitySize):
                numRandomContacts = math.floor(random.gammavariate(
                        PopulationParameters['AGGammaShape'][ageCohort],PopulationParameters['AGGammaScale'][ageCohort] * pdscale))
                numHouseholdContacts = numRandomContacts
                person = Person(DiseaseParameters,x, HouseholdId, ageCohort, ParameterSet.Susceptible,
                                                    numHouseholdContacts,
                                                    numRandomContacts)
                self.persons[x] = person
        else:
            for x in range(0, HHSize+1):
                ageCohort = Utils.multinomial(HHSizeAgeDist[HHSize+1],
                                              sum(HHSizeAgeDist[HHSize+1]))
                
        
                
                #print(PopulationDensity," --",pdscale)
                numRandomContacts = math.floor(random.gammavariate(
                        PopulationParameters['AGGammaShape'][ageCohort],PopulationParameters['AGGammaScale'][ageCohort] * pdscale))
                numHouseholdContacts = PopulationParameters['householdcontactRate']
                person = Person(DiseaseParameters,x, HouseholdId, ageCohort, ParameterSet.Susceptible,
                                                    numHouseholdContacts,
                                                    numRandomContacts)
                
                self.persons[x] = person

    def areAllHouseholdMembersInfected(self):   
        for personkey in self.persons:
            if self.persons[personkey].status == 0:
                return False
                
        return True
        
        
    def numHouseholdMembersSusceptible(self):   
        susnum = 0
        for personkey in self.persons:
            if self.persons[personkey].status == 0:
                susnum += 1        
        return susnum
        
    def deleteHousehold(self):   
        # recovered is -1, so if everyone is less than 0 we don't care about house anymore and can "delete"
        for personkey in self.persons:
            if self.persons[personkey].status >= 0:
                return False
        return True    
        
    def getHouseholdSize(self):
        return len(self.persons.keys())
                
    def reset(self):
        for key in self.persons.keys():
            self.persons[key].reset()
        
    def infectHousehouldMember(self, timeNow, tend, LocalInteractionMatrixList,
                    RegionListGuide, LocalPopulationId,HospitalTransitionMatrixList,
                               currentAgentId=-1, ageCohort=-1,infectingAgent={},ProportionLowIntReduction=0):
        
        
        if len(self.persons.keys()) > 0:
            if len(self.persons.keys()) == 1:
                p = list(self.persons.keys())[0]
            else:
            
                # if we are infecting in our household (so pass in agent) then choose someone else in household
                if currentAgentId >= 0:
                    if self.numHouseholdMembersSusceptible() > 0:
                        #make sure it doesn't get stuck here
                        numtries = 0
                        p = random.choice(list(self.persons.keys()))
                        while p == currentAgentId or self.persons[p].status != ParameterSet.Susceptible:
                            p = random.choice(list(self.persons.keys()))
                            numtries+=1
                            if numtries > 100:
                                print("LOOP ERROR")
                                break
                    else:
                        return [],0,'household all infected',-1
                else:
                    p = self.getRandomAgent(ageCohort)
                    
            outcome, queueEvents, ac = self.persons[p].infect(timeNow, tend, LocalInteractionMatrixList,
                                                 RegionListGuide, LocalPopulationId,self.numHouseholdMembersSusceptible(),
                                                 HospitalTransitionMatrixList,infectingAgent,ProportionLowIntReduction)
        return queueEvents, ac, outcome, p

    
    def getHouseholdStats(self):
        hhstats = [] #change to dict to get statuses
        for personkey in self.persons.keys():
            hhstats.append(self.getHouseholdPersonStatus(personkey))
        return self.HouseholdId, hhstats
        
    def getHouseholdPersonStatus(self,personId):
        return self.persons[personId].status
        
    def setHouseholdPersonStatus(self,personId,status):
        self.persons[personId].status = status
        
    def getHouseholdPersonHospStatus(self,personId):
        return self.persons[personId].hospitalized
        
    def setHouseholdPersonHospStatus(self,personId,status,HospitalId=-1):
        self.persons[personId].setHospStatus(status,HospitalId) 
        
    def getPersonHospital(self,personId):
        return self.persons[personId].hospital

    def getPersonAgeCohort(self,personId):
        return self.persons[personId].ageCohort
        
    def getPersonRandomContactRate(self,personId):
        return self.persons[personId].randomContactRate
        
    def getPersonIDs(self):
        return self.persons.keys()
             
    def getRandomAgent(self,ageCohort=-1):        
        if ageCohort >= 0:
            vals = []
            for key in self.persons.keys():
                vals.append(self.PopulationParameters['AgeCohortInteraction'][ageCohort][self.persons[key].ageCohort])
            p = Utils.Multinomial(vals)
        else:
            p = random.choice(list(self.persons.keys())) 
        return p
        
    def setPersonQuarantine(self,personId,timeNow,QuarantineTime):
        self.persons[personId].setQuarantineTime(timeNow,QuarantineTime)
        
    def getLocalInfections(self,personId):
        return  self.persons[personId].LocalInfections
        
    def getNonLocalInfections(self,personId):
        return self.persons[personId].getNonLocalInfections()
        
    def WasInfectedByThisPerson(self,InfAgentId,InfHHId,InfLPID,InfRegionId):
        for key in self.persons.keys():
            w = self.persons[key].WasInfectedByThisPerson(InfAgentId,InfHHId,InfLPID,InfRegionId)
            if w >= 0:
                return w
        return -1
        
class Person:
    def __init__(self,DiseaseParameters,personID, HouseholdId, ageCohort, status, householdContactRate = 1,
                    randomContactRate=1):
        """
        Initialize person class represent persons in the model block and stores
        person-specific information

        """

        self.personID = personID
        self.ageCohort = ageCohort
        self.status = status
        self.symptom = 0
        self.randomContactRate = randomContactRate
        self.householdContactRate = householdContactRate
        self.HouseholdId = HouseholdId
        self.hospitalized = 0
        self.hospital = -1
        self.DiseaseParameters = DiseaseParameters
        self.QuarantineStart = -1
        self.QuarantineEnd = -1
        self.LocalInfections = 0
        self.NonLocalInfections = 0
        self.NonLocalRegionsInfected = []
        self.NonLocalPopsInfected = []
        self.infectingAgentHHID = -1
        self.infectingAgentId = -1
        self.infectingAgentHHID = -1
        self.infectingAgentId = -1
        self.infectingAgentLPID = -1
        self.infectingAgentRegionId = -1

    def setQuarantineTime(self,timeNow,QuarantineTime):
        if self.QuarantineStart < timeNow:
            self.QuarantineStart = timeNow
            self.QuarantineEnd = timeNow + QuarantineTime
        
    def infect(self, timeNow, tend, LocalInteractionMatrixList, RegionListGuide, LocalPopulationId,numHouseholdMembersSusceptible,HospitalTransitionMatrixList,infectingAgent,ProportionLowIntReduction):
        queueEvents = []
        infectNow = True
        outcome = ''
        
        if self.status != ParameterSet.Susceptible:
            infectNow = False
            outcome = 'not susceptible'
        if self.QuarantineStart > 0:
            if timeNow >= self.QuarantineStart and timeNow <= self.QuarantineEnd:
                infectNow = False
                outcome = 'quarantined'
                 
        if infectNow:
            if 'HHID' in infectingAgent.keys():
                self.infectingAgentHHID = infectingAgent['HHID']
                self.infectingAgentId = infectingAgent['personId']
                self.infectingAgentLPID = infectingAgent['LPID']
                self.infectingAgentRegionId = infectingAgent['RegionId']
            outcome = 'infection'
            self.status = ParameterSet.Incubating
            queueEvents, InfectionsDict = disease.DiseaseProgression.\
                SetupTransmissableContactEvents(timeNow,tend,self.DiseaseParameters, LocalInteractionMatrixList,
                                                RegionListGuide,
                                                self.HouseholdId,
                                                self.personID,
                                                LocalPopulationId,
                                                self.randomContactRate,
                                                self.householdContactRate,
                                                self.ageCohort,
                                                numHouseholdMembersSusceptible,
                                                HospitalTransitionMatrixList,
                                                ProportionLowIntReduction)
                         
                                                
        
        
        
            self.LocalInfections = InfectionsDict['LocalInfections']
            self.NonLocalInfections = InfectionsDict['NonLocalInfections']
            self.NonLocalRegionsInfected.extend(InfectionsDict['NonLocalRegionsInfected'])
            self.NonLocalPopsInfected.extend(InfectionsDict['NonLocalPopsInfected'])
            
            
        return outcome, queueEvents, self.ageCohort
        
    def setHospStatus(self,status,Hospital):
        self.hospitalized = status
        self.hospital = Hospital
        
    def getNonLocalInfections(self):
        return self.NonLocalInfections, self.NonLocalRegionsInfected, self.NonLocalPopsInfected
        
    def WasInfectedByThisPerson(self,InfAgentId,InfHHId,InfLPID,InfRegionId):
        if self.infectingAgentHHID == InfHHId and \
                self.infectingAgentId == InfAgentId and \
                self.infectingAgentLPID == InfLPID and \
                self.infectingAgentRegionId == InfRegionId:
            return self.personID
        else:
            return -1