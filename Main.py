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

import sys, getopt
import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
from datetime import timedelta 
import os
import csv
import unicodedata
import string
import pandas as pd
import traceback
import copy
import re

import PostProcessing
import ParameterSet
import Utils
import GlobalModel
import ProcessManager
import LocalPopulation
import ParameterInput
import ProcessDataForPresentation as PDFP
import FitModelRegions
import FitModelInits


def main(argv):
        
    import time

    starttimer = time.time()
    
    ## Setup the folder structure and the settings   
    try:
        runs, OutputResultsFolder, FolderContainer, generatePresentationVals, OutputRunsFolder, Model = Utils.ModelFolderStructureSetup(argv)
    except:
        print("Setup error. There was an error setting up the folders for output. Please ensure that you have permission to create files and directories on this system.")
        if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
            print(traceback.format_exc())
        exit()
    
    # check that the model exists
    try:
        ModelFileInfo = os.path.join('data','Models.csv')
        modelfound = False
        with open(ModelFileInfo, mode='r') as infile:
            reader = csv.reader(infile)
            headers = next(reader)            
            ModelFileData = {}
            for rows in reader:
                modelname = rows[headers.index('Model')]
                if modelname == Model:
                    modelvals = {}
                    for i in range(0,len(headers)):
                        if headers[i] == 'startdate':
                            startdate = Utils.dateparser(rows[i])
                        elif headers[i] == 'enddate':
                            enddate = Utils.dateparser(rows[i])
                        else:
                            modelvals[headers[i]] = rows[i]
                            
                    if int(modelvals['UseHospital']) == 0:
                        ParameterSet.SaveHospitalData = False
                    if startdate > enddate:
                        print("Parameter input error. Start date is greater than end date. Please correct in the parameters file.")
                        raise Exception("Parameter Error")
                    modelfound = True
        if not modelfound:
            print("Specified model does not exist. Please ensure that the model is correctly specified in the Models.csv file")
            raise("Model not found error")
    except:
        print("Model input error. Please confirm the Models.csv file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
            print(traceback.format_exc())
        exit()
    
    # load the humidity data
    humiditydata = {}
    if os.path.exists(os.path.join('data',Model,modelvals['humiditydatafile'])):
        try: 
            mindate = Utils.dateparser('2030-12-31')
            maxdate = Utils.dateparser('1976-05-31')
            maxdatestr = ''
            with open(os.path.join('data',Model,modelvals['humiditydatafile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    dateval = rows[headers.index('Date')]
                    addrow = False
                    try:
                        testdate = Utils.dateparser(dateval)
                        addrow = True
                    except:
                        pass
                    if addrow:
                        if testdate < mindate:
                            mindate = testdate
                        if testdate > maxdate:
                            maxdate = testdate
                            maxdatestr = dateval
                        if dateval not in humiditydata.keys():
                            humiditydata[dateval] = {}
                        humiditydata[dateval]['ReportDateVal'] = testdate
                        for i in range(1,23):
                            nameval = 'Rand'+str(i)
                            humiditydata[dateval][nameval] = rows[headers.index(nameval)]

        except Exception as e:
            print("Humidity values error. Please confirm the Encounters file exists and is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            exit()    
    
        
    # load the essentialvisit file
    encountersdata = {}
    if os.path.exists(os.path.join('data',Model,modelvals['encountersfile'])):
        try: 
            mindate = Utils.dateparser('2030-12-31')
            maxdate = Utils.dateparser('1976-05-31')
            maxdatestr = ''
            with open(os.path.join('data',Model,modelvals['encountersfile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    dateval = rows[headers.index('Date')]
                    addrow = False
                    try:
                        testdate = Utils.dateparser(dateval)
                        addrow = True
                    except:
                        pass
                    if addrow:
                        if testdate < mindate:
                            mindate = testdate
                        if testdate > maxdate:
                            maxdate = testdate
                            maxdatestr = dateval
                        if dateval not in encountersdata.keys():
                            encountersdata[dateval] = {}
                        encountersdata[dateval]['Date'] = testdate
                        encountersdata[dateval]['VisitEnc'] = rows[headers.index('VisitEnc')]
                            
        except Exception as e:
            print("Encounters values error. Please confirm the Encounters file exists and is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            exit()    
    
    # Load the parameters
    input_df = None
    try:
        ParametersFileName = os.path.join('data','Parameters.csv')
        with open(ParametersFileName, mode='r') as infile:
            reader = csv.reader(infile)
            ParametersInputData = {}
            for rows in reader:
                minmaxvals = {}                    
                minmaxvals['min'] = rows[1]
                minmaxvals['max'] = rows[2]
                ParametersInputData[rows[0]] = minmaxvals
                
    except Exception as e:
        print("Parameter input error. Please confirm the parameter file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
            print(traceback.format_exc())
        exit()
    
    ##### Do not delete
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is - this left here for compatibility - deprecated
    ######
    
    
    #### For loading history data to start at
    historyCaseData = {}
    currentHospitalData = []
    if ParameterSet.LoadHistory:
        if not os.path.exists(os.path.join('data',Model,modelvals['historyCaseFile'])):
            print("Case history file does not exists")
            exit()
            
        try: 
            mindate = Utils.dateparser('2030-12-31')
            maxdate = Utils.dateparser('1976-05-31')
            maxdatestr = ''
            with open(os.path.join('data',Model,modelvals['historyCaseFile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    dateval = rows[headers.index('ReportDate')]
                    addrow = False
                    try:
                        testdate = Utils.dateparser(dateval)
                        addrow = True
                    except:
                        pass
                    if addrow:
                        if testdate < mindate:
                            mindate = testdate
                        if testdate > maxdate:
                            maxdate = testdate
                            maxdatestr = dateval
                        if dateval not in historyCaseData.keys():
                            historyCaseData[dateval] = {}
                        historyCaseData[dateval]['ReportDateVal'] = testdate
                        historyCaseData[dateval][rows[headers.index('ZipCode')]] = {}
                        historyCaseData[dateval][rows[headers.index('ZipCode')]]['ReportedNewCases'] = rows[headers.index('ReportedNewCases')]
                        historyCaseData[dateval][rows[headers.index('ZipCode')]]['EstimatedMildCases'] = rows[headers.index('EstimatedMildCases')]
        except Exception as e:
            print("History values error. Please confirm the history case file exists and is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            exit()       	

        if os.path.exists(os.path.join('data',Model,modelvals['currentHospitalFile'])):            
            try: 
                currentHospitalData = {}
                with open(os.path.join('data',Model,modelvals['currentHospitalFile']),mode='r') as infile:
                    reader = csv.reader(infile)   
                    headers = next(reader,None)   
                    for rows in reader:
                        currentHospitalData[rows[headers.index('ProviderNames')]] = int(rows[headers.index('Pats')])
                
                
                historyCaseData['currentHospitalData'] = {}
                
                ComHosAdj = pd.read_csv(os.path.join("data",Model,modelvals['HospitalMatrixFile']), index_col=0)
                
                
                for hosp in currentHospitalData.keys():
                    curVal = currentHospitalData[hosp]
                    hospperlist = ComHosAdj[hosp].tolist()
                    while curVal > 0:
                        j = Utils.Multinomial(hospperlist)
                        if str(list(ComHosAdj.index.values)[j]) in historyCaseData['currentHospitalData']:
                            historyCaseData['currentHospitalData'][str(list(ComHosAdj.index.values)[j])] += 1
                        else:
                            historyCaseData['currentHospitalData'][str(list(ComHosAdj.index.values)[j])] = 1
                        curVal -= 1
                                               
            except Exception as e:
                print("History hospital values error. Please confirm the hospital history data file exists and is correctly specified")
                if ParameterSet.logginglevel == "debug":
                    print(traceback.format_exc())
                exit()       	
                
    # This sets the interventions
    interventions = ParameterInput.InterventionsParameters(Model,modelvals['intfile'],startdate)
    if len(interventions) == 0:
        print("Interventions input error. Please confirm the intervention file exists and is correctly specified")
        exit()
    
    ## alter values related to transmission in Utils file
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)

    try:
        if ParameterSet.FitModel:
            fitted = False
            ParameterVals = FitModelInits.getFitModelParameters(Model,ParameterSet.FitModelRuns,append=True)
            if len(ParameterVals) < 1:
                print("Error creating parametervals for fitting")
                exit()
                
            ParameterSet.SavedRegionContainer = overallResultsName
            print("Saved Region Folder:",ParameterSet.SavedRegionContainer)
            if not os.path.exists(os.path.join("data",Model,ParameterSet.SavedRegionContainer)):
                os.makedirs(os.path.join("data",Model,ParameterSet.SavedRegionContainer))
            
            i = 0
            while not fitted:
                print(ParameterVals[i])
                fitinfo, fitdates = FitModelRegions.runRegionFit(FolderContainer,OutputRunsFolder,overallResultsName,Model,modelvals,enddate,ParameterVals[i],historyCaseData=historyCaseData,saveRun=True,SavedRegionFolder=os.path.join("data",Model,ParameterSet.SavedRegionContainer),encountersdata=encountersdata,humiditydata=humiditydata)
                fitted = fitinfo['fitted']
                
                i += 1
                if i > len(ParameterVals):
                    print("Model never hit a fit! Try a larger number of runs!")
                    exit()
                
            ParameterSet.UseSavedRegion = True
    except Exception as e:
        print("Fitting error.")
        if ParameterSet.logginglevel == "debug":
            print(traceback.format_exc())
        exit()      
    
    # get list of saved regiuons if using that value
    saveregionsfolderlist = []
    if ParameterSet.UseSavedRegion:
        if not os.path.exists(os.path.join("data",Model,ParameterSet.SavedRegionContainer)):
            print("Saved Container not found. Please check that this folder exists.")
            exit()
        
        xlength = len(os.path.join("data",Model,ParameterSet.SavedRegionContainer))+1
        for root, dirs, files in os.walk(os.path.join("data",Model,ParameterSet.SavedRegionContainer), topdown=False):
            for filename in files:
                #print(root[xlength:])
                if root[xlength:] not in saveregionsfolderlist:
                    saveregionsfolderlist.append(root[xlength:])    
            #for name in dirs:            
            #    dirname = os.path.join(root, name)
                #print(dirname + " -> " + dirname[xlength:])
            #    saveregionsfolderlist.append(dirname[xlength:])
        #print("SavedRegionList:",saveregionsfolderlist)
        #saveregionsfolderlist = os.listdir(os.path.join("data",Model,ParameterSet.SavedRegionContainer))
        if len(saveregionsfolderlist) == 0:
            print("Saved Container has no saved regions. Please check that this folder has data.")
            exit()
    
            
    
                  
    PopulationParameters, DiseaseParameters = ParameterInput.SampleRunParameters(ParametersInputData)
    runningavg = []                  
    run = 0
    totruns = []
    for key in interventions.keys():
        totruns.append(runs)
            
    nummissmax = 0    
    while sum(totruns) > 0:
        fitted = False
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        
        #for intnum in range(0,len(interventionnames)):
        inton = Utils.Multinomial(totruns)
        key = list(interventions.keys())[inton]
    
        print("Running:",key," Remaining:",sum(totruns),totruns)
                
        DiseaseParameters['ImportationRate'] = int(modelvals['ImportationRate'])
        randomstate = random.getstate()
        mprandomseed = random.randint(100000,99999999)
        np.random.seed(seed=mprandomseed)
        endTime = (enddate - startdate).days
        DiseaseParameters['startdate'] = startdate
        DiseaseParameters['enddate'] = enddate
        DiseaseParameters['humidityversion'] = -1
            
        DiseaseParameters = ParameterInput.setInfectionProb(interventions,key,DiseaseParameters,Model,historyData=historyCaseData,encountersdata=encountersdata,humiditydata=humiditydata)
        
        resultsNameP = key + "_" + resultsName
                    
        if Utils.RepresentsInt(modelvals['StartInfected']):
            StartInfected = int(modelvals['StartInfected'])
        else:
            StartInfected = -1
            
        if ParameterSet.UseSavedRegion:
            fitted = True
            reg = random.randint(0,len(saveregionsfolderlist)-1)
            SavedRegionFolder = saveregionsfolderlist[reg]
            regionfiles = []
            for (dirpath, dirnames, filenames) in os.walk(os.path.join("data",Model,ParameterSet.SavedRegionContainer,SavedRegionFolder)):
                regionfiles.extend(filenames)
                break
            print("Foldername:",SavedRegionFolder)
            print("RegionFiles",regionfiles)
            
            #regionfiles.remove('DiseaseParameters.pickle')
            #regionfiles.remove('PopulationParameters.pickle')
            numregions = 0
            for rfname in regionfiles:
                if re.search('Region.+', rfname):
                    if not re.search('RegionStats.+', rfname): 
                        numregions += 1    

            
                
            DiseaseParametersCur = copy.deepcopy(DiseaseParameters)
            DiseaseParameters = Utils.PickleFileRead(os.path.join("data",Model,ParameterSet.SavedRegionContainer,SavedRegionFolder,"DiseaseParameters.pickle"))
            
            PopulationParameters = Utils.PickleFileRead(os.path.join("data",Model,ParameterSet.SavedRegionContainer,SavedRegionFolder,"PopulationParameters.pickle"))
            startdate = DiseaseParameters['startdate']
            endTime = (enddate - startdate).days
            
            ## Should be updated to take account of any differences 
            updatetransprob = True
            if 'UpdateTransProb' in interventions[key]:
                if interventions[key]['UpdateTransProb'] == "0":
                    updatetransprob = False
            if updatetransprob:
                if 'humidityversion' in DiseaseParameters:
                    DiseaseParametersCur['humidityversion'] = DiseaseParameters['humidityversion']
                    DiseaseParametersCur = ParameterInput.setInfectionProb(interventions,key,DiseaseParametersCur,Model,historyData=historyCaseData,encountersdata=encountersdata,humiditydata=humiditydata)
                
                DiseaseParameters['TransProb'] = copy.deepcopy(DiseaseParametersCur['TransProb'])
                DiseaseParameters['TransProbLow'] = copy.deepcopy(DiseaseParametersCur['TransProbLow'])
                DiseaseParameters['TransProbSchool'] = copy.deepcopy(DiseaseParametersCur['TransProbSchool'])
                DiseaseParameters['InterventionMobilityEffect'] = copy.deepcopy(DiseaseParametersCur['InterventionMobilityEffect'])
                DiseaseParameters['InterventionDate'] = interventions[key]['InterventionStartReductionDate']
                DiseaseParameters['QuarantineType'] = interventions[key]['QuarantineType']

                DiseaseParameters['TestingAvailabilityDateHosp'] = interventions[key]['TestingAvailabilityDateHosp']
                DiseaseParameters['TestingAvailabilityDateComm'] = interventions[key]['TestingAvailabilityDateComm']
                DiseaseParameters['PerFollowQuarantine'] = float(interventions[key]['PerFollowQuarantine'])
                DiseaseParameters['testExtra'] = int(interventions[key]['testExtra'])
                DiseaseParameters['ContactTracing'] = int(interventions[key]['ContactTracing'])
                
            
            if interventions[key]['QuarantineStartDate'] == '':
                DiseaseParameters['QuarantineStartDate'] = interventions[key]['finaldate']    
                
            else:
                DiseaseParameters['QuarantineStartDate'] = interventions[key]['QuarantineStartDate']    
                
            ParameterSet.OldAgeRestriction = False
            ParameterSet.OldAgeReduction = 0
            if 'OldAgeRestriction' in interventions[key]:     
                if interventions[key]['OldAgeRestriction'] == '1':
                    ParameterSet.OldAgeRestriction = True
                    ParameterSet.OldAgeReduction = float(interventions[key]['OldAgeReduction'])
                    
            ParameterSet.GatheringRestriction = False
            ParameterSet.GatheringMax = 10000
            if 'GatheringRestriction' in interventions[key]:     
                if interventions[key]['GatheringRestriction'] == '1':
                    ParameterSet.GatheringRestriction = True
                    ParameterSet.GatheringMax = float(interventions[key]['GatheringMax'])
                    ParameterSet.GatheringPer = float(interventions[key]['GatheringPer'])
            
            if 'TimeToFindContactsLow' in interventions[key] and Utils.RepresentsInt(interventions[key]['TimeToFindContactsLow']) and \
                'TimeToFindContactsHigh' in interventions[key] and Utils.RepresentsInt(interventions[key]['TimeToFindContactsHigh']):
                DiseaseParameters['TimeToFindContactsLow'] = int(interventions[key]['TimeToFindContactsLow'])
                DiseaseParameters['TimeToFindContactsHigh'] = int(interventions[key]['TimeToFindContactsHigh'])
            
            fiinfo = GlobalModel.RunSavedRegionModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,SavedRegionFolder=os.path.join("data",Model,ParameterSet.SavedRegionContainer),numregions=numregions,FolderContainer=SavedRegionFolder)
            
            fitted = fitinfo['fitted']
            
            PERIOD_OF_TIME = 39600 # 11 hours
    
            if time.time() > starttimer + PERIOD_OF_TIME : exit()   
               
        #elif ParameterSet.LoadHistory:
            #startdate = maxdate+timedelta(days=1)
            #endTime = (enddate - startdate).days
            #ParameterSet.StartDateHistory = (mindate - startdate).days
        #    for reportdate in historyCaseData.keys():
        #        if reportdate != 'currentHospitalData':
        #            historyCaseData[reportdate]['timeval'] = (historyCaseData[reportdate]['ReportDateVal'] - startdate).days
                
        #    DiseaseParameters['startdate'] = startdate
        #    fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = GlobalModel.RunHistoryModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,historyData=historyCaseData)
        else:
            if ParameterSet.LoadHistory:                
                for reportdate in historyCaseData.keys():
                    if reportdate != 'currentHospitalData':
                        historyCaseData[reportdate]['timeval'] = (historyCaseData[reportdate]['ReportDateVal'] - startdate).days
                    
            fitinfo = GlobalModel.RunDefaultModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,StartInfected=StartInfected,historyData=historyCaseData)
            fitted = fitinfo['fitted']
            
        if fitted:
            #PopulationParameters, DiseaseParameters = ParameterInput.SampleRunParameters(ParametersInputData,MC=True,PopulationParameters=PopulationParameters, DiseaseParameters=DiseaseParameters,maxstepsize=.05)
            totruns[inton]-=1
        else:
            if SLSH+SLSD+SLSC == 0:
                nummissmax += 1
            if nummissmax > 25:                            
                PopulationParameters, DiseaseParameters = ParameterInput.SampleRunParameters(ParametersInputData)
                nummissmax = 0
            else:
                if avgperdiffhosp > 1:
                    PopulationParameters, DiseaseParameters = ParameterInput.SampleRunParameters(ParametersInputData)
                else:
                    PopulationParameters, DiseaseParameters = ParameterInput.SampleRunParameters(ParametersInputData,MC=True,PopulationParameters=PopulationParameters, DiseaseParameters=DiseaseParameters,maxstepsize=1)
            
    if generatePresentationVals == 1:
        interventionnames = []
        for key in interventions.keys():
            interventionnames.append(key)
        PDFP.Presentation(interventionnames,OutputRunsFolder,OutputResultsFolder)
                
       
            
        
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])
