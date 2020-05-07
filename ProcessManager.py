# -----------------------------------------------------------
# Main.py is the executable that runs the entire model
# -----------------------------------------------------------

import multiprocessing as mp
import multiprocessing.queues as mpq

from queue import Empty, Full
import logging
import signal
import functools
import sys, getopt
import time
import math
import os
from datetime import datetime  
from datetime import timedelta 

import Region
import Utils
import ParameterSet


def _sleep_secs(max_sleep, end_time=999999999999999.9):
    # Calculate time left to sleep, no less than 0
    return max(0.0, min(end_time - time.time(), max_sleep))

class TerminateInterrupt(BaseException):
    pass


class SignalObject:
    MAX_TERMINATE_CALLED = 3

    def __init__(self, shutdown_event):
        self.terminate_called = 0
        self.shutdown_event = shutdown_event


def default_signal_handler(signal_object, exception_class, signal_num, current_stack_frame):
    signal_object.terminate_called += 1
    signal_object.shutdown_event.set()
    if signal_object.terminate_called >= signal_object.MAX_TERMINATE_CALLED:
        raise exception_class()


def init_signal(signal_num, signal_object, exception_class, handler):
    handler = functools.partial(handler, signal_object, exception_class)
    signal.signal(signal_num, handler)
    signal.siginterrupt(signal_num, False)


def init_signals(shutdown_event, int_handler, term_handler):
    signal_object = SignalObject(shutdown_event)
    init_signal(signal.SIGINT, signal_object, KeyboardInterrupt, int_handler)
    init_signal(signal.SIGTERM, signal_object, TerminateInterrupt, term_handler)
    return signal_object

class ProcWorker:

    int_handler = staticmethod(default_signal_handler)
    term_handler = staticmethod(default_signal_handler)

    def __init__(self, name, startup_event, shutdown_event, event_q,reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix, *args):
        self.name = name
        #self.log = functools.partial(_logger, f'{self.name} Worker')
        self.startup_event = startup_event
        self.shutdown_event = shutdown_event
        self.event_q = event_q
        self.reply_q = reply_q
        self.terminate_called = 0
        self.modelPopNames = modelPopNames
        
        self.ProcRegion = Region.Region(RegionalLocations, RegionInteractionMatrixList, name, RegionListGuide,HospitalTransitionMatrix,PopulationParameters,DiseaseParameters,endTime)
  
    def log(self,logtype,logval):
        if ParameterSet.logginglevel == 'debug':
            print(logval)
        elif ParameterSet.logginglevel == 'error':
            if logtype == logging.ERROR:
                print(logval)
                Utils.WriteLogFile(os.path.join(ParameterSet.ResultsFolder,str(self.modelPopNames)+str(self.name)+"ERROR.txt"),logval)
        
    def init_signals(self):
        self.log(logging.DEBUG, str(self.name)+"Entering init_signals")
        signal_object = init_signals(self.shutdown_event, self.int_handler, self.term_handler)
        return signal_object

    def main_loop(self):
        self.log(logging.DEBUG, str(self.name)+"Entering main_loop")
        #self.main_func(1)
        while not self.shutdown_event.is_set():
            item = self.event_q.safe_get()
            #print("**",item,"**")
            if not item:
                continue
            else:
                #self.log(logging.DEBUG, f"QueueProcWorker.main_loop received '{item}' message")
                if item.msg_type == "END":
                    break
                else:
                    self.main_func(item.msg)
                    

    def startup(self):
        self.log(logging.DEBUG, str(self.name)+"Entering startup")
        pass

    def shutdown(self):
        self.log(logging.DEBUG, str(self.name)+"Entering shutdown")
        pass

    def main_func(self, procdict):
        
        #self.log(logging.DEBUG, str(self.name)+"Entering main_func")
        tend = procdict['tend']
        infectNumAgents = procdict['infectNumAgents']
        LPIDinfect = procdict['LPIDinfect']
        #print("do something here")
            
        ## need to add read from file
        try:
            RegionReconciliationEvents = Utils.PickleFileRead(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"))
        except:
           RegionReconciliationEvents = [] 
        try:
            os.remove(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"))
        except:
            pass
            #if(ParameterSet.debugmodelevel >= ParameterSet.debugnotimportant): print("ProcWorker:ReconcileEventsProcess():File Not Found for Removal: Queues/"+str(self.modelPopNames)+str(self.name)+"Queue.pickle")
            
        ## check for quarantine & testing files
        try:
            testlpzips = Utils.PickleFileRead(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"testextra.pickle"))
        except:
           testlpzips = [] 
            
        if len(RegionReconciliationEvents) > 0:
            self.ProcRegion.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
        
        infop = []
        if infectNumAgents > 0:
            infop = self.ProcRegion.infectRandomAgents(tend,infectNumAgents,LPIDinfect)
            
        regionStats, offPopQueueEvents, numEvents = self.ProcRegion.runTimePeriod(tend,testlpzips)
        
        if len(infop) > 0:
            offPopQueueEvents.extend(infop)
            
        regionStatsX = {}
        regionStatsX[self.name] = regionStats
            
        hospOccupancyList = self.ProcRegion.getHospitalOccupancy()
        
        R0Stats = self.ProcRegion.getR0Stats()
        R0StatsList = {}
        R0StatsList[self.name] = R0Stats
        
        LPAgeStats = self.ProcRegion.getAgeStats()
        AgeStatsList = {}
        AgeStatsList[self.name] = LPAgeStats

        Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"RegionStats.pickle"), regionStatsX)
                
        Utils.PickleFileWrite(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"), offPopQueueEvents)
        
        if os.path.exists(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"HOSPLIST.pickle")):
            CurrentHospOccList = Utils.PickleFileRead(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"HOSPLIST.pickle"))
        else:
            CurrentHospOccList = {}
        CurrentHospOccList[tend] = hospOccupancyList  
        Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"HOSPLIST.pickle"), CurrentHospOccList)
        Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"R0Stats.pickle"), R0StatsList)
        Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"AgeStats.pickle"), AgeStatsList)
        
        self.reply_q.safe_put(EventMessage(self.name, "finishedrun", tend))
        

    def run(self):
        self.init_signals()
        if ParameterSet.logginglevel == 'test':
            self.startup()
            self.startup_event.set()
            self.main_loop()
            self.log(logging.INFO, str(self.name)+"Normal Shutdown")
            #self.event_q.safe_put(EventMessage(self.name, "SHUTDOWN", "Normal"))
            return 0
        else:
            try:
                self.startup()
                self.startup_event.set()
                self.main_loop()
                self.log(logging.INFO, str(self.name)+"Normal Shutdown")
                #self.event_q.safe_put(EventMessage(self.name, "SHUTDOWN", "Normal"))
                return 0
            except BaseException as exc:
                # -- Catch ALL exceptions, even Terminate and Keyboard interrupt
                #self.log(logging.ERROR, f"Exception Shutdown: {exc}", exc_info=True)
                self.log(logging.ERROR, f"Exception Shutdown: {exc}")
                self.reply_q.safe_put(EventMessage(self.name, "FATAL", f"{exc}"))
                # -- TODO: call raise if in some sort of interactive mode
                if type(exc) in (TerminateInterrupt, KeyboardInterrupt):
                    sys.exit(1)
                else:
                    sys.exit(2)
            finally:
                self.shutdown()

def proc_worker_wrapper(name, startup_evt, shutdown_evt, event_q, reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix, *args):
    proc_worker = ProcWorker(name, startup_evt, shutdown_evt, event_q,reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix, *args)
    return proc_worker.run()    
    
class Proc:
    STARTUP_WAIT_SECS = 3.0
    SHUTDOWN_WAIT_SECS = 3.0
    
    def __init__(self, name, shutdown_event, event_q, reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix, *args):
        self.name = name
        self.shutdown_event = shutdown_event
        self.startup_event = mp.Event()
        self.proc = mp.Process(target=proc_worker_wrapper,
                               args=(name, self.startup_event, shutdown_event, event_q, reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix, *args))
        self.proc.start()
        started = self.startup_event.wait(timeout=Proc.STARTUP_WAIT_SECS)
        self.log(logging.DEBUG, f"Proc.__init__ starting : {name} got {started}")
        if not started:
            self.terminate()
        #    raise RuntimeError(f"Process {n

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
            print(logval)
        elif ParameterSet.logginglevel == 'error':
            if logtype == logging.ERROR:
                print(logval)
                Utils.WriteLogFile(os.path.join(ParameterSet.ResultsFolder,str(self.name)+"ERROR.txt"),logval)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.full_stop()
        return not exc_type
        
        
class MPQueue(mpq.Queue):

    DEFAULT_POLLING_TIMEOUT = 0.02

    # -- See StackOverflow Article :
    #   https://stackoverflow.com/questions/39496554/cannot-subclass-multiprocessing-queue-in-python-3-5
    #
    # -- tldr; mp.Queue is a _method_ that returns an mpq.Queue object.  That object
    # requires a context for proper operation, so this __init__ does that work as well.
    def __init__(self, *args, **kwargs):
        ctx = mp.get_context()
        super().__init__(*args, **kwargs, ctx=ctx)

    def safe_get(self, timeout=DEFAULT_POLLING_TIMEOUT):
        try:
            if timeout is None:
                return self.get(block=False)
            else:
                return self.get(block=True, timeout=timeout)
        except Empty:
            return None

    def safe_put(self, item, timeout=DEFAULT_POLLING_TIMEOUT):
        try:
            self.put(item, block=False, timeout=timeout)
            return True
        except Full:
            return False

    def drain(self):
        item = self.safe_get()
        while item:
            yield item
            item = self.safe_get()

    def safe_close(self):
        num_left = sum(1 for __ in self.drain())
        self.close()
        self.join_thread()
        return num_left


class EventMessage:
    def __init__(self, msg_src, msg_type, msg):
        self.id = time.time()
        self.msg_src = msg_src
        self.msg_type = msg_type
        self.msg = msg

    def __str__(self):
        return f"{self.msg_src:10} - {self.msg_type:10} : {self.msg}"

        
# ProcessManager.RunFullModel(RegionalList,PopulationParameters,DiseaseParameters, endTime, stepLength, modelPopNames, resultsName, numInfList,randomInfect,LocationImportationRisk,RegionListGuide,multiprocess,Regions,startDate=startDate)
def RunModel(GlobalLocations, GlobalInteractionMatrix, HospitalTransitionRate,LocationImportationRisk,PopulationParameters,DiseaseParameters,endTime,resultsName,startDate=datetime(2020,2,22),stepLength=1,numregions=-1,modelPopNames='zipcodes'):

    
    MAX_PROCESS_WAIT_SECS = 30.0
    num_regions = mp.cpu_count()
    
    if numregions > 0:
        num_regions = numregions
        

    # define the shutdown event
    shutdown_event = mp.Event()
    
    # Response queue for getting results back out
    responseq = MPQueue()
    
    poptotals = {}
    poptotal = 0
    for i in range(0,len(GlobalLocations)):
        poptotal += GlobalLocations[i].populationAmt
    
    RegionInteractionMatrixList = []
    RegionalLocations = []
    RegionalList = []
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
        mpq = MPQueue()
        eventqueues.append(mpq)
        proc = Proc(i, shutdown_event,mpq, responseq, PopulationParameters,DiseaseParameters,endTime,RegionalLocations[i],RegionInteractionMatrixList[i],RegionListGuide,modelPopNames,HospitalTransitionMatrix[i])
        procs.append(proc)

    # start the procs and build the regions

                
    # set the time of the simulation
    timeNow = 0
    timeRange = []
    
    while timeNow < endTime:
        timeNow = timeNow + stepLength
        timeRange.append(timeNow)
          
    results = {}
    numInfList = {}
    
    ### data for reconciliation
    offPopQueueEvents = []
    RegionReconciliationEvents = {} 
    testRegionValues = {}     
    
    
    lpvalslastdate = DiseaseParameters['QuarantineStartDate']
    InfPrior = 1
    HosPrior = 1  
        
    for tend in timeRange:
    
        infect = [0]*len(RegionalList)
        LPIDinfect = -1
        #if tend < 2: #---------------------- back this back out
        if len(LocationImportationRisk) > 0:
            LPIDinfect = Utils.multinomial(LocationImportationRisk,sum(LocationImportationRisk))
            rnum = RegionListGuide[LPIDinfect]
        else:
            rnum = random.choice(RegionalList)
        infect[rnum] = DiseaseParameters['ImportationRate']

        
        nextEventTime = {}
        offPopQueueEvents = []
        R0Stats = [0]*101
    
        for i in range(0,len(RegionalList)):
            procdict = {}
            procdict['tend'] = tend
            procdict['infectNumAgents'] = infect[i]
            procdict['LPIDinfect'] = LPIDinfect
            eventqueues[i].safe_put(EventMessage("main", "startevent", procdict))
        allprocsdone = False
        doneprocs = [0]*len(RegionalList)
        
        MAX_PROCESS_WAIT_SECS = 60.0
        tstart = time.time()
        while not allprocsdone:
            item = responseq.safe_get()
            if not item:
                t2 = time.time()
                if (t2 - tstart) > MAX_PROCESS_WAIT_SECS:
                    endRun(procs, eventqueues,RegionalList,modelPopNames)
                    exit()
                continue
            else:
                #print(f"MainWorker.main_loop received '{item}' message")
                if item.msg_type == "finishedrun":
                    doneprocs[item.msg_src] = 1
                   
                if item.msg_type == "FATAL":
                    endRun(procs, eventqueues,RegionalList,modelPopNames)
                    time.sleep(2) ## add here to let all the procs exit
                    exit()
                                            
                if sum(doneprocs) == len(RegionalList):
                    allprocsdone = True
                    break
            
            
            
        for i in range(0,len(RegionalList)):
            numinfVals = Utils.PickleFileRead(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"))
            for key in numinfVals.keys():
                numInfList[key] = numinfVals[key]
            
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
                
            if os.path.exists(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"R0Stats.pickle")):
                R0StatsList = Utils.PickleFileRead(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"R0Stats.pickle"))
                for key in R0StatsList.keys():
                    R0Stat = R0StatsList[key]
                    for rkey in R0Stat.keys():
                        rvals = R0Stat[rkey]
                        for r in range(0,len(rvals)):
                            R0Stats[r] += rvals[r]            
                            
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
                        lpvals[rkey]=lpdict['C']+lpdict['I']
                    numQ += lpdict['numQ']
                    numInfPrev += lpdict['numInfPrev']
                    InfEvtClear += lpdict['InfEvtClear']
                    numTests += lpdict['numTests']
                    confirmedcases += lpdict['CC']
        
        if tend > (lpvalslastdate+7) or tend == DiseaseParameters['QuarantineStartDate']:
            for i in range(0,len(RegionalList)):
                try:
                    os.remove(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"testextra.pickle"))
                except:
                    pass
                
            lpvalslastdate = tend
            sorted_d = sorted(((value, key) for (key,value) in lpvals.items()),reverse=True)
            numzip = min(len(sorted_d),20)
            sumval = 0
            testlpzips = [0]*20
            for i in range(0,numzip):
                testlpzips[i] = sorted_d[i][1]
                sumval += sorted_d[i][0]
            
            for i in range(0,len(RegionalList)):           
                Utils.PickleFileWrite(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"testextra.pickle"), testlpzips)                
            
            
        #if totS+totN+totInf+totC+totR+totD != totvalue:
        #    print("Error - something went wrong with the data -- please fix. This can only happen if there is a bug in the code")
        #    exit()
            
        ## Sort them by region            
        for QE in offPopQueueEvents:
            #ts = QE.getEventTime()
            # Clear events are sent to all regions            
            Rid = QE.RegionId
            testRegionValues[Rid]+=1
            RegionReconciliationEvents[Rid].append(QE) 
        
        for i in range(0,len(RegionalList)):
            if testRegionValues[i] > 0:
                Utils.PickleFileWrite(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"), RegionReconciliationEvents[i])
            
        x = startDate + timedelta(days=tend) 
        
        #print("End:",tend," (",(x.strftime('%Y-%m-%d')),") Time:",t3-t1,"(",t3-t2,") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," NumC:",totC," numR:",totR," numD:",totD," numH:",totH," R0:",round(R0,2)," R0R:",round(R0R,2)," R0HH:",round(R0HH,2)," HI:",totHI," HE:",totHE)
        
        
        rnumer = 0
        rdenom = 0
        
        for i in range(1,len(R0Stats)):
            rdenom += R0Stats[i]
            rnumer += R0Stats[i]*i            
        if rdenom > 0:
            R0Val = rnumer/rdenom
        else:
            R0Val = 0
        
        print("End:",tend," (",(x.strftime('%Y-%m-%d')),") num:", totS+totN+totInf+totC+totR+totD," numS:",totS," numN:",totN," NumInf:",totInf," (" + str(round(totInf / InfPrior,3)) +") NumC:",totC," numR:",totR," numH:",totH," numHMD:",totHMD,"(" ,str(round(totHMD/HosPrior,3)),") R0:",round(R0Val,2)," (cases:",confirmedcases," (",numTests,") Q:",numQ," (",numInfPrev,",",InfEvtClear,")")
        if totInf > 0:
            InfPrior = totInf
        if totHMD > 0:
            HosPrior = totHMD                   
            
        if os.path.exists(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle")):
                results = Utils.PickleFileRead(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"))
        results[tend] = numInfList
        Utils.PickleFileWrite(os.path.join(ParameterSet.ResultsFolder,"Results_"+resultsName+".pickle"),results)
            
    endRun(procs,eventqueues,RegionalList,modelPopNames)       

    print("Finished run")
    return RegionalList
            
def endRun(procs,eventqueues,RegionalList,modelPopNames):
    for i in range(0,len(procs)):
        eventqueues[i].safe_put(EventMessage("stop_procs", "END", "END"))
    
    for i in range(0,len(procs)):
        procs[i].shutdown_event.set()
    
    for i in range(0,len(procs)):
        procs[i].full_stop()

    for i in range(0,len(RegionalList)):
        try:
            os.remove(os.path.join(ParameterSet.QueueFolder,str(modelPopNames)+str(i)+"Queue.pickle"))
        except:
            print("error removing queue")
        
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"HOSPLIST.pickle"))
        except:
            print("error removing hosplist")
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+".pickle"))
        except:
            print("error removing ",str(modelPopNames))
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"RegionStats.pickle"))
        except:
            print("error removing regionstats")
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"R0Stats.pickle"))
        except:
            print("error removing R0stats")
            
        try:
            os.remove(os.path.join(ParameterSet.PopDataFolder,str(modelPopNames)+str(i)+"AgeStats.pickle"))
        except:
            print("error removing agestats")
