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

def main(argv):
        
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
            ModelFileData = {}
            for rows in reader:
                modelname = rows[0]
                if modelname == Model:
                    modelvals = {}
                    modelvals['PopulationFile'] = rows[1]
                    modelvals['GeographicScale'] = rows[2]
                    modelvals['LocalPopName'] = rows[3]
                    modelvals['RegionalPopName'] = rows[4]
                    modelvals['UseHospital'] = rows[5]
                    if int(modelvals['UseHospital']) == 0:
                        ParameterSet.SaveHospitalData = False
                    modelvals['HospitalMatrixFile'] = rows[6]
                    modelvals['HospitalNamesFile'] = rows[7]
                    startdate = Utils.dateparser(rows[8])
                    enddate = Utils.dateparser(rows[9])
                    modelvals['FitPer'] = rows[10]
                    modelvals['ImportationRate'] = rows[11]
                    modelvals['intfile'] = rows[12]
                    modelvals['StartInfected'] = rows[13]
                    modelvals['FitValFile'] = rows[14]
                    modelvals['historyCaseFile'] = rows[15]
                    modelvals['currentHospitalFile'] = rows[16]
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
    
    ### For fitting purposes
    fitdates = []
    fitdatesorig = []
    hospitalizations = []
    deaths = []
    cases = []
    fitper = .3
    if ParameterSet.FitModel:
        if not os.path.exists(os.path.join('data',Model,modelvals['FitValFile'])):
            print("Fitting file does not exist")
            exit()
            
        try:
            fitper = float(modelvals['FitPer'])
            FitModelVals = os.path.join('data',Model,modelvals['FitValFile'])
            with open(FitModelVals, mode='r') as infile:
                reader = csv.reader(infile)
                headers = next(reader, None)
                if 'hospitalizations' not in headers and 'deaths' not in headers and 'cases' not in headers:
                    print("Fitvals file is not specified correctly")
                    raise Exception("Fitvals Error")    
                for rows in reader:
                    
                    fitdate = Utils.dateparser(rows[0])
                    fitdatesorig.append(fitdate)
                    if fitdate < startdate or fitdate > enddate:
                        print("Fit dates error. Fit date must be between start and end date.")
                        raise Exception("Fitvals Error")    
                    
                    
                    try:
                        hospitalizations.append(int(rows[headers.index('hospitalizations')]))
                    except ValueError:
                        pass
                    try:
                        deaths.append(int(rows[headers.index('deaths')]))
                    except ValueError:
                        pass
                    try:
                        cases.append(int(rows[headers.index('cases')]))
                    except ValueError:
                        pass
                    
        except Exception as e:
            print("Fit values error. Please confirm the FitVals file exists and is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            exit()        
    print(deaths)
    for fitdate in fitdatesorig:
        fitdates.append((fitdate - startdate).days)
    
    #### For loading history data to start at
    historyCaseData = {}
    currentHospitalData = []
    if ParameterSet.LoadHistory:
        if not os.path.exists(os.path.join('data',Model,modelvals['historyCaseFile'])):
            print("Case history file does not exists")
            exit()
            
        try: 
            with open(os.path.join('data',Model,modelvals['historyCaseFile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    historyCaseData[rows[headers.index('Zip')]] = {}
                    historyCaseData[rows[headers.index('Zip')]]['CurrentCases'] = rows[headers.index('CurrentCases')]
                    historyCaseData[rows[headers.index('Zip')]]['PriorCases'] = rows[headers.index('PriorCases')]
                    historyCaseData[rows[headers.index('Zip')]]['NewCases'] = rows[headers.index('NewCases')]
                    historyCaseData[rows[headers.index('Zip')]]['HospitalCases'] = 0
                    historyCaseData[rows[headers.index('Zip')]]['State'] = rows[headers.index('State')]
        except Exception as e:
            print("History values error. Please confirm the history case file exists and is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            exit()       	

        
        if os.path.exists(os.path.join('data',Model,modelvals['currentHospitalFile'])):            
            try: 
                with open(os.path.join('data',Model,modelvals['currentHospitalFile']),mode='r') as infile:
                    reader = csv.reader(infile)      
                    for rows in reader:
                        currentHospitalData.append(int(rows[1]))
                print(sum(currentHospitalData))
                ComHosAdj = pd.read_csv(os.path.join("data",Model,modelvals['HospitalMatrixFile']), index_col=0)
                
                for chd in range(0,len(currentHospitalData)):
                    curVal = currentHospitalData[chd]
                    hospperlist = ComHosAdj[ComHosAdj.columns[chd]].tolist()
                    while curVal > 0:
                        j = Utils.Multinomial(hospperlist)
                        if str(list(ComHosAdj.index.values)[j]) in historyCaseData:
                            historyCaseData[str(list(ComHosAdj.index.values)[j])]['HospitalCases'] += 1
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
    
    # get list of saved regiuons if using that value
    saveregionsfolderlist = []
    if ParameterSet.UseSavedRegion:
        if not os.path.exists(os.path.join("data",Model,ParameterSet.SavedRegionContainer)):
            print("Saved Container not found. Please check that this folder exists.")
            exit()
            
        saveregionsfolderlist = os.listdir(os.path.join("data",Model,ParameterSet.SavedRegionContainer))
        if len(saveregionsfolderlist) == 0:
            print("Saved Container has no saved regions. Please check that this folder has data.")
            exit()
        print(saveregionsfolderlist)
        
    ## alter values related to transmission in Utils file
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
                  
    PopulationParameters, DiseaseParameters = ParameterInput.SampleRunParameters(ParametersInputData)
    runningavg = []                  
    run = 0
    totruns = []
    for key in interventions.keys():
        totruns.append(runs)
            
    nummissmax = 0    
    while sum(totruns) > 0:
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
            
        DiseaseParameters = ParameterInput.setInfectionProb(interventions,key,DiseaseParameters,Model,fitdates=fitdates,historyData=historyCaseData)
        
        resultsNameP = key + "_" + resultsName
                    
        if Utils.RepresentsInt(modelvals['StartInfected']):
            StartInfected = int(modelvals['StartInfected'])
        else:
            StartInfected = -1
            
        if ParameterSet.UseSavedRegion:
            reg = random.randint(0,len(saveregionsfolderlist)-1)
            SavedRegionFolder = saveregionsfolderlist[reg]
            regionfiles = []
            for (dirpath, dirnames, filenames) in os.walk(os.path.join("data",Model,ParameterSet.SavedRegionContainer,SavedRegionFolder)):
                regionfiles.extend(filenames)
                break
            print(SavedRegionFolder)
            print(regionfiles)
            
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
            #DiseaseParameters['TransProb'] = copy.deepcopy(DiseaseParametersCur['TransProb'])
            #DiseaseParameters['TransProbLow'] = copy.deepcopy(DiseaseParametersCur['TransProbLow'])
            #DiseaseParameters['TransProbSchool'] = copy.deepcopy(DiseaseParametersCur['TransProbSchool'])
            #DiseaseParameters['InterventionMobilityEffect'] = copy.deepcopy(DiseaseParametersCur['InterventionMobilityEffect'])
            #DiseaseParameters['InterventionDate'] = interventions[key]['InterventionStartReductionDate']
            #DiseaseParameters['QuarantineType'] = interventions[key]['QuarantineType']
            
            if interventions[key]['QuarantineStartDate'] == '':
                DiseaseParameters['QuarantineStartDate'] = interventions[key]['finaldate']    
                
            else:
                DiseaseParameters['QuarantineStartDate'] = interventions[key]['QuarantineStartDate']    
                
            #DiseaseParameters['TestingAvailabilityDateHosp'] = interventions[key]['TestingAvailabilityDateHosp']
            #DiseaseParameters['TestingAvailabilityDateComm'] = interventions[key]['TestingAvailabilityDateComm']
            #DiseaseParameters['PerFollowQuarantine'] = float(interventions[key]['PerFollowQuarantine'])
            #DiseaseParameters['testExtra'] = int(interventions[key]['testExtra'])
            #DiseaseParameters['ContactTracing'] = int(interventions[key]['ContactTracing'])
                
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
                    
            
            if 'TimeToFindContactsLow' in interventions[key] and Utils.RepresentsInt(interventions[key]['TimeToFindContactsLow']) and \
                'TimeToFindContactsHigh' in interventions[key] and Utils.RepresentsInt(interventions[key]['TimeToFindContactsHigh']):
                DiseaseParameters['TimeToFindContactsLow'] = int(interventions[key]['TimeToFindContactsLow'])
                DiseaseParameters['TimeToFindContactsHigh'] = int(interventions[key]['TimeToFindContactsHigh'])
            
            fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = GlobalModel.RunSavedRegionModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,SavedRegionFolder=os.path.join("data",Model,ParameterSet.SavedRegionContainer,SavedRegionFolder),numregions=numregions)
                
        elif ParameterSet.LoadHistory:
            fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = GlobalModel.RunHistoryModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,historyData=historyCaseData)
        else:
            fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = GlobalModel.RunDefaultModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper,StartInfected=StartInfected)
        
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
