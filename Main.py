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

import PostProcessing
import ParameterSet
import Utils
import GlobalModel
import ProcessManager
import LocalPopulation
import ParameterInput
import ProcessDataForPresentation as PDFP
import traceback

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
    hospitalizations = []
    deaths = []
    fitper = .3
    if ParameterSet.FitModel:
        try:
            fitper = float(modelvals['FitPer'])
            FitModelVals = os.path.join('data',Model,'FitVals.csv')
            with open(FitModelVals, mode='r') as infile:
                reader = csv.reader(infile)
                for rows in reader:
                    
                    fitdate = Utils.dateparser(rows[0])
                    if fitdate < startdate or fitdate > enddate:
                        print("Fit dates error. Fit date must be between start and end date.")
                        raise Exception("Parameter Error")    
                    
                    fitdates.append((fitdate - startdate).days)
                    hospitalizations.append(int(rows[1]))
                    deaths.append(int(rows[2]))
                    
        except Exception as e:
            print("Fit values error. Please confirm the FitVals file exists and is correctly specified")
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
    
    run = 0
    totruns = []
    for key in interventions.keys():
        totruns.append(runs)
            
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
        PopulationParameters, DiseaseParameters = ParameterInput.SetRunParameters(ParametersInputData)
        DiseaseParameters['ImportationRate'] = int(modelvals['ImportationRate'])
        randomstate = random.getstate()
        mprandomseed = random.randint(100000,99999999)
        np.random.seed(seed=mprandomseed)
        endTime = (enddate - startdate).days
        DiseaseParameters['startdate'] = startdate
            
        DiseaseParameters = ParameterInput.setInfectionProb(interventions,key,DiseaseParameters,Model,fitdates=fitdates)
        
        resultsNameP = key + "_" + resultsName
                    
        fitted = GlobalModel.RunDefaultModelType(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper)
        if fitted:
            totruns[inton]-=1
            
    if generatePresentationVals == 1:
        interventionnames = []
        for key in interventions.keys():
            interventionnames.append(key)
        PDFP.Presentation(interventionnames,OutputRunsFolder,OutputResultsFolder)
                
       
            
        
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])
