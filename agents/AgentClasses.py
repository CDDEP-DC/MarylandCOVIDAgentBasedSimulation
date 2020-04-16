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
    def __init__(self, HouseholdID, HHSize, HHSizeAgeDist,PopulationDensity,PopulationParameters,DiseaseParameters):
        """
        Initialize household class representing a single family/household in
        a location and stores household-specific information

        """

        self.HouseholdID = HouseholdID
        self.persons = {}

        self.PopulationParameters = PopulationParameters
        
        for x in range(0, HHSize+1):
            ageCohort = Utils.multinomial(HHSizeAgeDist[HHSize+1],
                                          sum(HHSizeAgeDist[HHSize+1]))
            
    
            pdscale = 1/(1+ .25*math.exp(-.001*PopulationDensity))
            numRandomContacts = math.floor(random.gammavariate(
                    PopulationParameters['AGGammaShape'][ageCohort],PopulationParameters['AGGammaScale'][ageCohort])+1)
            numHouseholdContacts = PopulationParameters['householdcontactRate']
            person = Person(DiseaseParameters,x, HouseholdID, ageCohort, 0,
                                                numHouseholdContacts,
                                                numRandomContacts)
            self.persons[x] = person

    def areAllHouseholdMembersInfected(self):   
        for personkey in self.persons:
            if self.persons[personkey].getStatus() == 0:
                return False
                
        return True
        
        
    def numHouseholdMembersSusceptible(self):   
        susnum = 0
        for personkey in self.persons:
            if self.persons[personkey].getStatus() == 0:
                susnum += 1        
        return susnum
        
    def deleteHousehold(self):   
        # recovered is -1, so if everyone is less than 0 we don't care about house anymore and can "delete"
        for personkey in self.persons:
            if self.persons[personkey].getStatus() >= 0:
                return False
        return True    
        
    def getHouseholdSize(self):
        return len(self.persons.keys())
        
    def getHouseholdId(self):
        return self.HouseholdID
                
    def reset(self):
        for key in self.persons.keys():
            self.persons[key].reset()
        
    def infectHousehouldMember(self, timeNow, LocalInteractionMatrixList,
                    RegionListGuide, LocalPopulationId,HospitalTransitionMatrixList,
                               currentAgentId=-1, ageCohort=-1):
        #print("currentAgentId=",currentAgentId)
        #print("ageCohort=",ageCohort)
        if len(self.persons.keys()) > 0:
            if len(self.persons.keys()) == 1:
                p = list(self.persons.keys())[0]
            else:
                # if we are infecting in our household (so pass in agent) then choose someone else in household
                if currentAgentId >= 0:
                    #make sure it doesn't get stuck here
                    numtries = 0
                    p = random.choice(list(self.persons.keys()))
                    while p == currentAgentId:
                        p = random.choice(list(self.persons.keys()))
                        numtries+=1
                        if numtries > 100:
                            print("LOOP ERROR")
                            break
                else:
                    if ageCohort >= 0:
                        vals = []
                        for key in self.persons.keys():
                            vals.append(self.PopulationParameters['AgeCohortInteraction'][ageCohort][self.persons[key].getAgeCohort()])
                        p = Utils.Multinomial(vals)
                    else:
                        p = random.choice(list(self.persons.keys()))     
                    
            queueEvents = self.persons[p].infect(timeNow, LocalInteractionMatrixList,
                                                 RegionListGuide, LocalPopulationId,self.areAllHouseholdMembersInfected(),
                                                 HospitalTransitionMatrixList,len(self.persons))
        return queueEvents

    
    def getHouseholdStats(self):
        hhstats = [] #change to dict to get statuses
        for personkey in self.persons.keys():
            hhstats.append(self.getHouseholdPersonStatus(personkey))
        return self.HouseholdID, hhstats
        
    def getHouseholdPersonStatus(self,personId):
        return(self.persons[personId].getStatus())
        
    def setHouseholdPersonStatus(self,personId,status):
        self.persons[personId].setStatus(status)
        
    def getHouseholdPersonHospStatus(self,personId):
        return(self.persons[personId].getHospStatus())
        
    def setHouseholdPersonHospStatus(self,personId,status,HospitalId=-1):
        self.persons[personId].setHospStatus(status,HospitalId) 
        return self.getPersonHospital(personId)
        
    def getPersonHospital(self,personId):
        return self.persons[personId].getHospital()

    def getPersonAgeCohort(self,personId):
        return self.persons[personId].getAgeCohort()
        
class Person:
    def __init__(self,DiseaseParameters,personID, householdId, ageCohort, status, householdContactRate = 1,
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
        self.householdId = householdId
        self.hospitalized = 0
        self.hospital = -1
        self.DiseaseParameters = DiseaseParameters
        

    def reset(self):
        self.status = ParameterSet.Susceptible
        self.symptom = 0
        self.hospitalized = 0
        
    def infect(self, timeNow, LocalInteractionMatrixList, RegionListGuide, LocalPopulationId,areAllHouseholdMembersInfected,HospitalTransitionMatrixList,HHSize):
        queueEvents = []
        if self.status == ParameterSet.Susceptible:
            self.status = ParameterSet.Incubating
            queueEvents = disease.DiseaseProgression.\
                SetupTransmissableContactEvents(timeNow,self.DiseaseParameters, LocalInteractionMatrixList,
                                                RegionListGuide,
                                                self.householdId,
                                                self.personID,
                                                LocalPopulationId,
                                                self.randomContactRate,
                                                self.householdContactRate,
                                                self.ageCohort,
                                                areAllHouseholdMembersInfected,
                                                HospitalTransitionMatrixList,HHSize)
        return queueEvents, self.ageCohort

    def getStatus(self):
        return self.status
        
    def setStatus(self,status):
        self.status = status

    def getHospStatus(self):
        return(self.hospitalized)
        
    def setHospStatus(self,status,Hospital):
        self.hospitalized = status
        self.hospital = Hospital
        
    def getHospital(self):
        return(self.hospital)
        
    def getAgeCohort(self):
        return(self.ageCohort)