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

import multiprocessing as mp

from queue import Empty, Full
import logging
import signal
import functools
import sys, getopt
import time
import math
import os
import random
import numpy as np
from datetime import datetime  
from datetime import timedelta 
import traceback

import Region
import Utils
import ParameterSet
import GBQueue
import ProcWorker

    
class Proc:
    STARTUP_WAIT_SECS = 3.0
    SHUTDOWN_WAIT_SECS = 3.0
    
    def __init__(self, name, shutdown_event, event_q, reply_q,
                    PopulationParameters,DiseaseParameters,endTime,RegionalLocations,
                    RegionInteractionMatrixList,RegionListGuide,modelPopNames,
                    HospitalTransitionMatrix,mprandomseed,eventqueues, *args):
        self.name = name
        self.shutdown_event = shutdown_event
        self.startup_event = mp.Event()
        self.proc = mp.Process(target=ProcWorker.proc_worker_wrapper,
                               args=(name, self.startup_event, shutdown_event, event_q, reply_q,
                               PopulationParameters,DiseaseParameters,endTime,RegionalLocations,
                               RegionInteractionMatrixList,RegionListGuide,modelPopNames,
                               HospitalTransitionMatrix,mprandomseed,eventqueues, *args))
        self.proc.start()
        started = self.startup_event.wait(timeout=Proc.STARTUP_WAIT_SECS)
        self.log(logging.DEBUG, f"Proc.__init__ starting : {name} got {started}")
        if not started:
            self.terminate()
            raise RuntimeError(f"Process failed to start")

    def full_stop(self, wait_time=SHUTDOWN_WAIT_SECS):
        self.log(logging.DEBUG, f"Proc.full_stop stopping : {self.name}")
        self.shutdown_event.set()
        self.proc.join(wait_time)
        if self.proc.is_alive():
            self.terminate()

    def terminate(self):
        self.log(logging.DEBUG, f"Proc.terminate terminating : {self.name}")
        NUM_TRIES = 3
        tries = NUM_TRIES
        while tries and self.proc.is_alive():
            self.proc.terminate()
            time.sleep(0.01)
            tries -= 1

        if self.proc.is_alive():
            self.log(logging.ERROR, f"Proc.terminate failed to terminate {self.name} after {NUM_TRIES} attempts")
            return False
        else:
            self.log(logging.INFO, f"Proc.terminate terminated {self.name} after {NUM_TRIES - tries} attempt(s)")
            return True

    def log(self,logtype,logval):
        if ParameterSet.logginglevel == 'debug':
            #print(logval)
            pass
        elif ParameterSet.logginglevel == 'error':
            if logtype == logging.ERROR:
                print(logval)
                Utils.WriteLogFile(os.path.join(ParameterSet.ResultsFolder,str(self.name)+"ERROR.txt"),logval)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.full_stop()
        return not exc_type
        

def RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,
                LocationImportationRisk,PopulationParameters,DiseaseParameters,
                endTime,resultsName,mprandomseed,
                startDate=datetime(2020,2,22),stepLength=1,numregions=-1,
                modelPopNames='zipcodes',fitdates=[],hospitalizations=[],deaths=[],fitper=.3):

    print("Starting Run")
    fitted = True
    RegionalList = []
    # set the time of the simulation
    timeNow = 0
    timeRange = []
    
    while timeNow < endTime:
        timeNow = timeNow + stepLength
        timeRange.append(timeNow)
        
    try:
    
        MAX_PROCESS_WAIT_SECS = 600.0
        num_regions = mp.cpu_count() * 2
        
        if numregions > 0:
            num_regions = numregions
            
        if num_regions > len(GlobalLocations):
            num_regions = len(GlobalLocations)
            
        # define the shutdown event
        shutdown_event = mp.Event()
        
        # Response queue for getting results back out
        responseq = GBQueue.MPQueue()
        
        poptotals = {}
        poptotal = 0
        for i in range(0,len(GlobalLocations)):
            poptotal += GlobalLocations[i].populationAmt
        
        RegionInteractionMatrixList = []
        RegionalLocations = []
    
        RegionListGuide = []
        HospitalTransitionMatrix = []
        i = 0
        for R in range(0,num_regions):
            popinR = 0
            tempR = []
            tempL = []
            tempH = []
            while popinR < math.ceil(poptotal/num_regions) and i <= (len(GlobalLocations)-1):
                popinR += GlobalLocations[i].populationAmt
                tempR.append(GlobalInteractionMatrix[i,:])
                tempL.append(GlobalLocations[i])
                if(len(HospitalTransitionRate) == len(GlobalInteractionMatrix)):
                    tempH.append(HospitalTransitionRate[i,:])   
                RegionListGuide.append(R)
                i+=1
            RegionalList.append(R)
            RegionInteractionMatrixList.append(tempR)
            RegionalLocations.append(tempL)
            if(len(HospitalTransitionRate) == len(GlobalInteractionMatrix)):
                HospitalTransitionMatrix.append(tempH) 
        
        # set up the procs for each region
        procs = []
        eventqueues = []
        for i in range(0,num_regions):
            mpq = GBQueue.MPQueue()
            eventqueues.append(mpq)
            
        for i in range(0,num_regions):
            proc = Proc(i, shutdown_event,eventqueues[i], responseq, PopulationParameters,
                        DiseaseParameters,endTime,RegionalLocations[i],RegionInteractionMatrixList[i],
                        RegionListGuide,modelPopNames,HospitalTransitionMatrix[i],mprandomseed,eventqueues)
            procs.append(proc)
                    
        
              
        results = {}
        numInfList = {}
        
        
        lpvalslastdate = DiseaseParameters['QuarantineStartDate']
        InfPrior = 1
        HosPrior = 1  
          
        numFitDeaths = []
        numFitHospitalizations = []
        for tend in timeRange:
        
            infect = [0]*len(RegionalList)
            LPIDinfect = -1
            
            if len(LocationImportationRisk) > 0:
                LPIDinfect = Utils.multinomial(LocationImportationRisk,sum(LocationImportationRisk))
                rnum = RegionListGuide[LPIDinfect]
            else:
                rnum = random.choice(RegionalList)
            infect[rnum] = DiseaseParameters['ImportationRate']
    
                
            offPopQueueEvents = []
            fithospitalizations = 0
            fitdeaths = 0
            try:
                for i in range(0,len(RegionalList)):
                    procdict = {}
                    procdict['tend'] = tend
                    procdict['infectNumAgents'] = infect[i]
                    procdict['LPIDinfect'] = LPIDinfect
                    eventqueues[i].safe_put(GBQueue.EventMessage("main", "startevent", procdict))
                allprocsdone = False
                doneprocs = [0]*len(RegionalList)
                
                MAX_PROCESS_WAIT_SECS = 600.0
                tstart = time.time()
                while not allprocsdone:
                    item = responseq.safe_get()
                    if not item:
                        t2 = time.time()
                        if (t2 - tstart) > MAX_PROCESS_WAIT_SECS:
                            endRun(procs, eventqueues)
                            exit()
                        continue
                    else:
                        #print(f"MainWorker.main_loop received '{item}' message")
                        if item.msg_type == "finishedrun":
                            doneprocs[item.msg_src] = 1
                            fitval = item.msg
                            fithospitalizations += fitval[0]
                            fitdeaths += fitval[1]
                            
                        if item.msg_type == "offPopQueueEvent":
                            offPopQueueEvents.append(item.msg)        
                        
                        if item.msg_type == "FATAL":
                            endRun(procs, eventqueues)
                            for i in range(0,1000):
                                item = responseq.safe_get()
                            responseq.drain()
                            responseq.safe_close()
                            time.sleep(2) ## add here to let all the procs exit
                            exit()
                                                    
                        if sum(doneprocs) == len(RegionalList):
                            allprocsdone = True
                            break
            except BaseException as exc:
                # -- Catch ALL exceptions, even Terminate and Keyboard interrupt
                #self.log(logging.ERROR, f"Exception Shutdown: {exc}", exc_info=True)
                print("Model run error:")
                print(traceback.format_exc())
                print(f"Run Exception Shutdown: {exc}")
                responseq.drain()
                responseq.safe_close()
                if type(exc) in (ProcWorker.TerminateInterrupt, KeyboardInterrupt):
                    raise Exception("Known error while running models")
                else:
                    raise Exception("UNKNOWN error while running models")
                
            # This does the fitting process if fitting values are enabled and passed in
            numFitDeaths.append(fitdeaths)
            numFitHospitalizations.append(fithospitalizations)
            #print(tend,fitval,max(fitvals))
            if (len(hospitalizations) > 0 or len(deaths) > 0) and tend > min(fitdates) and tend < max(fitdates):
                if ParameterSet.FitValue == 'hospitalizations' or ParameterSet.FitValue == 'both':
                    if fithospitalizations > max(hospitalizations)*3:
                        print("Run did not fit hospitalizations ... exiting")
                        fitted = False
                        break
                if ParameterSet.FitValue == 'deaths' or ParameterSet.FitValue == 'both':
                    if fitdeaths > max(deaths)*3:
                        print("Run did not fit deaths ... exiting")
                        fitted = False
                        break
            if ParameterSet.FitValue == 'hospitalizations' or ParameterSet.FitValue == 'both':
                if len(hospitalizations) > 0 and tend == max(fitdates):
                    fitpervals = 0
                    f = 0
                    for x in range(min(fitdates),max(fitdates)):
                        fitpervals += abs((numFitHospitalizations[x]-hospitalizations[f])/numFitHospitalizations[x])*(f+1)
                        if ParameterSet.logginglevel == 'debug' or ParameterSet.logginglevel == 'error':
                            print(numFitHospitalizations[x],hospitalizations[f],abs((numFitHospitalizations[x]-hospitalizations[f])/numFitHospitalizations[x]))
                        f += 1
                    N=len(hospitalizations)
                    avgperdiff = fitpervals / (N+(N-1)*N/2)
                    if ParameterSet.logginglevel == 'debug' or ParameterSet.logginglevel == 'error':
                        print(fitpervals,len(hospitalizations),avgperdiff)
                    if avgperdiff > fitper:
                        print("Run did not fit hospitalizations ... exiting")
                        fitted = False
                        break
                    else:
                        print("Run fit Hospitalizations!")
            if ParameterSet.FitValue == 'deaths' or ParameterSet.FitValue == 'both':
                if len(deaths) > 0 and tend == max(fitdates):
                    fitpervals = 0
                    f = 0
                    for x in range(min(fitdates),max(fitdates)):
                        fitpervals += abs((numFitDeaths[x]-deaths[f])/numFitDeaths[x])*(f+1)
                        if ParameterSet.logginglevel == 'debug' or ParameterSet.logginglevel == 'error':
                            print(numFitDeaths[x],deaths[f],abs((numFitDeaths[x]-deaths[f])/numFitDeaths[x]))
                        f += 1
                    N=len(deaths)
                    avgperdiff = fitpervals / (N+(N-1)*N/2)
                    if ParameterSet.logginglevel == 'debug' or ParameterSet.logginglevel == 'error':
                        print(fitpervals,len(deaths),avgperdiff)
                    if avgperdiff > fitper:
                        print("Run did not fit deaths ... exiting")
                        fitted = False
                        break
                    else:
                        print("Run fit deaths!")            
                    
            ## Get all the Reconcilliation events
            try:
                if ParameterSet.UseQueuesForQueues:
                    for QE in offPopQueueEvents:
                        Rid = QE.RegionId
                        eventqueues[Rid].safe_put(EventMessage("main", "offPopQueueEvent", QE))
                    offPopQueueEvents.clear()
                    
                else:
                    RegionReconciliationEvents = {} 
                    testRegionValues = {} 
                    for i in range(0,len(RegionalList)):
                        testRegionValues[i] = 0
                        RegionReconciliationEvents[i] = []
                        
                    # Now get the off-pop queues
                    for i in range(0,len(RegionalList)):
                        testRegionValues[i] = 0
                        RegionReconciliationEvents[i] = []
                        try:
                            OPQE = Utils.PickleFileRead(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"))
                        except:
                           OPQE = None 
                        if OPQE:
                            offPopQueueEvents.extend(OPQE)
                        try:
                            os.remove(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"))
                        except:
                            pass
                
                    for QE in offPopQueueEvents:
                        Rid = QE.RegionId
                        testRegionValues[Rid]+=1
                        RegionReconciliationEvents[Rid].append(QE) 
                    offPopQueueEvents.clear()    
                    
                    for i in range(0,len(RegionalList)):
                        if testRegionValues[i] > 0:
                            Utils.PickleFileWrite(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"), RegionReconciliationEvents[i])
                            
            except BaseException as exc:
                # -- Catch ALL exceptions, even Terminate and Keyboard interrupt
                #self.log(logging.ERROR, f"Exception Shutdown: {exc}", exc_info=True)
                print(f"Reconcilining Exception Shutdown: {exc}")
                responseq.drain()
                responseq.safe_close()
                if type(exc) in (ProcWorker.TerminateInterrupt, KeyboardInterrupt):
                    raise Exception("Known error while reconciling queues")
                else:
                    raise Exception("UNKNOWN error while reconciling queues")
                
            
                
            if ParameterSet.logginglevel == 'debug':
                InfPrior, HosPrior = printCurrentState(tend,RegionalList,modelPopNames,startDate,InfPrior,HosPrior)
                
        endRun(procs,eventqueues)       
    
        print("Finished run")
    except BaseException as exc:
            # -- Catch ALL exceptions, even Terminate and Keyboard interrupt
            #self.log(logging.ERROR, f"Exception Shutdown: {exc}", exc_info=True)
            print(f"Exception Shutdown: {exc}")
            endRun(procs, eventqueues)
            if type(exc) in (ProcWorker.TerminateInterrupt, KeyboardInterrupt):
                sys.exit(1)
            else:
                sys.exit(2)
        
    return RegionalList, timeRange, fitted
        
def printCurrentState(tend,RegionalList,modelPopNames,startDate,InfPrior,HosPrior):

    numInfList = {}
    for i in range(0,len(RegionalList)):
        numinfVals = Utils.PickleFileRead(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"))
        for key in numinfVals.keys():
            numInfList[key] = numinfVals[key]
        
    totInf = 0
    totC = 0
    totH = 0
    totN = 0
    totR = 0
    totD = 0
    totS = 0
    totHI = 0
    totHE = 0
    totHMD = 0
    totDMD = 0
    x = 0
    totICU = 0
    numQ = 0
    numInfPrev = 0
    InfEvtClear = 0
    numTests = 0
    confirmedcases = 0
    
    #sorted_d = sorted((value, key) for (key,value) in SortCol.items())
    
    lpvals = {}
    
    for key in numInfList.keys():
        rdict = numInfList[key]
        for rkey in rdict:
            lpdict = rdict[rkey]
            if len(lpdict) > 0:
                totInf += lpdict['I']
                totC += lpdict['C']
                totH += lpdict['H']
                totICU += lpdict['ICU']
                totN += lpdict['N']
                totR += lpdict['R']
                totD += lpdict['D']
                totS += lpdict['S']
                totHI += lpdict['HI']
                totHE += lpdict['HE']
                if lpdict['regionalid'] == 'MD':
                    totHMD += lpdict['H']  
                    totDMD += lpdict['D']  
                    lpvals[rkey]=lpdict['C']+lpdict['I']
                numQ += lpdict['numQ']
                numInfPrev += lpdict['numInfPrev']
                InfEvtClear += lpdict['InfEvtClear']
                numTests += lpdict['numTests']
                confirmedcases += lpdict['CC']
    x = startDate + timedelta(days=tend) 
    
    #print("End:",tend," (",(x.strftime('%Y-%m-%d')),") Time:",t3-t1,"(",t3-t2,") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," NumC:",totC," numR:",totR," numD:",totD," numH:",totH," R0:",round(R0,2)," R0R:",round(R0R,2)," R0HH:",round(R0HH,2)," HI:",totHI," HE:",totHE)
    
    
    rnumer = 0
    rdenom = 0
    
    if ParameterSet.FitMD:
        print("End:",tend," (",(x.strftime('%Y-%m-%d')),") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," (" + str(round(totInf / InfPrior,3)) +") NumC:",totC," numR:",totR," numDMD:",totDMD," numHMD:",totHMD,"(" ,str(round(totHMD/HosPrior,3)),") cases:",confirmedcases," (",numTests,") Q:",numQ," (",numInfPrev,",",InfEvtClear,")")
    else:
        if ParameterSet.FitValue == 'hospitalizations':
            print("End:",tend," (",(x.strftime('%Y-%m-%d')),") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," (" + str(round(totInf / InfPrior,3)) +") NumC:",totC," numR:",totR," numH:",totH," cases:",confirmedcases," (",numTests,") Q:",numQ," (",numInfPrev,",",InfEvtClear,")")
        else:
            print("End:",tend," (",(x.strftime('%Y-%m-%d')),") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," (" + str(round(totInf / InfPrior,3)) +") NumC:",totC," numR:",totR," numD:",totD," cases:",confirmedcases," (",numTests,") Q:",numQ," (",numInfPrev,",",InfEvtClear,")")
    if totInf > 0:
        InfPrior = totInf
    if totHMD > 0:
        HosPrior = totHMD
                   
    return InfPrior, HosPrior 
    #if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):
    #    results = Utils.PickleFileRead(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))
    #results[tend] = numInfList
    #Utils.PickleFileWrite(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"),results)

    
def endRun(procs,eventqueues):
    for i in range(0,len(procs)):
        eventqueues[i].safe_put(GBQueue.EventMessage("stop_procs", "END", "END"))
    
    for i in range(0,len(procs)):
        procs[i].shutdown_event.set()
    
    for i in range(0,len(procs)):
        procs[i].full_stop()

