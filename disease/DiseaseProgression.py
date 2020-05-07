# -----------------------------------------------------------------------------
# DiseaseProgression.py contains all disease-specific events
# -----------------------------------------------------------------------------
from random import gammavariate, random, randint
import ParameterSet
import numpy as np
import Utils
import events.SimulationEvent as SimEvent
import math


def calcIntRegTime(start,end,IntStart,IntEnd):
    
    if IntStart > 0:
        if start > IntEnd or end < IntStart:
            regtime = end - start
            inttime = 0
        elif start > IntStart and end < IntEnd:
            inttime = end - start
            regtime = 0
        else:
            if start < IntStart and end < IntEnd:
                regtime = IntStart - start
                inttime = end - IntStart
            elif start < IntStart and end > IntEnd:
                regtime = (IntStart - start) + (end - IntEnd)
                inttime = IntEnd - IntStart
            elif start > IntStart and end > IntEnd:
                inttime = IntEnd - start
                regtime = end - IntEnd
            else:
                print("ERRROR")
                inttime = 0
                regtime = end - start
    else:
        inttime = 0
        regtime = end - start 
    return regtime, inttime
    
def getDiseaseTimeline(ageCohort,DiseaseParameters):
    diseasetimeline = {}
    diseasetimeline['Symptomatic'] = False
    diseasetimeline['Hospitalization']=False
    diseasetimeline['ICU']=False        
    
    # Everyone is subject to incubation time
    incubationTime = gammavariate(DiseaseParameters['IncubationTime'],1)
    #incubationTime = gammavariate(DiseaseParameters['IncubationTime'],1)
    
    #if they are "symptomatic"
    if random() > DiseaseParameters['AGAsymptomaticRate'][ageCohort]:
        #Time they are pre contagious (transmission is higher)
        preContagiousTime = gammavariate(DiseaseParameters['preContagiousTime'],1)
        
        diseasetimeline['Symptomatic'] = True
        
        #Are they hospitalized
        if random() < DiseaseParameters['AGHospRate'][ageCohort]:
            diseasetimeline['Hospitalization']=True
            # assume hospitalized patients are not transmissable after symptoms
            postContagiousTime = 0            
                
            # Do they end up in ICU? (should probably be age weighted
            if random() < DiseaseParameters['ICURate']:
                diseasetimeline['ICU']=True        
                ICUTime = gammavariate(DiseaseParameters['ICUtime'],1)
                PostICUTime = gammavariate(DiseaseParameters['PostICUTime'], 1)
                if PostICUTime == 0:
                    PostICUTime = 1
                symptomaticTime = ICUTime + PostICUTime
            else:
                # symptomatic time
                symptomaticTime = gammavariate(DiseaseParameters['hospitalSymptomaticTime']*2, .5)
                ICUTime = 0
                PostICUTime = 0
            
            #Time till they go to the hospital - ensure it is less than hospital symptomatic time
            preHospTime = gammavariate(DiseaseParameters['preHospTime']*2, .5)
            while preHospTime > symptomaticTime:
                symptomaticTime+=1
            
        else:
            #Get the amount of time they are symptomatic fo rnon-hospital patients
            
            symptomaticTime = gammavariate(DiseaseParameters['symptomaticTime'], 1)
            postContagiousTime = gammavariate(DiseaseParameters['postContagiousTime'], 1)
            #### For visits to providers for testing or ED -- used only if this is true
            preHospTime = gammavariate(DiseaseParameters['preHospTime'], 1)
            while preHospTime > symptomaticTime:
                symptomaticTime+=1
            
            ICUTime = 0
            PostICUTime = 0
        # set for household events    
        ContagiousTime = preContagiousTime+symptomaticTime+postContagiousTime
    # Asymptomatic
    else:
        # only contagious time is set
        ContagiousTime = gammavariate(DiseaseParameters['mildContagiousTime'], 1)
        preContagiousTime = 0
        preHospTime = 0
        symptomaticTime = 0
        postContagiousTime = 0
        ICUTime = 0
        PostICUTime = 0
    
    diseasetimeline['incubationTime'] = incubationTime
    diseasetimeline['preContagiousTime'] = preContagiousTime
    diseasetimeline['ContagiousTime'] = ContagiousTime
    diseasetimeline['preContagiousTime'] = preContagiousTime
    diseasetimeline['preHospTime'] = preHospTime
    diseasetimeline['symptomaticTime'] = symptomaticTime
    diseasetimeline['postContagiousTime'] = postContagiousTime
    ## need to add preICU time
    diseasetimeline['ICUTime'] = ICUTime
    diseasetimeline['PostICUTime'] = PostICUTime 
    
    return diseasetimeline
    
def getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,StartTime,Length,DiseaseParameters,LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort,diseasetimeline,HouseholdId, PersonId,uselowintreduction=False, Hospital=False,Symptomatic=False,Asymptomatic=False):
    
    IntVals = DiseaseParameters['InterventionReduction']
    if uselowintreduction:
        IntVals = DiseaseParameters['InterventionReductionLow']
            
    RegTransProb = DiseaseParameters['ProbabilityOfTransmissionPerContact']
    IntStart = DiseaseParameters['InterventionDate']
    IntEnd = IntStart+len(IntVals)-1
    IntReduction = IntVals
    if ageCohort <= 1:
        IntStart = DiseaseParameters['SchoolInterventionDate']
        IntEnd  = IntStart + len(DiseaseParameters['SchoolInterventionReduction'])-1
        IntReduction = DiseaseParameters['SchoolInterventionReduction']
        
    RegularTime,InterventionTime = calcIntRegTime(StartTime,StartTime+Length,IntStart,IntEnd)
    IntTransProb = 0
    IntLength = InterventionTime
    if InterventionTime > 0:
        if math.floor(timeNow) <= IntStart:
            st = IntStart
        else:
            st = math.floor(timeNow)
        while st < IntEnd and IntLength > 1:
            IntTransProb += RegTransProb * IntReduction[st-IntStart]
            st+=1
            IntLength -= 1 

    ratemodifier = 1
    if Hospital:
        ratemodifier = DiseaseParameters['hospitalSymptomaticContactRateReduction']
    elif Symptomatic:    
        ratemodifier = DiseaseParameters['symptomaticContactRateReduction']
    elif Asymptomatic:
        ratemodifier = DiseaseParameters['AsymptomaticReducationTrans']
      
              
    numRandInfReg = np.random.poisson(ratemodifier *
                    contactRate * RegularTime * RegTransProb, 1)[0]  ### this isn't good to be switching between numpy and random
    #print(numRandInfReg," ",timeNow, " " ,StartTime, " ", RegularTime)
    
    IERegs,InfectionsDict = createInfectionEvents(numRandInfReg,InfectionsDict, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, StartTime, RegularTime, 0, DiseaseParameters,HouseholdId, PersonId)
                         
    #print("ratemodifier:",ratemodifier," * contactRate:",contactRate," * RegularTime:",RegularTime, " * RegTransProb:",RegTransProb," = ",  ratemodifier *
    #                contactRate * RegularTime * RegTransProb, " --> ",numRandInfReg," -->",len(IERegs))    
    numRandInfInt = np.random.poisson(ratemodifier *
                    contactRate * IntTransProb, 1)[0]  ### this isn't good to be switching between numpy and random
    IEInts,InfectionsDict = createInfectionEvents(numRandInfInt,InfectionsDict, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, StartTime+RegularTime, InterventionTime, 1, DiseaseParameters,HouseholdId, PersonId)

    return numRandInfReg, IERegs, numRandInfInt, IEInts, InfectionsDict
    
    
def SetupTransmissableContactEvents(timeNow,tend,DiseaseParameters, LocalInteractionMatrixList, RegionListGuide,
                                    HouseholdId, PersonId, LocalPopulationId,
                                    contactRate, householdcontactRate,
                                    ageCohort,numHouseholdMembersSusceptible,
                                    HospitalTransitionMatrixList, ProportionLowIntReduction):
                                            

        InfectionsDict = {}
        InfectionsDict['NonLocalInfections']=0
        InfectionsDict['NonLocalRegionsInfected'] = []
        InfectionsDict['NonLocalPopsInfected'] = []
        InfectionsDict['LocalInfections'] = 0
        
        uselowintreduction = False
        if random() < ProportionLowIntReduction:
            uselowintreduction = True                
        
        # Set the incupbation time
        queueEvents = []
        
        diseasetimeline = getDiseaseTimeline(ageCohort,DiseaseParameters)
               
                    
        ### Add event for when the patient becomes contagious pre symptoms
        queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+diseasetimeline['incubationTime'], HouseholdId, PersonId, ParameterSet.Contagious))
        
        # if they are sym
        if diseasetimeline['Symptomatic'] > 0: 
            t1 = diseasetimeline['incubationTime']+diseasetimeline['preContagiousTime']
            queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t1, HouseholdId, PersonId, ParameterSet.Symptomatic))
            
            # infection events pre-contagious
            
            numRandInfReg, IERegs, numRandInfInt, IEInts,InfectionsDict = getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,timeNow+diseasetimeline['incubationTime'],diseasetimeline['preContagiousTime'],DiseaseParameters,
                             LocalInteractionMatrixList, RegionListGuide,LocalPopulationId, ageCohort,diseasetimeline,HouseholdId, PersonId, uselowintreduction=uselowintreduction)
            if numRandInfReg > 0: queueEvents.extend(IERegs)
            if numRandInfInt > 0: queueEvents.extend(IEInts)
            
        
            if diseasetimeline['Hospitalization']:
                t2 = t1 + diseasetimeline['preHospTime']
                
                # infection events 
                numRandInfReg, IERegs, numRandInfInt, IEInts,InfectionsDict = getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,timeNow+t1,diseasetimeline['preHospTime'],DiseaseParameters,LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort,diseasetimeline,HouseholdId, PersonId, uselowintreduction=uselowintreduction,Symptomatic=True)
                if numRandInfReg > 0: queueEvents.extend(IERegs)
                if numRandInfInt > 0: queueEvents.extend(IEInts)             
                
            
                # get hospital they went to
                if len(HospitalTransitionMatrixList) > 0:
                    Hospital = Utils.multinomial(HospitalTransitionMatrixList, 1)
                else:
                    Hospital = 0
                
                # if they went to ICU
                if diseasetimeline['ICU']:
                    # add start ICU time event (assumes no pre-ICU time) ## need to add preICU time
                    queueEvents.append(SimEvent.PersonHospICUEvent(timeNow+t2, HouseholdId, PersonId, Hospital))
                       
                    # add end ICU time event                 
                    t2I = t2 + diseasetimeline['ICUTime']
                    queueEvents.append(SimEvent.PersonHospExitICUEvent(timeNow+t2I, HouseholdId, PersonId, Hospital))
                
                else:             
                    # Set the time at which they go to hospital    
                    queueEvents.append(SimEvent.PersonHospCritEvent(timeNow+t2, HouseholdId, PersonId, Hospital))
                    
                # time till they leave hospital
                t3 = t2 + diseasetimeline['symptomaticTime']
                # if they die
                if random() < DiseaseParameters['AGMortalityRate'][ageCohort]:
                    queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t3, HouseholdId, PersonId, ParameterSet.Dead))
                else:
                    queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t3, HouseholdId, PersonId, ParameterSet.Recovered))
                
                #Symptomatic Infection Events                                           
                numRandInfReg, IERegs, numRandInfInt, IEInts,InfectionsDict = getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,timeNow+t2,diseasetimeline['symptomaticTime'],DiseaseParameters,LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, diseasetimeline,HouseholdId, PersonId,uselowintreduction=uselowintreduction, Hospital=True)
                if numRandInfReg > 0: queueEvents.extend(IERegs)
                if numRandInfInt > 0: queueEvents.extend(IEInts)
                
                
            else:
                
                detected = False
                t2E = t1 + diseasetimeline['preHospTime']
                if random() < DiseaseParameters['EDVisit']:
                    # If they go to see a provider - then we can capture them for testing 
                    queueEvents.append(SimEvent.PersonHospEDEvent(timeNow+t2E, HouseholdId, PersonId, 0))
                    if t2E > DiseaseParameters['TestingAvailabilityDateHosp']:
                        if random() < ParameterSet.TestEfficacy:
                            detected = True
                    
                t2 = t1 + diseasetimeline['symptomaticTime']
                queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t2, HouseholdId, PersonId, ParameterSet.Contagious))
                t3 = t2 + diseasetimeline['postContagiousTime']
                queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t3, HouseholdId, PersonId, ParameterSet.Recovered))
                
                #Symptomatic Infection Events                                           
                numRandInfReg, IERegs, numRandInfInt, IEInts,InfectionsDict = getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,timeNow+t1,diseasetimeline['symptomaticTime'],DiseaseParameters,LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort,diseasetimeline,HouseholdId, PersonId, uselowintreduction=uselowintreduction, Symptomatic=True)
                if numRandInfReg > 0: 
                    ## assume if they are a positive test than after that they don't infect anyone while still contagious
                    if detected:
                        for i in range(0,len(IERegs)):
                            SE = IERegs[i]
                            if SE.timestamp < t2E:
                                queueEvents.append(SE)
                    else:
                        queueEvents.extend(IERegs)
                if numRandInfInt > 0: 
                    ## assume if they are a positive test than after that they don't infect anyone while still contagious
                    if detected:
                        for i in range(0,len(IEInts)):
                            SE = IEInts[i]
                            if SE.timestamp < t2E:
                                queueEvents.append(SE)
                    else:
                        queueEvents.extend(IEInts)
                
                #Post-Contagious Infection Events                                           
                numRandInfReg, IERegs, numRandInfInt, IEInts,InfectionsDict = getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,timeNow+t2,diseasetimeline['postContagiousTime'],DiseaseParameters,LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort,diseasetimeline,HouseholdId, PersonId, uselowintreduction=uselowintreduction)
                if numRandInfReg > 0: queueEvents.extend(IERegs)
                if numRandInfInt > 0: queueEvents.extend(IEInts)             
                
        # Not Symptomatic        
        else:         
            t1 = diseasetimeline['incubationTime']
            queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t1, HouseholdId, PersonId, ParameterSet.Contagious))
            t2 = t1 + diseasetimeline['ContagiousTime']
            queueEvents.append(SimEvent.PersonStatusUpdate(timeNow+t2, HouseholdId, PersonId, ParameterSet.Recovered))
            
            numRandInfReg, IERegs, numRandInfInt, IEInts,InfectionsDict = getInfectionQueueEvents(timeNow,InfectionsDict,contactRate,timeNow+t1,diseasetimeline['ContagiousTime'],DiseaseParameters,LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, diseasetimeline,HouseholdId, PersonId, uselowintreduction=uselowintreduction,Asymptomatic=True)
            if numRandInfReg > 0: queueEvents.extend(IERegs)
            if numRandInfInt > 0: queueEvents.extend(IEInts)
            if timeNow+t1 > DiseaseParameters['TestingAvailabilityDateComm']:
                if random() < DiseaseParameters['CommunityTestingRate']:
                    queueEvents.append(SimEvent.PersonHospTestEvent(timeNow+t1+random()*t2, HouseholdId, PersonId, 0))
            
        ###################    
        # Now infect household members
        if numHouseholdMembersSusceptible > 0:
            numHHInf = np.random.poisson(householdcontactRate * diseasetimeline['ContagiousTime'] * DiseaseParameters['ProbabilityOfTransmissionPerContact'], 1)[0]  ### this isn't good to be switching between numpy and random
            if numHHInf > 0: 
                if numHHInf > numHouseholdMembersSusceptible:
                    numHHInf = numHouseholdMembersSusceptible
                for i in range(numHHInf):
                    t = timeNow + diseasetimeline['incubationTime'] + random() * diseasetimeline['ContagiousTime']
                    queueEvents.append(SimEvent.HouseholdInfectionEvent(timeNow + t, HouseholdId, PersonId))
                    if i > numHouseholdMembersSusceptible:
                        break;
        
        return queueEvents,InfectionsDict


def createInfectionEvents(numInf,InfectionsDict, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, preTime, ContagiousTime, intervention, DiseaseParameters,HouseholdId, PersonId):
    
    events = []
    if numInf > 0:
        for i in range(0, numInf):
            # get time frame of infection
            t = preTime + random() * ContagiousTime
            #Decide if it is in the local population or somewhere else
            if intervention == 1:
                LocalInteractionMatrixListINT = LocalInteractionMatrixList * DiseaseParameters['InterventionMobilityEffect'] #[j * .5 for j in LocalInteractionMatrixList]
                LocalInteractionMatrixListINT[LocalPopulationId] = LocalInteractionMatrixList[LocalPopulationId]
                listsum = sum(LocalInteractionMatrixListINT)
                NormalizedLocalInteractionMatrixListINT = LocalInteractionMatrixListINT / listsum
                InfLocalPopulationId = Utils.multinomial(NormalizedLocalInteractionMatrixListINT, 1)
            else:
                InfLocalPopulationId = Utils.multinomial(LocalInteractionMatrixList, 1)

            InfRegionId = RegionListGuide[InfLocalPopulationId]
            if LocalPopulationId != InfLocalPopulationId:
                events.append(SimEvent.NonLocalInfectionEvent(t, InfRegionId,
                                                              InfLocalPopulationId, ageCohort,HouseholdId, PersonId,RegionListGuide[LocalPopulationId], LocalPopulationId))
                InfectionsDict['NonLocalInfections']+=1
                InfectionsDict['NonLocalRegionsInfected'].append(InfRegionId)
                InfectionsDict['NonLocalPopsInfected'].append(InfLocalPopulationId)
            else:
                events.append(SimEvent.LocalInfectionEvent(t, ageCohort,HouseholdId, PersonId))
                InfectionsDict['LocalInfections']+=1
                
    return events,InfectionsDict
