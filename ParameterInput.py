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
import random
import traceback
import os
import csv

import ParameterSet
import Utils

def setInfectionProb(interventions,intname,DiseaseParameters,Model):

    interventions[intname]['InterventionReduction'] = []
    interventions[intname]['InterventionReductionLow'] = []
    interventions[intname]['SchoolInterventionReduction'] = []
    interventions[intname]['Mobility'] = []
        
    interventions[intname]['SchoolInterventionDate'] = interventions[intname]['SchoolCloseDate']
    intred = random.random()*(float(interventions[intname]['InterventionReductionPerMax'])-float(interventions[intname]['InterventionReductionPerMin']))+float(interventions[intname]['InterventionReductionPerMin'])
    intredLow = random.random()*(float(interventions[intname]['InterventionReductionPerLowMax'])-float(interventions[intname]['InterventionReductionPerLowMin']))+float(interventions[intname]['InterventionReductionPerLowMin'])
    intdays = int(interventions[intname]['InterventionStartReductionDateCalcDays'])-int(interventions[intname]['InterventionStartReductionDate'])
    mobeffect = float(interventions[intname]['InterventionMobilityEffect'])
        
    intredred = (1-intred)/intdays
    intredLowred = (1-intredLow)/intdays
    intredval = 1 - intredred
    intredvalLow = 1 - intredLowred
    mobeffectred = (1-mobeffect)/intdays
    mobeffectval = 1 - mobeffectred
    
    for i in range(int(interventions[intname]['InterventionStartReductionDate']),int(interventions[intname]['InterventionStartReductionDateCalcDays'])):
        interventions[intname]['InterventionReduction'].append(intredval)    
        interventions[intname]['InterventionReductionLow'].append(intredvalLow)
        interventions[intname]['SchoolInterventionReduction'].append(float(interventions[intname]['SchoolCloseReductionPer']))
        interventions[intname]['Mobility'].append(mobeffectval)
        intredval -= intredred
        intredvalLow -= intredLowred
        mobeffectval -= mobeffectred

    for i in range(int(interventions[intname]['InterventionStartReductionDateCalcDays'])+1,int(interventions[intname]['InterventionStartEndLift'])):
        interventions[intname]['InterventionReduction'].append(intredval)    
        interventions[intname]['InterventionReductionLow'].append(intredvalLow)
        interventions[intname]['SchoolInterventionReduction'].append(intredval)
        interventions[intname]['Mobility'].append(mobeffectval)
    
    opendays = int(interventions[intname]['InterventionStartEndLiftCalcDays']) - int(interventions[intname]['InterventionStartEndLift']+1)
    openinc = ((1-intred)*float(interventions[intname]['InterventionEndPerIncrease']))/opendays
    openincLow = ((1-intredLow)*float(interventions[intname]['InterventionEndPerIncrease']))/opendays
    mobinc = ((1-mobeffect)*float(interventions[intname]['InterventionEndPerIncrease']))/opendays
    
    for i in range(int(interventions[intname]['InterventionStartEndLift']+1),int(interventions[intname]['InterventionStartEndLiftCalcDays'])):
        interventions[intname]['InterventionReduction'].append(intredval)    
        interventions[intname]['InterventionReductionLow'].append(intredvalLow)
        interventions[intname]['SchoolInterventionReduction'].append(intredval)
        interventions[intname]['Mobility'].append(mobeffectval)
        intredval+=openinc
        intredvalLow+=openincLow
        mobeffectval += mobinc
    
    opendays = (int(interventions[intname]['finaldate']) - int(interventions[intname]['InterventionStartEndLiftCalcDays']+1))
    openinc = (1-intredval)/opendays
    openincLow = (1-intredvalLow)/opendays    
    mobinc = (1-mobeffectval)/opendays
    for i in range(int(interventions[intname]['InterventionStartEndLiftCalcDays']+1),int(interventions[intname]['finaldate'])):
        interventions[intname]['InterventionReduction'].append(intredval)    
        interventions[intname]['InterventionReductionLow'].append(intredvalLow)
        if i < (interventions[intname]['SchoolOpenDate']):
            interventions[intname]['SchoolInterventionReduction'].append(intredval)
        interventions[intname]['Mobility'].append(mobeffectval)
        intredval+=openinc
        intredvalLow+=openincLow
        mobeffectval += mobinc
        
    for i in range(int(interventions[intname]['SchoolOpenDate']),int(interventions[intname]['finaldate'])):
        interventions[intname]['SchoolInterventionReduction'].append(float(interventions[intname]['SchoolOpenReductionAmt']))

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
    
    for i in range(0,interventions[intname]['SchoolCloseDate']):
        DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact'])
    
    for i in range(0,interventions[intname]['InterventionStartReductionDate']):
        DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact'])
        DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact'])
        DiseaseParameters['InterventionMobilityEffect'].append(1)
    
    for i in range(0,len(interventions[intname]['InterventionReduction'])):
        DiseaseParameters['TransProb'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*interventions[intname]['InterventionReduction'][i])
        DiseaseParameters['TransProbLow'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*interventions[intname]['InterventionReductionLow'][i])
        DiseaseParameters['TransProbSchool'].append(DiseaseParameters['ProbabilityOfTransmissionPerContact']*interventions[intname]['SchoolInterventionReduction'][i])
        DiseaseParameters['InterventionMobilityEffect'].append(interventions[intname]['Mobility'][i])
    
    DiseaseParameters['InterventionDate'] = interventions[intname]['InterventionStartReductionDate']
    
    DiseaseParameters['InterventionReduction'] = interventions[intname]['InterventionReduction']
    DiseaseParameters['InterventionReductionLow'] = interventions[intname]['InterventionReductionLow']
    DiseaseParameters['SchoolInterventionDate'] = interventions[intname]['SchoolInterventionDate']
    DiseaseParameters['SchoolInterventionReduction'] = interventions[intname]['SchoolInterventionReduction']
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
    
    return DiseaseParameters
    

def SetRunParameters(PID):

    AgeCohortInteraction = {0:{0:1.39277777777778,1:0.328888888888889,2:0.299444444444444,3:0.224444444444444,4:0.108333333333333},
                        1:{0:0.396666666666667,1:2.75555555555556,2:0.342407407407407,3:0.113333333333333,4:0.138333333333333},
                        2:{0:0.503333333333333,1:1.22666666666667,2:1.035,3:0.305185185185185,4:0.180555555555556},
                        3:{0:0.268888888888889,1:0.164074074074074, 2:0.219444444444444,3:0.787777777777778,4:0.27},
                        4:{0:0.181666666666667,1:0.138888888888889, 2:0.157222222222222,3:0.271666666666667,4:0.703333333333333}}

                    
    AG04GammaScale = random.random()*(float(PID['AG04GammaScale']['max']) - float(PID['AG04GammaScale']['min'])) + float(PID['AG04GammaScale']['min'])
    AG04GammaShape = random.random()*(float(PID['AG04GammaShape']['max']) - float(PID['AG04GammaShape']['min'])) + float(PID['AG04GammaShape']['min'])
    AG04AsymptomaticRate = random.random()*(float(PID['AG04AsymptomaticRate']['max']) - float(PID['AG04AsymptomaticRate']['min'])) + float(PID['AG04AsymptomaticRate']['min'])
    AG04HospRate = random.random()*(float(PID['AG04HospRate']['max']) - float(PID['AG04HospRate']['min'])) + float(PID['AG04HospRate']['min'])
    AG04MortalityRate = random.random()*(float(PID['AG04MortalityRate']['max']) - float(PID['AG04MortalityRate']['min'])) + float(PID['AG04MortalityRate']['min'])
    AG517GammaScale = random.random()*(float(PID['AG517GammaScale']['max']) - float(PID['AG517GammaScale']['min'])) + float(PID['AG517GammaScale']['min'])
    AG517GammaShape = random.random()*(float(PID['AG517GammaShape']['max']) - float(PID['AG517GammaShape']['min'])) + float(PID['AG517GammaShape']['min'])
    AG517AsymptomaticRate = random.random()*(float(PID['AG517AsymptomaticRate']['max']) - float(PID['AG517AsymptomaticRate']['min'])) + float(PID['AG517AsymptomaticRate']['min'])
    AG517HospRate = random.random()*(float(PID['AG517HospRate']['max']) - float(PID['AG517HospRate']['min'])) + float(PID['AG517HospRate']['min'])
    AG517MortalityRate = random.random()*(float(PID['AG517MortalityRate']['max']) - float(PID['AG517MortalityRate']['min'])) + float(PID['AG517MortalityRate']['min'])
    AG1849GammaScale = random.random()*(float(PID['AG1849GammaScale']['max']) - float(PID['AG1849GammaScale']['min'])) + float(PID['AG1849GammaScale']['min'])
    AG1849GammaShape = random.random()*(float(PID['AG1849GammaShape']['max']) - float(PID['AG1849GammaShape']['min'])) + float(PID['AG1849GammaShape']['min'])
    AG1849AsymptomaticRate = random.random()*(float(PID['AG1849AsymptomaticRate']['max']) - float(PID['AG1849AsymptomaticRate']['min'])) + float(PID['AG1849AsymptomaticRate']['min'])
    AG1849HospRate = random.random()*(float(PID['AG1849HospRate']['max']) - float(PID['AG1849HospRate']['min'])) + float(PID['AG1849HospRate']['min'])
    AG1849MortalityRate = random.random()*(float(PID['AG1849MortalityRate']['max']) - float(PID['AG1849MortalityRate']['min'])) + float(PID['AG1849MortalityRate']['min'])
    AG5064GammaScale = random.random()*(float(PID['AG5064GammaScale']['max']) - float(PID['AG5064GammaScale']['min'])) + float(PID['AG5064GammaScale']['min'])
    AG5064GammaShape = random.random()*(float(PID['AG5064GammaShape']['max']) - float(PID['AG5064GammaShape']['min'])) + float(PID['AG5064GammaShape']['min'])
    AG5064AsymptomaticRate = random.random()*(float(PID['AG5064AsymptomaticRate']['max']) - float(PID['AG5064AsymptomaticRate']['min'])) + float(PID['AG5064AsymptomaticRate']['min'])
    AG5064HospRate = random.random()*(float(PID['AG5064HospRate']['max']) - float(PID['AG5064HospRate']['min'])) + float(PID['AG5064HospRate']['min'])
    AG5064MortalityRate = random.random()*(float(PID['AG5064MortalityRate']['max']) - float(PID['AG5064MortalityRate']['min'])) + float(PID['AG5064MortalityRate']['min'])
    AG65GammaScale = random.random()*(float(PID['AG65GammaScale']['max']) - float(PID['AG65GammaScale']['min'])) + float(PID['AG65GammaScale']['min'])
    AG65GammaShape = random.random()*(float(PID['AG65GammaShape']['max']) - float(PID['AG65GammaShape']['min'])) + float(PID['AG65GammaShape']['min'])
    AG65AsymptomaticRate = random.random()*(float(PID['AG65AsymptomaticRate']['max']) - float(PID['AG65AsymptomaticRate']['min'])) + float(PID['AG65AsymptomaticRate']['min'])
    AG65HospRate = random.random()*(float(PID['AG65HospRate']['max']) - float(PID['AG65HospRate']['min'])) + float(PID['AG65HospRate']['min'])
    AG65MortalityRate = random.random()*(float(PID['AG65MortalityRate']['max']) - float(PID['AG65MortalityRate']['min'])) + float(PID['AG65MortalityRate']['min'])
    householdcontactRate = random.random()*(float(PID['householdcontactRate']['max']) - float(PID['householdcontactRate']['min'])) + float(PID['householdcontactRate']['min'])
    IncubationTime = random.random()*(float(PID['IncubationTime']['max']) - float(PID['IncubationTime']['min'])) + float(PID['IncubationTime']['min'])
    mildContagiousTime = random.random()*(float(PID['mildContagiousTime']['max']) - float(PID['mildContagiousTime']['min'])) + float(PID['mildContagiousTime']['min'])
    AsymptomaticReducationTrans = random.random()*(float(PID['AsymptomaticReducationTrans']['max']) - float(PID['AsymptomaticReducationTrans']['min'])) + float(PID['AsymptomaticReducationTrans']['min'])
    preContagiousTime = random.random()*(float(PID['preContagiousTime']['max']) - float(PID['preContagiousTime']['min'])) + float(PID['preContagiousTime']['min'])
    symptomaticTime = random.random()*(float(PID['symptomaticTime']['max']) - float(PID['symptomaticTime']['min'])) + float(PID['symptomaticTime']['min'])
    postContagiousTime = random.random()*(float(PID['postContagiousTime']['max']) - float(PID['postContagiousTime']['min'])) + float(PID['postContagiousTime']['min'])
    symptomaticContactRateReduction = random.random()*(float(PID['symptomaticContactRateReduction']['max']) - float(PID['symptomaticContactRateReduction']['min'])) + float(PID['symptomaticContactRateReduction']['min'])
    preHospTime = random.random()*(float(PID['preHospTime']['max']) - float(PID['preHospTime']['min'])) + float(PID['preHospTime']['min'])
    hospitalSymptomaticTime = random.random()*(float(PID['hospitalSymptomaticTime']['max']) - float(PID['hospitalSymptomaticTime']['min'])) + float(PID['hospitalSymptomaticTime']['min'])
    ICURate = random.random()*(float(PID['ICURate']['max']) - float(PID['ICURate']['min'])) + float(PID['ICURate']['min'])
    ICUtime = random.random()*(float(PID['ICUtime']['max']) - float(PID['ICUtime']['min'])) + float(PID['ICUtime']['min'])
    PostICUTime = random.random()*(float(PID['PostICUTime']['max']) - float(PID['PostICUTime']['min'])) + float(PID['PostICUTime']['min'])
    hospitalSymptomaticContactRateReduction = random.random()*(float(PID['hospitalSymptomaticContactRateReduction']['max']) - float(PID['hospitalSymptomaticContactRateReduction']['min'])) + float(PID['hospitalSymptomaticContactRateReduction']['min'])
    EDVisit = random.random()*(float(PID['EDVisit']['max']) - float(PID['EDVisit']['min'])) + float(PID['EDVisit']['min'])
    ProbabilityOfTransmissionPerContact = random.random()*(float(PID['ProbabilityOfTransmissionPerContact']['max']) - float(PID['ProbabilityOfTransmissionPerContact']['min'])) + float(PID['ProbabilityOfTransmissionPerContact']['min'])
    CommunityTestingRate = random.random()*(float(PID['CommunityTestingRate']['max']) - float(PID['CommunityTestingRate']['min'])) + float(PID['CommunityTestingRate']['min'])
    pdscale1 = random.random()*(float(PID['pdscale1']['max']) - float(PID['pdscale1']['min'])) + float(PID['pdscale1']['min'])
    pdscale2 = random.random()*(float(PID['pdscale2']['max']) - float(PID['pdscale2']['min'])) + float(PID['pdscale2']['min'])
    
    PopulationParameters = {}
    PopulationParameters['AGGammaScale'] = [AG04GammaScale,AG517GammaScale,AG1849GammaScale,AG5064GammaScale,AG65GammaScale]
    PopulationParameters['AGGammaShape'] = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    PopulationParameters['householdcontactRate'] = householdcontactRate
    
    DiseaseParameters = {}
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
                        else:    
                            interventions[intname][header[i]] = rows[i]
                
    except Exception as e:
        print("Interventions values error. Please confirm the interventions file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug":
            print(traceback.format_exc())
        exit()   
    
        
    return interventions


