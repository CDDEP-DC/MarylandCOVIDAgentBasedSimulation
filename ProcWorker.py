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

import logging
import signal
import functools
import sys, getopt
import time
import math
import os
import copy
import random
import traceback
import numpy as np
from datetime import datetime  
from datetime import timedelta 

import Region
import ParameterSet
import Utils
import GBQueue




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

    def __init__(self, name, startup_event, shutdown_event, event_q,reply_q,PopulationParameters,
                    DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,
                    RegionListGuide,modelPopNames,HospitalTransitionMatrix,mprandomseed,eventqueues,historyData,SavedRegionFolder,GlobalLocations, *args):
        self.name = name
        #self.log = functools.partial(_logger, f'{self.name} Worker')
        self.startup_event = startup_event
        self.shutdown_event = shutdown_event
        self.event_q = event_q
        self.reply_q = reply_q
        self.terminate_called = 0
        self.modelPopNames = modelPopNames
        
        self.eventqueues = eventqueues
        
        self.R0StatsList = {}
        self.AgeStatsList = {}
        self.CurrentHospOccList = {}
        self.RegionStats = {}
        self.historyData = historyData
        
        self.RegionReconciliationEvents = []
        
        
        if ParameterSet.UseSavedRegion:
            if os.path.exists(os.path.join(SavedRegionFolder,"Region"+str(self.name)+".pickle")):
                self.ProcRegion = Utils.PickleFileRead(os.path.join(SavedRegionFolder,"Region"+str(self.name)+".pickle"))
                print("Getting Region"+str(self.name)+".pickle")
                self.RegionStats = copy.deepcopy(self.ProcRegion.savedStats)
                self.CurrentHospOccList = copy.deepcopy(self.ProcRegion.savedOcc)
                self.ProcRegion.resetParameters(GlobalLocations,PopulationParameters,DiseaseParameters,endTime)
            else:            
                print("Prior data for Region"+str(self.name)+" is missing")
            ##### need to update here based on new version
            #print(self.RegionStats)
            
        else:
            self.ProcRegion = Region.Region(RegionalLocations, RegionInteractionMatrixList, name, RegionListGuide,HospitalTransitionMatrix,PopulationParameters,DiseaseParameters,endTime)
            
        random.seed(mprandomseed+int(self.name))
        np.random.seed(seed=mprandomseed+int(self.name))
        
    def log(self,logtype,logval):
        if ParameterSet.logginglevel == 'debug':
            #print(logval)
            pass
        elif ParameterSet.logginglevel == 'error':
            if logtype == logging.ERROR:
                print(logval)
                Utils.WriteLogFile(os.path.join(ParameterSet.ResultsFolder,str(self.modelPopNames)+str(self.name)+"ProcWorkerERROR.txt"),logval)
        
    def init_signals(self):
        self.log(logging.DEBUG, str(self.name)+"Entering init_signals")
        signal_object = init_signals(self.shutdown_event, self.int_handler, self.term_handler)
        return signal_object

    def saveRegion(self,Folder):
        try:
            
            if os.path.exists(Folder):
                self.ProcRegion.savedStats = copy.deepcopy(self.RegionStats)
                self.ProcRegion.savedOcc = copy.deepcopy(self.CurrentHospOccList)
                Utils.PickleFileWrite(os.path.join(Folder,"Region"+str(self.name)+".pickle"), self.ProcRegion)
                
                #Utils.PickleFileWrite(os.path.join(ParameterSet.SavedRegionFolder,FolderContainer,"RegionStats"+str(self.name)+".pickle"), RegionSaveStats)
            self.reply_q.safe_put(GBQueue.EventMessage(self.name, "finishedsave", 0))
        except Exception as e:
            print("Error in ProcWorker.saveRegion.")
            if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                print(traceback.format_exc())
            exit()    
        
    def main_loop(self):
        self.log(logging.DEBUG, str(self.name)+"Entering main_loop")
        while not self.shutdown_event.is_set():
            item = self.event_q.safe_get()
            if not item:
                continue
            else:
                if item.msg_type == "END":
                    break
                elif item.msg_type == "offPopQueueEvent":
                    self.RegionReconciliationEvents.append(item.msg)
                elif item.msg_type == "history":
                    self.initHistory(item.msg)
                elif item.msg_type == "saveregion":
                    self.saveRegion(item.msg)
                elif item.msg_type == "startevent":
                    self.main_func(item.msg)
                elif item.msg_type == "reconciliation":
                    self.reconciliation(item.msg,reply=True)    
                    

    def startup(self):
        self.log(logging.DEBUG, str(self.name)+"Entering startup")
        pass

    def shutdown(self):
        self.log(logging.DEBUG, str(self.name)+"Entering shutdown")
        self.event_q.drain()
        self.event_q.safe_close()
        pass

    def initHistory(self, procdict):
        try:
            if len(self.historyData) > 0:
                
                offPopQueueEvents, numpriorcases, numnewcases = self.ProcRegion.initializeHistory(self.historyData,procdict['startdate'],procdict['fitenddate'],procdict['virus'])
                # Reconcile the current region events 
                offRegionEvents = []
                RegionReconciliationEvents = []
                for QE in offPopQueueEvents:
                    if self.name == QE.RegionId:
                        RegionReconciliationEvents.append(QE) 
                    else:
                        offRegionEvents.append(QE)
                
                if len(RegionReconciliationEvents) > 0:
                    self.ProcRegion.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
                    RegionReconciliationEvents.clear()
                    
                # Write the off-pop queues to disk for assessing in the merge       
                Utils.PickleFileWrite(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"), offRegionEvents)
                    
                if ParameterSet.logginglevel == 'debug':
                    print(str(self.name)+" setup "+str(numpriorcases)+" prior cases "+str(numnewcases)+" new cases")
                    
                timeNow = procdict['timeNow']
                day = 0
                while day <= timeNow:
                    regionStats = self.ProcRegion.getRegionStats()
                    regionStatsX = {}
                    regionStatsX[self.name] = regionStats
                    self.RegionStats[day] = regionStatsX
                    
                    # Get the hospital stats for printing at the end    
                    if ParameterSet.SaveHospitalData:
                        self.CurrentHospOccList[day] = copy.deepcopy(self.ProcRegion.getHospitalOccupancy())
          
                    # Save the R0 stats
                    R0Stats = self.ProcRegion.getR0Stats()
                    self.R0StatsList[self.name] = R0Stats    
                    day += 1
                    
            self.reply_q.safe_put(GBQueue.EventMessage(self.name, "finishedhistoryinit", numpriorcases))
        except Exception as e:
            print("Error in ProcWorker.initHistory.")
            if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                print(traceback.format_exc())
            exit()
        
    def reconciliation(self,msg,reply=False):
        RegionReconciliationEvents = []
        
        ## Reconcile any off-region events        
        try:
            RegionReconciliationEvents = Utils.PickleFileRead(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"))
        except:
           RegionReconciliationEvents = [] 
        try:
            os.remove(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"))
        except:
            pass
        if len(RegionReconciliationEvents) > 0:
            self.ProcRegion.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
            RegionReconciliationEvents.clear()
        if reply:
            self.reply_q.safe_put(GBQueue.EventMessage(self.name, "finishedrec", "all done"))    
            
    def main_func(self, procdict):
        try:
            tend = int(procdict['tend'])
            LPIDs = procdict['LPIDs']
            vacnumperregion = 0
            if 'VacNum' in procdict.keys():
                 vacnumperregion = int(procdict['VacNum'])
                 
            virus = None
            if 'virus' in procdict.keys():
                 virus = procdict['virus']
            
            self.reconciliation(procdict,reply=False)
            
            ## add vaccinations
            if vacnumperregion > 0:
                ac = random.randint(2,4)
                self.ProcRegion.vaccinateRandomAgents(tend,vacnumperregion,ageCohort=ac)
            
            ## First run the preliminary infections   
            infop = []
            if len(LPIDs) > 0:
                infop = self.ProcRegion.infectRandomAgents(tend,virus,LPIDs=LPIDs)
                
            ## Main work done here in running forward one step    
            regionStats, offPopQueueEvents, numEvents, fitval = self.ProcRegion.runTimePeriod(tend)
            
            # add any extra off pop queue events generated in the initial infection process here
            if len(infop) > 0:
                offPopQueueEvents.extend(infop)
                
            # save the region stats
            regionStatsX = {}
            regionStatsX[self.name] = regionStats
            self.RegionStats[tend] = regionStatsX
            if ParameterSet.logginglevel == 'debug':
                Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"RegionStats.pickle"), regionStatsX)
            
            # Get the hospital stats for printing at the end    
            if ParameterSet.SaveHospitalData:
                self.CurrentHospOccList[tend] = copy.deepcopy(self.ProcRegion.getHospitalOccupancy())
      
            # Save the R0 stats
            R0Stats = self.ProcRegion.getR0Stats()
            self.R0StatsList[self.name] = R0Stats
            
            # Save the age stats
            #LPAgeStats = self.ProcRegion.getAgeStats()
            #self.AgeStatsList[self.name] = LPAgeStats
            
            # Reconcile the current region events 
            offRegionEvents = []
            RegionReconciliationEvents = []
            for QE in offPopQueueEvents:
                if self.name == QE.RegionId:
                    RegionReconciliationEvents.append(QE) 
                else:
                    offRegionEvents.append(QE)
            
            if len(RegionReconciliationEvents) > 0:
                self.ProcRegion.addEventsFromOtherLocalPopulations(RegionReconciliationEvents)
                RegionReconciliationEvents.clear()
                
            if ParameterSet.UseQueuesForQueues:
                if len(offRegionEvents) > 0:
                    for opqe in offPopQueueEvents:
                        self.eventqueues[opqe.RegionId].safe_put(GBQueue.EventMessage(self.name,"offPopQueueEvent",opqe))
            else:
                # Write the off-pop queues to disk for assessing in the merge       
                Utils.PickleFileWrite(os.path.join(ParameterSet.QueueFolder,str(self.modelPopNames)+str(self.name)+"Queue.pickle"), offRegionEvents)
            
            self.reply_q.safe_put(GBQueue.EventMessage(self.name, "finishedrun", fitval))
        except Exception as e:
            print("Error in ProcWorker.MainLoop.")
            if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                print(traceback.format_exc())
            exit()
            
    def run(self):
        self.init_signals()
        try:
            self.startup()
            self.startup_event.set()
            self.main_loop()        
            Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"RegionStats.pickle"), self.RegionStats)
            if ParameterSet.SaveHospitalData:
                Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"HOSPLIST.pickle"), self.CurrentHospOccList)
            
            Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"R0Stats.pickle"), self.R0StatsList)
            #Utils.PickleFileWrite(os.path.join(ParameterSet.PopDataFolder,str(self.modelPopNames)+str(self.name)+"AgeStats.pickle"), self.AgeStatsList)
            self.event_q.drain()
            self.event_q.safe_close()
            self.log(logging.INFO, str(self.name)+"Normal Shutdown")
            #self.event_q.safe_put(EventMessage(self.name, "SHUTDOWN", "Normal"))
            return 0
        except BaseException as exc:
            # -- Catch ALL exceptions, even Terminate and Keyboard interrupt
            #self.log(logging.ERROR, f"Exception Shutdown: {exc}", exc_info=True)
            self.log(logging.ERROR, f"Exception Shutdown: {exc}")
            if not self.shutdown_event.is_set():
                self.reply_q.safe_put(GBQueue.EventMessage(self.name, "FATAL", f"{exc}"))
            self.event_q.drain()
            # -- TODO: call raise if in some sort of interactive mode
            if type(exc) in (TerminateInterrupt, KeyboardInterrupt):
                sys.exit(1)
            else:
                sys.exit(2)
        finally:
            self.shutdown()

def proc_worker_wrapper(name, startup_evt, shutdown_evt, event_q, reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix,mprandomseed,eventqueues,historyData,SavedRegionFolder,GlobalLocations, *args):
    proc_worker = ProcWorker(name, startup_evt, shutdown_evt, event_q,reply_q,PopulationParameters,DiseaseParameters,endTime,RegionalLocations,RegionInteractionMatrixList,RegionListGuide,modelPopNames,HospitalTransitionMatrix,mprandomseed,eventqueues,historyData,SavedRegionFolder, GlobalLocations,*args)
    return proc_worker.run()    
