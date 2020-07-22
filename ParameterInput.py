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


import pandas as pd
from datetime import datetime  
from datetime import timedelta 
import random
import traceback
import os
import csv


import ParameterSet
import Utils

def setInfectionProb(interventions,intname,DiseaseParameters,Model,fitdates=[],historyData={}):

    DiseaseParameters['TransProb'] = []
    DiseaseParameters['TransProbLow'] = []
    DiseaseParameters['TransProbSchool'] = []
    DiseaseParameters['InterventionMobilityEffect'] = []
    DiseaseParameters['InterventionStartReductionDateCalcDays'] = int(interventions[intname]['InterventionStartReductionDateCalcDays'])
    DiseaseParameters['InterventionStartReductionDate'] = int(interventions[intname]['InterventionStartReductionDate'])
    DiseaseParameters['InterventionStartEndLift'] = int(interventions[intname]['InterventionStartEndLift'])
    DiseaseParameters['InterventionStartEndLiftCalcDays'] = int(interventions[intname]['InterventionStartEndLiftCalcDays'])
    DiseaseParameters['finaldate'] = int(interventions[intname]['finaldate'])
    DiseaseParameters['InterventionEndPerIncrease'] = interventions[intname]['InterventionEndPerIncrease']

    startingprobdate = 0
    if len(historyData) > 0:
        startingprobdate = ParameterSet.ProbStartDateHistory
        
    if 'Seasonality' in interventions[intname]:
        DiseaseParameters['Seasonality'] = interventions[intname]['Seasonality']
    else:
        DiseaseParameters['Seasonality'] = 0    
    
    # get values of intervention amounts
    interventions[intname]['SchoolInterventionDate'] = interventions[intname]['SchoolCloseDate']
    intred = random.random()*(float(interventions[intname]['InterventionReductionPerMax'])-float(interventions[intname]['InterventionReductionPerMin']))+float(interventions[intname]['InterventionReductionPerMin'])
    intredLow = random.random()*(float(interventions[intname]['InterventionReductionPerLowMax'])-float(interventions[intname]['InterventionReductionPerLowMin']))+float(interventions[intname]['InterventionReductionPerLowMin'])
    mobeffect = float(interventions[intname]['InterventionMobilityEffect'])
    
    
    # set amount for beginning phase reduction in social distancing
    intdays = int(interventions[intname]['InterventionStartReductionDateCalcDays'])-int(interventions[intname]['InterventionStartReductionDate'])
    intredred = (1-intred)/intdays
    intredLowred = (1-intredLow)/intdays
    intredval = 1 - intredred
    intredvalLow = 1 - intredLowred
    mobeffectred = (1-mobeffect)/intdays
    mobeffectval = 1 - mobeffectred
    
    
    for i in range(0,interventions[intname]['InterventionStartReductionDate']):
        if i >= startingprobdate:
            DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact'])
            DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact'])
            DiseaseParameters['InterventionMobilityEffect'].append(1)    

    for i in range(0,interventions[intname]['SchoolCloseDate']):
        if i >= startingprobdate:
            DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact'])
    
    if interventions[intname]['SchoolCloseDate'] < interventions[intname]['InterventionStartReductionDate']:
        for i in range(interventions[intname]['SchoolCloseDate'],interventions[intname]['InterventionStartReductionDate']):
            if i >= startingprobdate:
                DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolCloseReductionPer']))
    
    for i in range(int(interventions[intname]['InterventionStartReductionDate']),int(interventions[intname]['InterventionStartReductionDateCalcDays'])):
        if i >= startingprobdate:
            DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)    
            DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredvalLow)
            if i >= interventions[intname]['SchoolCloseDate']:
                if intredval < float(interventions[intname]['SchoolCloseReductionPer']):
                    DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)
                else:
                    DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolCloseReductionPer']))
            DiseaseParameters['InterventionMobilityEffect'].append(mobeffectval)
        intredval -= intredred
        intredvalLow -= intredLowred
        mobeffectval -= mobeffectred

    
    # constant lower level till end of intervention    
    for i in range(int(interventions[intname]['InterventionStartReductionDateCalcDays']),int(interventions[intname]['InterventionStartEndLift'])):
        if i >= startingprobdate:
            DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)    
            DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredvalLow)
            if intredval < float(interventions[intname]['SchoolCloseReductionPer']):
                DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)
            else:
                DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolCloseReductionPer']))
            DiseaseParameters['InterventionMobilityEffect'].append(mobeffectval)
    
    opendays = int(interventions[intname]['InterventionStartEndLiftCalcDays']) - int(interventions[intname]['InterventionStartEndLift'])
    openinc = ((1-intred)*float(interventions[intname]['InterventionEndPerIncrease']))/opendays
    openincLow = ((1-intredLow)*float(interventions[intname]['InterventionEndPerIncrease']))/opendays
    mobinc = ((1-mobeffect)*float(interventions[intname]['InterventionEndPerIncrease']))/opendays
    
    for i in range(int(interventions[intname]['InterventionStartEndLift']),int(interventions[intname]['InterventionStartEndLiftCalcDays'])):
        if i >= startingprobdate:
            DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)    
            DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredvalLow)
            if i < (interventions[intname]['SchoolOpenDate']):
                if intredval < float(interventions[intname]['SchoolCloseReductionPer']):
                    DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)
                else:
                    DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolCloseReductionPer']))
            else:
                DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolOpenReductionAmt']))
            DiseaseParameters['InterventionMobilityEffect'].append(mobeffectval)
        intredval+=openinc
        intredvalLow+=openincLow
        mobeffectval += mobinc

    opendays = (int(interventions[intname]['finaldate']) - int(interventions[intname]['InterventionStartEndLiftCalcDays']))
    openinc = (1-intredval)/opendays
    openincLow = (1-intredvalLow)/opendays    
    mobinc = (1-mobeffectval)/opendays
    
    
    for i in range(int(interventions[intname]['InterventionStartEndLiftCalcDays']),int(interventions[intname]['finaldate'])):
        if i >= startingprobdate:
            DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredval)    
            DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*intredvalLow)
            if i < (interventions[intname]['SchoolOpenDate']):
                DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolCloseReductionPer']))
            else:
                DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*float(interventions[intname]['SchoolOpenReductionAmt']))        
            DiseaseParameters['InterventionMobilityEffect'].append(mobeffectval)
        intredval+=openinc/10
        intredvalLow+=openincLow/10
        mobeffectval += mobinc/10
        
        
    DiseaseParameters['InterventionDate'] = interventions[intname]['InterventionStartReductionDate']
    
    DiseaseParameters['InterventionReductionPer'] = intred
    DiseaseParameters['InterventionReductionPerLow'] = intredLow
    
    DiseaseParameters['QuarantineType'] = interventions[intname]['QuarantineType']
    if interventions[intname]['QuarantineStartDate'] == '':
        DiseaseParameters['QuarantineStartDate'] = interventions[intname]['finaldate']    
    else:
        DiseaseParameters['QuarantineStartDate'] = interventions[intname]['QuarantineStartDate']    
    DiseaseParameters['TestingAvailabilityDateHosp'] = interventions[intname]['TestingAvailabilityDateHosp']
    DiseaseParameters['TestingAvailabilityDateComm'] = interventions[intname]['TestingAvailabilityDateComm']
    DiseaseParameters['PerFollowQuarantine'] = float(interventions[intname]['PerFollowQuarantine'])
    DiseaseParameters['testExtra'] = int(interventions[intname]['testExtra'])
    DiseaseParameters['ContactTracing'] = int(interventions[intname]['ContactTracing'])
    
    if 'TimeToFindContactsLow' in interventions[intname] and Utils.RepresentsInt(interventions[intname]['TimeToFindContactsLow']) and \
        'TimeToFindContactsHigh' in interventions[intname] and Utils.RepresentsInt(interventions[intname]['TimeToFindContactsHigh']):
        DiseaseParameters['TimeToFindContactsLow'] = int(interventions[intname]['TimeToFindContactsLow'])
        DiseaseParameters['TimeToFindContactsHigh'] = int(interventions[intname]['TimeToFindContactsHigh'])
    else:
        DiseaseParameters['TimeToFindContactsLow'] = 24
        DiseaseParameters['TimeToFindContactsHigh'] = 72

    if 'UseCountyLevel' in interventions[intname]: 
        if interventions[intname]['UseCountyLevel'] == "1" and os.path.exists(os.path.join("data",Model,interventions[intname]['CountyEncountersFile'])):
            DiseaseParameters['UseCountyLevel'] = 1
            DiseaseParameters['CountyEncountersFile'] = interventions[intname]['CountyEncountersFile']
        else:
            DiseaseParameters['UseCountyLevel'] = 0
    else:
        DiseaseParameters['UseCountyLevel'] = 0
        
    if 'AdjustPopDensity' in interventions[intname]: 
        if interventions[intname]['AdjustPopDensity'] == "1":
            DiseaseParameters['AdjustPopDensity'] = 1
        else:
            DiseaseParameters['AdjustPopDensity'] = 0
    else:
        DiseaseParameters['AdjustPopDensity'] = 0    
        
    if 'TestIncreaseLow' in interventions[intname]: 
        DiseaseParameters['TestIncrease'] = random.random()*(float(interventions[intname]['TestIncreaseHigh']) - float(interventions[intname]['TestIncreaseLow'])) + float(interventions[intname]['TestIncreaseLow'])
        DiseaseParameters['TestIncreaseDate'] = int(interventions[intname]['InterventionStartEndLiftCalcDays'])
    else:
        DiseaseParameters['TestIncrease'] = 0
        DiseaseParameters['TestIncreaseDate'] = 1000
    
    #print(DiseaseParameters['TransProb'])
    
    return DiseaseParameters

    
def SampleParam(ParamMax,ParamMin,**kwargs):
    
    
    
    if 'MC' in kwargs:
        MC = kwargs['MC']
    else:
        MC = False
    
    if 'dict' in kwargs:
        dict = kwargs['dict']
    else:
        dict = {}
        
    if 'dictkey' in kwargs:
        dictkey = kwargs['dictkey']
    else:
        dictkey = ''
        
    if 'listval' in kwargs:
        listval = kwargs['listval']
    else:
        listval = -1
        
    if 'maxstepsize' in kwargs:
        maxstep = kwargs['maxstepsize']
    else:
        maxstep = .05
               
    if not MC:
        val = random.random()*(ParamMax - ParamMin) + ParamMin
    else:
        if listval >= 0:
            CurrentVal = dict[dictkey][listval]
        else:
            CurrentVal = dict[dictkey]
            
        sdval = (ParamMax - ParamMin)/4
        val = CurrentVal - maxstep*sdval*random.random() if random.random() < .5 else CurrentVal + maxstep*sdval*random.random()
        if CurrentVal > ParamMax: CurrentVal = ParamMax
        elif CurrentVal > ParamMin: CurrentVal = ParamMin

    return val

def SampleRunParameters(PID,MC=False,PopulationParameters = {},DiseaseParameters = {},maxstepsize=.05):

    AgeCohortInteraction = {0:{0:1.39277777777778,1:0.328888888888889,2:0.299444444444444,3:0.224444444444444,4:0.108333333333333},
                        1:{0:0.396666666666667,1:2.75555555555556,2:0.342407407407407,3:0.113333333333333,4:0.138333333333333},
                        2:{0:0.503333333333333,1:1.22666666666667,2:1.035,3:0.305185185185185,4:0.180555555555556},
                        3:{0:0.268888888888889,1:0.164074074074074, 2:0.219444444444444,3:0.787777777777778,4:0.27},
                        4:{0:0.181666666666667,1:0.138888888888889, 2:0.157222222222222,3:0.271666666666667,4:0.703333333333333}}


    AG04GammaScale = SampleParam(float(PID['AG04GammaScale']['max']),float(PID['AG04GammaScale']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaScale',listval=0)
    AG04GammaShape = SampleParam(float(PID['AG04GammaShape']['max']), float(PID['AG04GammaShape']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaShape',listval=0)
    AG04AsymptomaticRate = SampleParam(float(PID['AG04AsymptomaticRate']['max']), float(PID['AG04AsymptomaticRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGAsymptomaticRate',listval=0)
    AG04HospRate = SampleParam(float(PID['AG04HospRate']['max']), float(PID['AG04HospRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGHospRate',listval=0)
    AG04MortalityRate = SampleParam(float(PID['AG04MortalityRate']['max']), float(PID['AG04MortalityRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGMortalityRate',listval=0)
    AG517GammaScale = SampleParam(float(PID['AG517GammaScale']['max']), float(PID['AG517GammaScale']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaScale',listval=1)
    AG517GammaShape = SampleParam(float(PID['AG517GammaShape']['max']), float(PID['AG517GammaShape']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaShape',listval=1)
    AG517AsymptomaticRate = SampleParam(float(PID['AG517AsymptomaticRate']['max']), float(PID['AG517AsymptomaticRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGAsymptomaticRate',listval=1)
    AG517HospRate = SampleParam(float(PID['AG517HospRate']['max']), float(PID['AG517HospRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGHospRate',listval=1)
    AG517MortalityRate = SampleParam(float(PID['AG517MortalityRate']['max']), float(PID['AG517MortalityRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGMortalityRate',listval=1)
    AG1849GammaScale = SampleParam(float(PID['AG1849GammaScale']['max']), float(PID['AG1849GammaScale']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaScale',listval=2)
    AG1849GammaShape = SampleParam(float(PID['AG1849GammaShape']['max']), float(PID['AG1849GammaShape']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaShape',listval=2)
    AG1849AsymptomaticRate = SampleParam(float(PID['AG1849AsymptomaticRate']['max']), float(PID['AG1849AsymptomaticRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGAsymptomaticRate',listval=2)
    AG1849HospRate = SampleParam(float(PID['AG1849HospRate']['max']), float(PID['AG1849HospRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGHospRate',listval=2)
    AG1849MortalityRate = SampleParam(float(PID['AG1849MortalityRate']['max']), float(PID['AG1849MortalityRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGMortalityRate',listval=2)
    AG5064GammaScale = SampleParam(float(PID['AG5064GammaScale']['max']), float(PID['AG5064GammaScale']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaScale',listval=3)
    AG5064GammaShape = SampleParam(float(PID['AG5064GammaShape']['max']), float(PID['AG5064GammaShape']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaShape',listval=3)
    AG5064AsymptomaticRate = SampleParam(float(PID['AG5064AsymptomaticRate']['max']), float(PID['AG5064AsymptomaticRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGAsymptomaticRate',listval=3)
    AG5064HospRate = SampleParam(float(PID['AG5064HospRate']['max']), float(PID['AG5064HospRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGHospRate',listval=3)
    AG5064MortalityRate = SampleParam(float(PID['AG5064MortalityRate']['max']), float(PID['AG5064MortalityRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGMortalityRate',listval=3)
    AG65GammaScale = SampleParam(float(PID['AG65GammaScale']['max']), float(PID['AG65GammaScale']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaScale',listval=4)
    AG65GammaShape = SampleParam(float(PID['AG65GammaShape']['max']), float(PID['AG65GammaShape']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='AGGammaShape',listval=4)
    AG65AsymptomaticRate = SampleParam(float(PID['AG65AsymptomaticRate']['max']), float(PID['AG65AsymptomaticRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGAsymptomaticRate',listval=4)
    AG65HospRate = SampleParam(float(PID['AG65HospRate']['max']), float(PID['AG65HospRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGHospRate',listval=4)
    AG65MortalityRate = SampleParam(float(PID['AG65MortalityRate']['max']), float(PID['AG65MortalityRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AGMortalityRate',listval=4)
    householdcontactRate = SampleParam(float(PID['householdcontactRate']['max']), float(PID['householdcontactRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=PopulationParameters,dictkey='householdcontactRate')
    IncubationTime = SampleParam(float(PID['IncubationTime']['max']), float(PID['IncubationTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='IncubationTime')
    mildContagiousTime = SampleParam(float(PID['mildContagiousTime']['max']), float(PID['mildContagiousTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='mildContagiousTime')
    AsymptomaticReducationTrans = SampleParam(float(PID['AsymptomaticReducationTrans']['max']), float(PID['AsymptomaticReducationTrans']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='AsymptomaticReducationTrans')
    preContagiousTime = SampleParam(float(PID['preContagiousTime']['max']), float(PID['preContagiousTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='preContagiousTime')
    symptomaticTime = SampleParam(float(PID['symptomaticTime']['max']), float(PID['symptomaticTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='symptomaticTime')
    postContagiousTime = SampleParam(float(PID['postContagiousTime']['max']), float(PID['postContagiousTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='postContagiousTime')
    symptomaticContactRateReduction = SampleParam(float(PID['symptomaticContactRateReduction']['max']), float(PID['symptomaticContactRateReduction']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='symptomaticContactRateReduction')
    preHospTime = SampleParam(float(PID['preHospTime']['max']), float(PID['preHospTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='preHospTime')
    hospitalSymptomaticTime = SampleParam(float(PID['hospitalSymptomaticTime']['max']), float(PID['hospitalSymptomaticTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='hospitalSymptomaticTime')
    ICURate = SampleParam(float(PID['ICURate']['max']), float(PID['ICURate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='ICURate')
    ICUtime = SampleParam(float(PID['ICUtime']['max']), float(PID['ICUtime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='ICUtime')
    PostICUTime = SampleParam(float(PID['PostICUTime']['max']), float(PID['PostICUTime']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='PostICUTime') 
    hospitalSymptomaticContactRateReduction = SampleParam(float(PID['hospitalSymptomaticContactRateReduction']['max']), float(PID['hospitalSymptomaticContactRateReduction']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='hospitalSymptomaticContactRateReduction')
    EDVisit = SampleParam(float(PID['EDVisit']['max']), float(PID['EDVisit']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='EDVisit')
    ProbabilityOfTransmissionPerContact = SampleParam(float(PID['ProbabilityOfTransmissionPerContact']['max']), float(PID['ProbabilityOfTransmissionPerContact']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='ProbabilityOfTransmissionPerContact')
    CommunityTestingRate = SampleParam(float(PID['CommunityTestingRate']['max']), float(PID['CommunityTestingRate']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='CommunityTestingRate') 
    pdscale1 = SampleParam(float(PID['pdscale1']['max']), float(PID['pdscale1']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='pdscale1')
    pdscale2 = SampleParam(float(PID['pdscale2']['max']), float(PID['pdscale2']['min']),MC=MC,maxstepsize=maxstepsize,dict=DiseaseParameters,dictkey='pdscale2')
    

    PopulationParameters['AGGammaScale'] = [AG04GammaScale,AG517GammaScale,AG1849GammaScale,AG5064GammaScale,AG65GammaScale]
    PopulationParameters['AGGammaShape'] = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    PopulationParameters['householdcontactRate'] = householdcontactRate
    
    
    DiseaseParameters['AGHospRate'] = [AG04HospRate,AG517HospRate,AG1849HospRate,AG5064HospRate,AG65HospRate]
    DiseaseParameters['AGAsymptomaticRate'] = [AG04AsymptomaticRate,AG517AsymptomaticRate,AG1849AsymptomaticRate,AG5064AsymptomaticRate,AG65AsymptomaticRate]
    DiseaseParameters['AGMortalityRate'] = [AG04MortalityRate,AG517MortalityRate,AG1849MortalityRate,AG5064MortalityRate,AG65MortalityRate]
    
    # Disease Progression Parameters
    DiseaseParameters['IncubationTime'] = IncubationTime
    
    # gamma1
    DiseaseParameters['mildContagiousTime'] = mildContagiousTime
    DiseaseParameters['AsymptomaticReducationTrans'] = AsymptomaticReducationTrans
    
    # gamma2
    DiseaseParameters['preContagiousTime'] = preContagiousTime
    DiseaseParameters['symptomaticTime'] = symptomaticTime
    DiseaseParameters['postContagiousTime'] = postContagiousTime
    DiseaseParameters['symptomaticContactRateReduction'] = symptomaticContactRateReduction
    
    DiseaseParameters['preHospTime'] = preHospTime
    DiseaseParameters['hospitalSymptomaticTime'] = hospitalSymptomaticTime
    DiseaseParameters['ICURate'] = ICURate
    DiseaseParameters['ICUtime'] = ICUtime
    DiseaseParameters['PostICUTime'] = PostICUTime
    DiseaseParameters['hospitalSymptomaticContactRateReduction'] = hospitalSymptomaticContactRateReduction
    
    DiseaseParameters['pdscale1'] = pdscale1
    DiseaseParameters['pdscale2'] = pdscale2
    
    DiseaseParameters['EDVisit'] = EDVisit
    
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = ProbabilityOfTransmissionPerContact
    
    DiseaseParameters['CommunityTestingRate'] = CommunityTestingRate
    
    return PopulationParameters, DiseaseParameters


def InterventionsParameters(Model,intfilename,startdate,submodel=''):
    
    intdatevals = ['InterventionDate','SchoolCloseDate','SchoolOpenDate','InterventionStartReductionDate',
                    'InterventionStartReductionDateCalcDays','InterventionStartEndLift','InterventionStartEndLiftCalcDays'
                    ,'QuarantineStartDate','TestingAvailabilityDateHosp','TestingAvailabilityDateComm','finaldate']
    
    interventions = {}
    try:
        InterventionVals = os.path.join('data',Model,intfilename)
        with open(InterventionVals, mode='r') as infile:
            reader = csv.reader(infile)
            header = next(reader)            
            for rows in reader:
                loadIntervention = True
                intname = rows[0]
                if len(submodel) > 1:
                    if intname != submodel:
                        loadIntervention = False
                # intervention data validation
                if len(intname) < 1:
                    loadIntervention = False
                
                if loadIntervention:
                    interventions[intname] = {}
                    for i in range(0,len(header)):
                        if header[i] in intdatevals and rows[i] != '':
                            interventions[intname][header[i]] = (Utils.dateparser(rows[i]) - startdate).days
                            interventions[intname][header[i]+'_orig'] = Utils.dateparser(rows[i])
                        else:    
                            interventions[intname][header[i]] = rows[i]
                
    except Exception as e:
        print("Interventions values error. Please confirm the interventions file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug":
            print(traceback.format_exc())
        exit()   
    
        
    return interventions


