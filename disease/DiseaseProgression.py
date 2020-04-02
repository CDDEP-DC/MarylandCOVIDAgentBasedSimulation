# -----------------------------------------------------------------------------
# DiseaseProgression.py contains all disease-specific events
# -----------------------------------------------------------------------------
from random import gammavariate, random
import ParameterSet
import numpy as np
import Utils
import events.SimulationEvent as SimEvent
import math


def TransProb(t,TP):
    if ParameterSet.Intervention == 'seasonality':
        TP = (-1 * math.sin(2*math.pi/365*(t-91.75)))*.01+.017
    if ParameterSet.Intervention == 'seasonality2':    
        TP = (-1 * math.sin(2*math.pi/365*(t-91.75)))*0.005+.017
    return TP

def SetupTransmissableContactEvents(timeNow, LocalInteractionMatrixList, RegionListGuide,
                                    HouseholdId, PersonId, LocalPopulationId,
                                    contactRate, householdcontactRate,
                                    ageCohort,areAllHouseholdMembersInfected,
                                    HospitalTransitionMatrixList,HHSize):
                                    
        # Set the incupbation time
        queueEvents = []
        incubationTime = gammavariate(ParameterSet.IncubationTime, 1)
               
        RegTransProb = ParameterSet.ProbabilityOfTransmissionPerContact
                    
        #print(HouseholdId," ", PersonId)
        #if ParameterSet.Intervention == 'seasonality' or ParameterSet.Intervention == 'seasonality2':
            #if timeNow > ParameterSet.SeasonalityStart:
            #    if ParameterSet.Intervention == 'seasonality2':
            #        RegTransProb = RegTransProb * ParameterSet.SeasonalityReduction2 ** (timeNow-ParameterSet.SeasonalityStart)    
            #    else:
            #        RegTransProb = RegTransProb * ParameterSet.SeasonalityReduction ** (timeNow-ParameterSet.SeasonalityStart)    
                    
        IntTransProb = RegTransProb
        
        if ParameterSet.InterventionDate > 0:
            if timeNow > ParameterSet.InterventionDate and timeNow < ParameterSet.InterventionEndDate:
                if ageCohort <= 1:
                    IntTransProb = RegTransProb * ParameterSet.InterventionReductionSchool
                else:
                    if ParameterSet.InterventionReduction2 == 1:
                        if contactRate > 24:
                            IntTransProb = RegTransProb * .6
                    else:
                        IntTransProb = RegTransProb * ParameterSet.InterventionReduction
        #print(contactRate, " ",RegTransProb, " ",IntTransProb," ", RegTransProb ," ", timeNow, " ", ParameterSet.InterventionDate, " " ,ParameterSet.SeasonalityStart )
        
        ### Add event for when the patient becomes contagious pre symptoms
        SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime, HouseholdId, PersonId, ParameterSet.Contagious)
        queueEvents.append(SE)
        
        # Symptomatic
        #testinfrate = 0
        if random() > ParameterSet.AGAsymptomaticRate[ageCohort]:
            # Set the time they become symptomatic == incubationTime + the time they were contagious before symptoms
            preContagiousTime = gammavariate(ParameterSet.preContagiousTime, 1)
            SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime, HouseholdId, PersonId, ParameterSet.Symptomatic)
            queueEvents.append(SE)                
            
            #Get the amount of time they are symptomatic
            symptomaticTime = gammavariate(ParameterSet.symptomaticTime, 1)
            
            # Now determine if they need hospitalization
            hospcritrand = random()
            
            # selecting the hospital they went to for both inpatient/ED
            if len(HospitalTransitionMatrixList) > 0:
                Hospital = Utils.multinomial(HospitalTransitionMatrixList, 1)
            else:
                Hospital = 0
                

            ## Did they go to the hospital?
            if hospcritrand < ParameterSet.AGHospRate[ageCohort]:
                #Decide the time they go to hospital as many will go to the ED
                numtries = 0
                hospTime = gammavariate(ParameterSet.hospTime, 1)
                while hospTime > symptomaticTime:
                    hospTime = gammavariate(ParameterSet.hospTime, 1)
                    symptomaticTime+=1
                if random() < ParameterSet.ICURate:
                    # If they went to the hospital and are hospitalized, their recovery is longer, so we add hospital time here
                    ICUTime = gammavariate(ParameterSet.ICUtime,1)
                    PostICUTime = gammavariate(ParameterSet.PostICUTime, 1)
                    if PostICUTime == 0:
                        PostICUTime = 1
                    symptomaticTime += ICUTime + PostICUTime
                        
                    # Set the time during syptoms at which they go to hospital    
                    SE = SimEvent.PersonHospICUEvent(timeNow+incubationTime+preContagiousTime+hospTime, HouseholdId, PersonId, Hospital)
                    queueEvents.append(SE) 
                    
                    SE = SimEvent.PersonHospExitICUEvent(timeNow+incubationTime+preContagiousTime+hospTime+ICUTime, HouseholdId, PersonId, Hospital)
                    queueEvents.append(SE)                
                
                else:             
                    # If they went to the hospital and are hospitalized, their recovery is longer, so we add hospital time here
                    symptomaticTime += gammavariate(ParameterSet.hospitalSymptomaticTime, 1)
                        
                    # Set the time during syptoms at which they go to hospital    
                    SE = SimEvent.PersonHospCritEvent(timeNow+incubationTime+preContagiousTime+hospTime, HouseholdId, PersonId, Hospital)
                    queueEvents.append(SE)                
                    
                if hospcritrand < ParameterSet.AGMortalityRate[ageCohort]:
                    SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime, HouseholdId, PersonId, ParameterSet.Dead)
                else:
                    SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime, HouseholdId, PersonId, ParameterSet.Recovered)
                queueEvents.append(SE)
                
            else:

                # If they didn't get admitted to hospital, length of symptoms is lower, but we assume some proportion of them present to the ED
                if random() < ParameterSet.EDVisit:
                    # If they go to ed then we get time of ED visit
                    numtries = 0
                    hospTime = gammavariate(ParameterSet.hospTime, 1)
                    while hospTime > symptomaticTime:
                        symptomaticTime+=1
                    SE = SimEvent.PersonHospEDEvent(timeNow+incubationTime+preContagiousTime+hospTime, HouseholdId, PersonId, Hospital)
                    queueEvents.append(SE)
                
                # but we add conversion back to contagious before recovery
                SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime, HouseholdId, PersonId, ParameterSet.Contagious)
                queueEvents.append(SE)
                
                postContagiousTime = gammavariate(ParameterSet.postContagiousTime, 1)
                SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime+postContagiousTime, HouseholdId, PersonId, ParameterSet.Recovered)
                queueEvents.append(SE)

                # Add Postcontagious Infections
                if ParameterSet.InterventionDate > 0:
                    postContagiousRegularTime = max(postContagiousTime - max((timeNow+incubationTime+preContagiousTime+symptomaticTime+postContagiousTime) - ParameterSet.InterventionDate,0),0)
                else:
                    postContagiousRegularTime = postContagiousTime
                postContagiousInterventionTime = postContagiousTime - postContagiousRegularTime
 
                numRandInf = np.random.poisson(contactRate * postContagiousRegularTime * TransProb(timeNow+incubationTime+preContagiousTime+symptomaticTime,RegTransProb), 1)[0]  ### this isn't good to be switching between numpy and random
                
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticTime, postContagiousRegularTime)
                if numRandInf > 0: queueEvents.extend(SE)
                
                numRandInf = np.random.poisson(contactRate * postContagiousInterventionTime * TransProb(timeNow+incubationTime+preContagiousTime+symptomaticTime,IntTransProb), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticTime+postContagiousRegularTime, postContagiousInterventionTime)
                if numRandInf > 0: queueEvents.extend(SE)
            # End hospital part
                
            # Add Precontagious Infections
            if ParameterSet.InterventionDate > 0:
                preContagiousRegularTime = max(preContagiousTime - max((timeNow+incubationTime+preContagiousTime) - ParameterSet.InterventionDate,0),0)
            else:
                preContagiousRegularTime = preContagiousTime
            preContagiousInterventionTime = preContagiousTime - preContagiousRegularTime
            numRandInf = np.random.poisson(contactRate * preContagiousRegularTime * TransProb(timeNow+incubationTime,RegTransProb), 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime, preContagiousRegularTime)
            if numRandInf > 0: queueEvents.extend(SE)
            numRandInf = np.random.poisson(contactRate * preContagiousInterventionTime * TransProb(timeNow+incubationTime,IntTransProb), 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime+preContagiousRegularTime, preContagiousInterventionTime)
            if numRandInf > 0: queueEvents.extend(SE)
            
            # Add Symptomatic Infections
            if ParameterSet.InterventionDate > 0:
                symptomaticRegularTime = max(symptomaticTime - max((timeNow+incubationTime+preContagiousTime+symptomaticTime) - ParameterSet.InterventionDate,0),0)
            else:
                symptomaticRegularTime = symptomaticTime
            symptomaticInterventionTime = symptomaticTime - symptomaticRegularTime
            numRandInf = np.random.poisson(ParameterSet.symptomaticContactRateReduction *
                                contactRate * symptomaticRegularTime * TransProb(timeNow+incubationTime+preContagiousTime,RegTransProb), 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime+preContagiousTime, symptomaticRegularTime)
            if numRandInf > 0: queueEvents.extend(SE)
            numRandInf = np.random.poisson(ParameterSet.symptomaticContactRateReduction *
                                contactRate * symptomaticInterventionTime * TransProb(timeNow+incubationTime+preContagiousTime,IntTransProb), 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticRegularTime, symptomaticInterventionTime)
            if numRandInf > 0: queueEvents.extend(SE)
         
        # Asymptomatic
        else:
            ContagiousTime = gammavariate(ParameterSet.totalContagiousTime, 1)
            SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime, HouseholdId, PersonId, ParameterSet.Contagious)
            queueEvents.append(SE)
            SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+ContagiousTime, HouseholdId, PersonId, ParameterSet.Recovered)
            queueEvents.append(SE)
            
            if ParameterSet.InterventionDate > 0:
                ContagiousRegularTime = max(ContagiousTime - max((timeNow+incubationTime+ContagiousTime) - ParameterSet.InterventionDate,0),0)
            else:
                ContagiousRegularTime = ContagiousTime
            ContagiousInterventionTime = ContagiousTime - ContagiousRegularTime
            numRandInf = np.random.poisson(contactRate * ContagiousRegularTime * TransProb(timeNow+incubationTime,RegTransProb)*ParameterSet.AsymptomaticReducationTrans, 1)[0]  ### this isn't good to be switching between numpy and random
            
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime, ContagiousRegularTime)
            if numRandInf > 0: queueEvents.extend(SE)
            numRandInf = np.random.poisson(contactRate * ContagiousInterventionTime * TransProb(timeNow+incubationTime,IntTransProb)*ParameterSet.AsymptomaticReducationTrans, 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime+ContagiousRegularTime, ContagiousInterventionTime)
            if numRandInf > 0: queueEvents.extend(SE)
            
            
        # Now infect household members
        if not areAllHouseholdMembersInfected:
            ContagiousTime = gammavariate(ParameterSet.totalContagiousTime, 1)
            
            numHHInf = np.random.poisson(householdcontactRate * ContagiousTime * RegTransProb, 1)[0]  ### this isn't good to be switching between numpy and random
            if numHHInf > 0: 
                for i in range(numHHInf):
                    SE = SimEvent.HouseholdInfectionEvent(timeNow, HouseholdId, PersonId)
                    queueEvents.append(SE)
                    if i > HHSize:
                        break;
        

        return queueEvents


def createInfectionEvents(numInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, preTime, ContagiousTime):
    
    events = []
    for i in range(0, numInf):
        # get time frame of infection
        t = preTime + random() * ContagiousTime
        #Decide if it is in the local population or somewhere else
        InfLocalPopulationId = Utils.multinomial(LocalInteractionMatrixList, 1)
        InfRegionId = RegionListGuide[InfLocalPopulationId]
        if LocalPopulationId != InfLocalPopulationId:
            events.append(SimEvent.NonLocalInfectionEvent(timeNow + t, InfRegionId,
                                                          InfLocalPopulationId, ageCohort))
        else:
            events.append(SimEvent.LocalInfectionEvent(timeNow + t, ageCohort))

    return events
