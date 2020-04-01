# -----------------------------------------------------------------------------
# ParameterSet.py contains the GlobalParameterSet and extracts local parameters
# for a local location and local population
# -----------------------------------------------------------------------------

import numpy as np

ModelRunning = ''
WuhanMktLocalPopId = -1
WuhanMktRegionId = -1
ImportationRate = 1
ImportationRatePower = 1

StopQueueDate = 1000

## debuggingmode
debugmodelevel = 3
debugerror = 1
debugwarning = 2
debugnotice = 3
debugnotimportant = 4
debugtimer = 5

PopDataFolder = 'pops'
QueueFolder = 'Queues'
ResultsFolder = 'results'

MAXIntVal = 9999999999999

testR0 = []

Intervention = ''
InterventionDate = -1
InterventionEndDate = -1
InterventionReduction = 1
InterventionReduction2 = 1
InterventionReductionSchool = 1
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

#DiseaseVariables:
IncubationTime = 6.1
totalContagiousTime = 9
symptomaticTime = 6
hospitalSymptomaticTime = 12
hospTime = 4
EDVisit = .8
preContagiousTime = 2
postContagiousTime = 6
ICURate = .6
ICUtime = 12
PostICUTime = 5


#ProbabilityOfTransmissionPerContact = .015 ## 0.015 --> 1.3-1.6
ProbabilityOfTransmissionPerContact = 0.001 #.02 ## 0.01 --> 2

symptomaticContactRateReduction = .05
householdcontactRate = 47

#HHSizeDist:
#Default US values 
HHSizeDist = [28.37, 34.51, 15.07, 12.76, 5.78, 2.26, 1.25]
HHSizeAgeDist = {}
HHSizeAgeDist[1] = [0, 0, 15.2350336473755, 8.40026917900404,4.73469717362046]
HHSizeAgeDist[2] = [0, 0, 18.5322880215343, 10.2183041722746,5.75940780619112]
HHSizeAgeDist[3] = [1.02476, 2.84823, 6.01293, 3.3154, 1.86868]
HHSizeAgeDist[4] = [0.86768, 2.41164, 5.09124, 2.8072, 1.58224]
HHSizeAgeDist[5] = [0.39304, 1.09242, 2.30622, 1.2716, 0.71672]
HHSizeAgeDist[6] = [0.15368, 0.42714, 0.90174, 0.4972, 0.28024]
HHSizeAgeDist[7] = [0.085, 0.23625, 0.49875, 0.275, 0.155]

#ContactRates:
## For creating contact rates
GammaScale = 5
#agecohort 0 -- 0-4
AG04GammaShape = 2.1
AG04AsymptomaticRate = .99
AG04HospRate = 0.0125
AG04MortalityRate = 0
        
#agecohort 1 -- 5-17
AG517GammaShape = 3
AG517AsymptomaticRate = .97
AG517HospRate = 0.009
AG517MortalityRate = 0.0018

#agecohort 2 -- 18-49
AG1849GammaShape = 2.5
AG1849AsymptomaticRate = .81
AG1849HospRate = 0.008
AG1849MortalityRate = 0.0032

#agecohort 3 -- 50-64
AG5064GammaShape = 2.3
AG5064AsymptomaticRate = .84
AG5064HospRate = 0.03
AG5064MortalityRate = 0.0207
        
#agecohort 4 -- 65+
AG65GammaShape = 2.1
AG65AsymptomaticRate = .4
AG65HospRate = 0.14
AG65MortalityRate = 0.08
        
AGGammaShape = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG1849GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
AGHospRate = [AG04HospRate,AG517HospRate,AG1849HospRate,AG1849HospRate,AG1849HospRate,AG5064HospRate,AG65HospRate]
AGMortalityRate = [AG04MortalityRate,AG517MortalityRate,AG1849MortalityRate,AG1849MortalityRate,AG1849MortalityRate,AG5064MortalityRate,AG65MortalityRate]
AGAsymptomaticRate = [AG04AsymptomaticRate, AG517AsymptomaticRate, AG1849AsymptomaticRate,AG1849AsymptomaticRate,AG1849AsymptomaticRate, AG5064AsymptomaticRate,AG65AsymptomaticRate]
AgeCohortInteraction = {0:{0:1.39277777777778,	1:0.328888888888889,	2:0.299444444444444,	3:0.224444444444444,	4:0.108333333333333},
                                    1:{0:0.396666666666667,	1:2.75555555555556,	2:0.342407407407407,	3:0.113333333333333,	4:0.138333333333333},
                                    2:{0:0.503333333333333,	1:1.22666666666667,	2:1.035,	3:0.305185185185185,	4:0.180555555555556},
                                    3:{0:0.268888888888889,	1:0.164074074074074, 2:0.219444444444444,	3:0.787777777777778,	4:0.27},
                                    4:{0:0.181666666666667,	1:0.138888888888889, 2:0.157222222222222,	3:0.271666666666667,	4:0.703333333333333}}

class WuhanResolution:
    def __init__(self):
        self.Xlength = 2
        self.Ylength = 2

class Parms(WuhanResolution):
    def __init__(self):
        HHSizeDist.__init__(self)
        WuhanResolution.__init__(self)
        ## Reduction in contact rate from symptomatic patients (under normal circumstances)


