from random import gammavariate, random
import Utils
import ParameterSet

class SimulationEvent:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        
    def getEventTime(self):
        return self.timestamp

class InfectionEvent(SimulationEvent):
    def __init__(self, timestamp, ageCohort, infectingAgentHHID,infectingAgentId):
        super().__init__(timestamp)
        self.ageCohort = ageCohort
        self.infectingAgentId = infectingAgentId
        self.infectingAgentHHID = infectingAgentHHID
        
    def getAgeCohort(self):
        return self.ageCohort
        
     
class NonLocalInfectionEvent(InfectionEvent):
    def __init__(self, timestamp, RegionId, LocalPopulationId, ageCohort, infectingAgentHHID,infectingAgentId):
        super().__init__(timestamp, ageCohort, infectingAgentHHID,infectingAgentId)
        self.RegionId = RegionId
        self.LocalPopulationId = LocalPopulationId
        
    def getRegionId(self):
        return self.RegionId
        
    def getLocalPopulationId(self):
        return self.LocalPopulationId        

class LocalInfectionEvent(InfectionEvent):
    pass
        
class HouseholdEvent(SimulationEvent):
    def __init__(self, timestamp, HouseholdId, PersonId):
        super().__init__(timestamp)
        self.HouseholdId = HouseholdId
        self.PersonId = PersonId
        
    def getHouseholdId(self):
        return self.HouseholdId
        
    def getPersonId(self):
        return self.PersonId

class PersonHospEvent(HouseholdEvent):
    def __init__(self, timestamp, HouseholdId, PersonId, Hospital):
        super().__init__(timestamp, HouseholdId, PersonId)
        self.Hospital = Hospital
    
    def getHospital(self):
        return self.Hospital   
        
class PersonHospCritEvent(PersonHospEvent):
    pass
    
class PersonHospICUEvent(PersonHospEvent):
    pass

class PersonHospExitICUEvent(PersonHospEvent):
    pass
    
class PersonHospEDEvent(PersonHospEvent):
    pass
    
class HouseholdInfectionEvent(HouseholdEvent):
    pass

# Change in status event
class PersonStatusUpdate(HouseholdEvent):
    def __init__(self, timestamp, HouseholdId, PersonId, Status):
        super().__init__(timestamp, HouseholdId, PersonId)
        self.Status = Status
    
    def getStatus(self):
        return self.Status

    
