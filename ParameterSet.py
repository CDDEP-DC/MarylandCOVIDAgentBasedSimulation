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
import numpy as np

ModelRunning = ''
WuhanMktLocalPopId = -1
WuhanMktRegionId = -1


## debuggingmode
logginglevel = 'error'

## QueueProcessing
UseQueuesForQueues = False
FitModel = False
FitModelRuns = 5000
FitValue = 'hospitalizations'
FitMD = False #for just fitting maryland in MDDCVAregion model ... 
SaveHospitalData = True
LoadHistory = False
UseSavedRegion = False
SavedRegionContainer = ''

OperationsFolder = 'Operations'
PopDataFolder = 'pops'
QueueFolder = 'Queues'
ResultsFolder = 'results'
OutputFolder = 'Output'
SavedRegionFolder = 'SavedRegions'
PERIOD_OF_TIME = 36000 # 10 hours

MAXIntVal = 9999999999999

testR0 = []

Intervention = ''
InterventionDate = -1
InterventionEndDate = -1
InterventionReduction = 1
InterventionReduction2 = 1
InterventionReductionSchool = 1
InterventionMobilityEffect = .5
SeasonalityStart = 60
SeasonalityReduction = .98
SeasonalityReduction2 = .95
StartDateHistory = -31
OldAgeRestriction = False
OldAgeReduction = 0
GatheringRestriction = False
GatheringMax = 10
GatheringPer = .9
                
#PersonStatus:
Susceptible = 0
Incubating = 1
Contagious = 2
Symptomatic = 3
Recovered = -1
Dead = -2
Vaccinated = -3

VaccinationDelay = 14

# Quarantine
QuarantineTime = 14
TestEfficacy = .7
MaxQuarantinePeople = 10
ProbTransmissionCleared = 0.5

agetestInf = []
agetestHosp = []
agetestSymp = []


#class WuhanResolution:
#    def __init__(self):
#        self.Xlength = 2
#        self.Ylength = 2

#class Parms(WuhanResolution):
#    def __init__(self):
#        HHSizeDist.__init__(self)
#        WuhanResolution.__init__(self)
        ## Reduction in contact rate from symptomatic patients (under normal circumstances)


