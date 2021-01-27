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

from random import gammavariate, random
import Utils
import ParameterSet
import disease.Virus

class SimulationEvent:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        


class InfectionEvent(SimulationEvent):
    def __init__(self, timestamp, virus, ageCohort, infectingAgentHHID,infectingAgentId):
        super().__init__(timestamp)
        self.ageCohort = ageCohort
        self.infectingAgentId = infectingAgentId
        self.infectingAgentHHID = infectingAgentHHID
        self.virus = virus

    def IsInfectionBy(self,infectingAgentHHID,infectingAgentId):
        if self.infectingAgentHHID == infectingAgentHHID and self.infectingAgentId == infectingAgentId:
            return True
        else:
            return False
    
class NonLocalInfectionEvent(InfectionEvent):
    def __init__(self, timestamp, virus, RegionId, LocalPopulationId, ageCohort, infectingAgentHHID,infectingAgentId, infectingAgentRegionId, infectingAgentLocalPopulationId):
        super().__init__(timestamp,virus, ageCohort, infectingAgentHHID,infectingAgentId)
        self.RegionId = RegionId
        self.LocalPopulationId = LocalPopulationId
        self.InfectingAgentRegionId = infectingAgentRegionId
        self.InfectingAgentLocalPopulationId = infectingAgentLocalPopulationId
        
    def getLocalPopulationId(self):
        return self.LocalPopulationId       
        
    def IsNonLocalInfectionBy(self,InfectingAgentRegionId,InfectingAgentLocalPopulationId,infectingAgentHHID,infectingAgentId):        
        if self.InfectingAgentRegionId == InfectingAgentRegionId and self.InfectingAgentLocalPopulationId == InfectingAgentLocalPopulationId:
            return super().IsInfectionBy(infectingAgentHHID,infectingAgentId)        
        else:
            return False
 

class LocalInfectionEvent(InfectionEvent):
    pass
        
class HouseholdEvent(SimulationEvent):
    def __init__(self, timestamp, HouseholdId, PersonId):
        super().__init__(timestamp)
        self.HouseholdId = HouseholdId
        self.PersonId = PersonId

class PersonHospEvent(HouseholdEvent):
    def __init__(self, timestamp, HouseholdId, PersonId, Hospital):
        super().__init__(timestamp, HouseholdId, PersonId)
        self.Hospital = Hospital
    
        
class PersonHospCritEvent(PersonHospEvent):
    pass
    
class PersonHospICUEvent(PersonHospEvent):
    pass

class PersonHospExitICUEvent(PersonHospEvent):
    pass
    
class PersonHospEDEvent(PersonHospEvent):
    pass
    
class PersonHospTestEvent(PersonHospEvent):
    pass
        
class HouseholdInfectionEvent(HouseholdEvent):
    def __init__(self, timestamp, virus, HouseholdId, PersonId):
        super().__init__(timestamp, HouseholdId, PersonId)
        self.virus = virus

# Change in status event
class PersonStatusUpdate(HouseholdEvent):
    def __init__(self, timestamp, HouseholdId, PersonId, Status):
        super().__init__(timestamp, HouseholdId, PersonId)
        self.Status = Status
    
class ContactTraceEvent(SimulationEvent):
    def __init__(self, timestamp, RegionId, LocalPopulationId, infectingAgentHHID,infectingAgentId, NumPeopleToLookFor):
        super().__init__(timestamp)
        self.infectingAgentId = infectingAgentId
        self.infectingAgentHHID = infectingAgentHHID
        self.NumPeopleToLookFor = NumPeopleToLookFor
        self.RegionId = RegionId
        self.LocalPopulationId = LocalPopulationId
        
class NonLocalContactTraceEvent(ContactTraceEvent):
    pass
        
class LocalContactTraceEvent(ContactTraceEvent):
    pass
       
    
class ClearInfectionEvents(SimulationEvent):
    def __init__(self, timestamp, RegionId, LocalPopulationId, infectingAgentHHID,infectingAgentId, numInfectionsToClear, infectingRegionId, infectingLocalPopulationId):
        super().__init__(timestamp)
        self.RegionId = RegionId
        self.LocalPopulationId = LocalPopulationId
        self.infectingAgentId = infectingAgentId
        self.infectingAgentHHID = infectingAgentHHID
        self.numInfectionsToClear = numInfectionsToClear
        self.infectingRegionId = infectingRegionId
        self.infectingLocalPopulationId = infectingLocalPopulationId
        