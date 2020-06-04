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
import json

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
        ParametersInputData['ProbabilityOfTransmissionPerContact']['min'] = .02
    except Exception as e:
        print("Parameter input error. Please confirm the parameter file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug":
            print(traceback.format_exc())
        exit()
    
    ##### Do not delete
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is - this left here for compatibility - deprecated
    ######
    
    
    # load the death fit data
    try:
        USStates = ['Alabama','Arizona','Arkansas','California',
                     'Colorado','Connecticut','Delaware','District of Columbia','Florida',
                     'Georgia','Idaho','Illinois','Indiana','Iowa','Kansas',
                     'Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan',
                     'Minnesota','Mississippi','Missouri','Nebraska','Nevada',
                     'New Hampshire','New Jersey','New Mexico','New York','North Carolina',
                     'North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island',
                     'South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont',
                     'Virginia','Washington','West Virginia','Wisconsin','Montana','Hawaii','Wyoming','Alaska']
        USDeathsFileInfo = os.path.join('data',Model,'time_series_covid19_deaths_US.csv')
        deathdata = pd.read_csv(os.path.join("data",Model,'time_series_covid19_deaths_US.csv'))
        header = deathdata.columns.tolist()
        
        deathfitdata = {}
        deathfitdata['dates'] = []
        for i in range(header.index('1/22/20'),len(header)):
            deathfitdata['dates'].append(Utils.dateparser(header[i]))
            
        for state in USStates:
            deathfitdata[state] = {}
            deaths = []
            ststartdate = None
            maxval = 0
            stdate20 = None
            stdate100 = None
            for i in range(header.index('1/22/20'),len(header)):
                numdeaths = deathdata.loc[deathdata['Province_State'] == state][header[i]].sum()
                deaths.append(numdeaths)
                if not stdate20 and numdeaths >= 20:
                    stdate20 = Utils.dateparser(header[i])
                if not stdate100 and numdeaths >= 100:
                    stdate100 = Utils.dateparser(header[i])    
                if numdeaths > maxval:
                    maxval = numdeaths
                if not ststartdate and numdeaths > 0:
                    ststartdate = Utils.dateparser(header[i])
            #print(state)
            deathfitdata[state]['startdate'] = ststartdate 
            deathfitdata[state]['stdate20'] = stdate20
            deathfitdata[state]['stdate100'] = stdate100
            deathfitdata[state]['maxval'] = maxval
            deathfitdata[state]['deaths'] = deaths 
            
        
    except:
        print("CSV input error. Please confirm the time_series_covid19_deaths_US.csv file exists and is correctly specified")
        if ParameterSet.logginglevel == "debug":
            print(traceback.format_exc())
        exit()
    
    ### For fitting purposes
    fitper = float(modelvals['FitPer'])
    
    
    ## Get the folder run name
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
    
    enddate = (dateTimeObj + timedelta(days=30)).date()
                  
    for state in USStates:
        stepLength = 1
        
        
        #for intnum in range(0,len(interventionnames)):
        fitted = False
        attempt = 0
        while not fitted:
            print(state," attempt:",attempt)
            randomstate = random.getstate()
            mprandomseed = random.randint(100000,99999999)
            np.random.seed(seed=mprandomseed)
            startdate = (deathfitdata[state]['startdate'] - timedelta(days=random.randint(14,45)))
            endTime = (enddate - startdate).days
            # This sets the interventions
            interventions = ParameterInput.InterventionsParameters(Model,modelvals['intfile'],startdate)
            
            if len(interventions) == 0:
                print("Interventions input error. Please confirm the intervention file exists and is correctly specified")
                exit()
            key = list(interventions.keys())[0] # for now use the same for all states, can add each state individually later
            
            PopulationParameters, DiseaseParameters = ParameterInput.SetRunParameters(ParametersInputData)
            DiseaseParameters['ImportationRate'] = random.randint(1,int(modelvals['ImportationRate']))
            DiseaseParameters['startdate'] = startdate
            
                        
            # get fotvals and dates
            fitvals = []
            fitdates = []
            if deathfitdata[state]['maxval'] >= 1000:
                fitstartdate = deathfitdata[state]['stdate100']
            elif deathfitdata[state]['maxval'] >= 100:
                fitstartdate = deathfitdata[state]['stdate20']
            else:
                fitstartdate = deathfitdata[state]['startdate']
            for i in range(0,len(deathfitdata[state]['deaths'])):
                if deathfitdata['dates'][i] >= fitstartdate:
                    fitvals.append(deathfitdata[state]['deaths'][i])
                    fitdates.append((deathfitdata['dates'][i] - startdate).days)
            print(startdate)
            print(deathfitdata[state])
            
            DiseaseParameters = ParameterInput.setInfectionProb(interventions,key,DiseaseParameters,Model,fitdates=fitdates)
            
            resultsNameP = state + "_" + overallResultsName
                        
            fitted = GlobalModel.RunUSStateForecastModel(Model,state,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,fitdates=fitdates,deaths=deaths,fitper=fitper)
            
            if not fitted:
                attempt += 1
                if attempt > 50:
                    print("erroring out ... need to fix parameters for ",state)
                    fitted = True
                    attempt = 0
            else:
                attempt = 0  # reset for next state
            
    if generatePresentationVals == 1:
        interventionnames = []
        for key in interventions.keys():
            interventionnames.append(key)
        PDFP.Presentation(interventionnames,OutputRunsFolder,OutputResultsFolder)
                
       
            
        
if __name__ == "__main__":
    # execute only if run as a script
    
    main(sys.argv[1:])
