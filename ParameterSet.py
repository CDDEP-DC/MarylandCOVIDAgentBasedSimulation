# -----------------------------------------------------------------------------
# ParameterSet.py contains the GlobalParameterSet and extracts local parameters
# for a local location and local population
# -----------------------------------------------------------------------------

import numpy as np

ModelRunning = ''
WuhanMktLocalPopId = -1
WuhanMktRegionId = -1


## debuggingmode
debugmodelevel = 3
debugerror = 1
debugwarning = 2
debugnotice = 3
debugnotimportant = 4
debugtimer = 5

OperationsFolder = 'Operations'
PopDataFolder = 'pops'
QueueFolder = 'Queues'
ResultsFolder = 'results'
OutputFolder = 'Output'

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

#PersonStatus:
Susceptible = 0
Incubating = 1
Contagious = 2
Symptomatic = 3
Recovered = -1
Dead = -2

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


