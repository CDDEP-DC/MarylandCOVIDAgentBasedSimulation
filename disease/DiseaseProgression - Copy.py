# -----------------------------------------------------------------------------
# DiseaseProgression.py contains all disease-specific events
# -----------------------------------------------------------------------------
from random import gammavariate, random
import ParameterSet
import numpy as np
import Utils
import events.SimulationEvent as SimEvent
import math


def TransProb(t,TP,DiseaseParameters):
    if 'seasonality' in DiseaseParameters['Intervention']:
        TP = (-1*math.sin(2*math.pi/365*(t-121.75)))*TP*.5+TP*.55
    return TP

def calcIntRegTime(start,end,intStart,IntEnd):
    if intStart > 0:
        if start > IntEnd or end < intStart:
            regtime = end - start
            inttime = 0
        elif start > intStart and end < IntEnd:
            inttime = end - start
            regtime = 0
        else:
            if start < intStart and end < IntEnd:
                regtime = intStart - start
                inttime = end - intStart
            elif start < intStart and end > IntEnd:
                regtime = (intStart - start) + (end - IntEnd)
                inttime = IntEnd - intStart
            elif start > intStart and end > IntEnd:
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
    
def SetupTransmissableContactEvents(timeNow,DiseaseParameters, LocalInteractionMatrixList, RegionListGuide,
                                    HouseholdId, PersonId, LocalPopulationId,
                                    contactRate, householdcontactRate,
                                    ageCohort,areAllHouseholdMembersInfected,
                                    HospitalTransitionMatrixList,HHSize):
                                    
        # Set the incupbation time
        queueEvents = []
        incubationTime = gammavariate(DiseaseParameters['IncubationTime'], 1)
               
        RegTransProb = DiseaseParameters['ProbabilityOfTransmissionPerContact']
                    
        IntTransProb = RegTransProb
        
        intStart = DiseaseParameters['InterventionDate']
        IntEnd  = DiseaseParameters['InterventionEndDate']
        if ageCohort <= 1:
            if DiseaseParameters['SchoolInterventionDate'] > 0:    
                IntTransProb = RegTransProb * DiseaseParameters['InterventionReductionSchool']
                intStart = DiseaseParameters['SchoolInterventionDate']
                IntEnd  = DiseaseParameters['SchoolInterventionEndDate']
        else:       
            if DiseaseParameters['InterventionDate'] > 0:
                if DiseaseParameters['InterventionReduction2'] < 1 and DiseaseParameters['InterventionReduction2'] > 0:
                    if contactRate > 24:
                        IntTransProb = RegTransProb * DiseaseParameters['InterventionReduction2']
                else:
                    IntTransProb = RegTransProb * DiseaseParameters['InterventionReduction']
            
        #print(contactRate, " ",RegTransProb, " ",IntTransProb," ", RegTransProb ," ", timeNow, " ", DiseaseParameters['InterventionDate'], " " ,ParameterSet.SeasonalityStart )
        
            
        ### Add event for when the patient becomes contagious pre symptoms
        SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime, HouseholdId, PersonId, ParameterSet.Contagious)
        queueEvents.append(SE)
        preContagiousTime = gammavariate(DiseaseParameters['preContagiousTime'], 1)
        postContagiousTime = 0
        # Symptomatic
        #testinfrate = 0
        if random() > DiseaseParameters['AGAsymptomaticRate'][ageCohort]:
            # Set the time they become symptomatic == incubationTime + the time they were contagious before symptoms
            SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime, HouseholdId, PersonId, ParameterSet.Symptomatic)
            queueEvents.append(SE)                
            
            #Get the amount of time they are symptomatic
            symptomaticTime = gammavariate(DiseaseParameters['symptomaticTime'], 1)
            
            # selecting the hospital they went to for both inpatient/ED
            if len(HospitalTransitionMatrixList) > 0:
                Hospital = Utils.multinomial(HospitalTransitionMatrixList, 1)
            else:
                Hospital = 0
                

            ## Did they go to the hospital?
            if random() < DiseaseParameters['AGHospRate'][ageCohort]:
                #Decide the time they go to hospital as many will go to the ED
                numtries = 0
                hospTime = gammavariate(DiseaseParameters['hospTime'], 1)
                while hospTime > symptomaticTime:
                    hospTime = gammavariate(DiseaseParameters['hospTime'], 1)
                    symptomaticTime+=1
                if random() < DiseaseParameters['ICURate']:
                    # If they went to the hospital and are hospitalized, their recovery is longer, so we add hospital time here
                    ICUTime = gammavariate(DiseaseParameters['ICUtime'],1)
                    PostICUTime = gammavariate(DiseaseParameters['PostICUTime'], 1)
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
                    symptomaticTime += gammavariate(DiseaseParameters['hospitalSymptomaticTime'], 1)
                        
                    # Set the time during syptoms at which they go to hospital    
                    SE = SimEvent.PersonHospCritEvent(timeNow+incubationTime+preContagiousTime+hospTime, HouseholdId, PersonId, Hospital)
                    queueEvents.append(SE)                
                    
                if random() < DiseaseParameters['AGMortalityRate'][ageCohort]:
                    SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime, HouseholdId, PersonId, ParameterSet.Dead)
                else:
                    SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime, HouseholdId, PersonId, ParameterSet.Recovered)
                queueEvents.append(SE)
                
                
                # Add Symptomatic Infections pre Hospital
                symptomaticRegularTime,symptomaticInterventionTime = calcIntRegTime(timeNow+incubationTime+preContagiousTime,timeNow+incubationTime+preContagiousTime+hospTime,intStart,IntEnd)
                    
                numRandInf = np.random.poisson(DiseaseParameters['hospitalSymptomaticContactRateReduction'] *
                                    contactRate * symptomaticRegularTime * TransProb(timeNow+incubationTime+preContagiousTime,RegTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime, symptomaticRegularTime,0, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
                numRandInf = np.random.poisson(DiseaseParameters['hospitalSymptomaticContactRateReduction'] *
                                    contactRate * symptomaticInterventionTime * TransProb(timeNow+incubationTime+preContagiousTime,IntTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticRegularTime, symptomaticInterventionTime,1, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
                
                # Add Symptomatic Infections in Hospital
                symptomaticRegularTime,symptomaticInterventionTime = calcIntRegTime(timeNow+incubationTime+preContagiousTime+hospTime,timeNow+incubationTime+preContagiousTime+hospTime+symptomaticTime,intStart,IntEnd)
                    
                numRandInf = np.random.poisson(DiseaseParameters['hospitalSymptomaticContactRateReduction'] *
                                    contactRate * symptomaticRegularTime * TransProb(timeNow+incubationTime+preContagiousTime+hospTime,RegTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+hospTime, symptomaticRegularTime,0, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
                numRandInf = np.random.poisson(DiseaseParameters['hospitalSymptomaticContactRateReduction'] *
                                    contactRate * symptomaticInterventionTime * TransProb(timeNow+incubationTime+preContagiousTime+hospTime,IntTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+hospTime+symptomaticRegularTime, symptomaticInterventionTime,1, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
            else:

                # If they didn't get admitted to hospital, length of symptoms is lower, but we assume some proportion of them present to the ED
                #-- commented out for the moment
                #if random() < DiseaseParameters['EDVisit']:
                    # If they go to ed then we get time of ED visit
                #    numtries = 0
                #    hospTime = gammavariate(DiseaseParameters['hospTime'], 1)
                #    while hospTime > symptomaticTime:
                #        symptomaticTime+=1
                #    SE = SimEvent.PersonHospEDEvent(timeNow+incubationTime+preContagiousTime+hospTime, HouseholdId, PersonId, Hospital)
                #    queueEvents.append(SE)
                
                # Add Symptomatic Infections
                symptomaticRegularTime,symptomaticInterventionTime = calcIntRegTime(timeNow+incubationTime+preContagiousTime,timeNow+incubationTime+preContagiousTime+symptomaticTime,intStart,IntEnd)
                if symptomaticRegularTime < 0 or symptomaticInterventionTime < 0:
                    print(timeNow+incubationTime+preContagiousTime," ",timeNow+incubationTime+preContagiousTime+symptomaticTime)
                    print(symptomaticRegularTime, " ",symptomaticInterventionTime)
                    
                numRandInf = np.random.poisson(DiseaseParameters['symptomaticContactRateReduction'] *
                                    contactRate * symptomaticRegularTime * TransProb(timeNow+incubationTime+preContagiousTime,RegTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime, symptomaticRegularTime,0, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
                numRandInf = np.random.poisson(DiseaseParameters['symptomaticContactRateReduction'] *
                                    contactRate * symptomaticInterventionTime * TransProb(timeNow+incubationTime+preContagiousTime,IntTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticRegularTime, symptomaticInterventionTime,1, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
                    
                # but we add conversion back to contagious before recovery
                preContagiousTime
                SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime, HouseholdId, PersonId, ParameterSet.Contagious)
                queueEvents.append(SE)
                
                postContagiousTime = gammavariate(DiseaseParameters['postContagiousTime'], 1)
                SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+preContagiousTime+symptomaticTime+postContagiousTime, HouseholdId, PersonId, ParameterSet.Recovered)
                queueEvents.append(SE)

                # Add Postcontagious Infections
                postContagiousRegularTime,postContagiousInterventionTime = calcIntRegTime(timeNow+incubationTime+preContagiousTime+symptomaticTime,timeNow+incubationTime+preContagiousTime+symptomaticTime+postContagiousTime,intStart,IntEnd)
                
                numRandInf = np.random.poisson(contactRate * postContagiousRegularTime * TransProb(timeNow+incubationTime+preContagiousTime+symptomaticTime,RegTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random                
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticTime, postContagiousRegularTime,0, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
                
                numRandInf = np.random.poisson(contactRate * postContagiousInterventionTime * TransProb(timeNow+incubationTime+preContagiousTime+symptomaticTime,IntTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
                SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                             LocalPopulationId, ageCohort, incubationTime+preContagiousTime+symptomaticTime+postContagiousRegularTime, postContagiousInterventionTime,1, DiseaseParameters)
                if numRandInf > 0: queueEvents.extend(SE)
            
                
            # Add Precontagious Infections
            preContagiousRegularTime,preContagiousInterventionTime = calcIntRegTime(timeNow+incubationTime,timeNow+incubationTime+preContagiousTime,intStart,IntEnd)
            numRandInf = np.random.poisson(contactRate * preContagiousRegularTime * TransProb(timeNow+incubationTime,RegTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime, preContagiousRegularTime,0, DiseaseParameters)
            if numRandInf > 0: queueEvents.extend(SE)
            numRandInf = np.random.poisson(contactRate * preContagiousInterventionTime * TransProb(timeNow+incubationTime,IntTransProb,DiseaseParameters), 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime+preContagiousRegularTime, preContagiousInterventionTime,1, DiseaseParameters)
            if numRandInf > 0: queueEvents.extend(SE)
            
         
            # Now infect household members
            if not areAllHouseholdMembersInfected:
                ContagiousTime = gammavariate(preContagiousTime+symptomaticTime, 1)
                numHHInf = np.random.poisson(householdcontactRate * ContagiousTime * RegTransProb, 1)[0]  ### this isn't good to be switching between numpy and random
                if numHHInf > 0: 
                    for i in range(numHHInf):
                        SE = SimEvent.HouseholdInfectionEvent(timeNow, HouseholdId, PersonId)
                        queueEvents.append(SE)
                        if i > HHSize:
                            break;
        # Asymptomatic
        else:
            ContagiousTime = gammavariate(DiseaseParameters['mildContagiousTime'], 1)
            SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime, HouseholdId, PersonId, ParameterSet.Contagious)
            queueEvents.append(SE)
            SE = SimEvent.PersonStatusUpdate(timeNow+incubationTime+ContagiousTime, HouseholdId, PersonId, ParameterSet.Recovered)
            queueEvents.append(SE)
            
            ContagiousRegularTime,ContagiousInterventionTime = calcIntRegTime(timeNow+incubationTime,timeNow+incubationTime+ContagiousTime,intStart,IntEnd)
            
            numRandInf = np.random.poisson(contactRate * ContagiousRegularTime * TransProb(timeNow+incubationTime,RegTransProb,DiseaseParameters)*DiseaseParameters['AsymptomaticReducationTrans'], 1)[0]  ### this isn't good to be switching between numpy and random
            
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime, ContagiousRegularTime,0, DiseaseParameters)
            if numRandInf > 0: queueEvents.extend(SE)
            numRandInf = np.random.poisson(contactRate * ContagiousInterventionTime * TransProb(timeNow+incubationTime,IntTransProb,DiseaseParameters)*DiseaseParameters['AsymptomaticReducationTrans'], 1)[0]  ### this isn't good to be switching between numpy and random
            SE = createInfectionEvents(numRandInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, incubationTime+ContagiousRegularTime, ContagiousInterventionTime,1, DiseaseParameters)
            
            if numRandInf > 0: queueEvents.extend(SE)
            
            
            # Now infect household members
            if not areAllHouseholdMembersInfected:
                ContagiousTime = gammavariate(DiseaseParameters['mildContagiousTime'], 1)
                numHHInf = np.random.poisson(householdcontactRate * ContagiousTime * RegTransProb, 1)[0]  ### this isn't good to be switching between numpy and random
                if numHHInf > 0: 
                    for i in range(numHHInf):
                        SE = SimEvent.HouseholdInfectionEvent(timeNow, HouseholdId, PersonId)
                        queueEvents.append(SE)
                        if i > HHSize:
                            break;
        

        return queueEvents


def createInfectionEvents(numInf, timeNow, LocalInteractionMatrixList, RegionListGuide,
                         LocalPopulationId, ageCohort, preTime, ContagiousTime, intervention, DiseaseParameters):
    
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
                events.append(SimEvent.NonLocalInfectionEvent(timeNow + t, InfRegionId,
                                                              InfLocalPopulationId, ageCohort))
                
            else:
                events.append(SimEvent.LocalInfectionEvent(timeNow + t, ageCohort))

    return events
