
import sys, getopt
import random
import numpy as np
import math
import time
import pickle
from datetime import datetime
from datetime import date
import os
import csv
import unicodedata
import string
import pandas as pd
import traceback
import copy


import PostProcessing
import ParameterSet
import Utils
import GlobalModel
import ParameterInput
import FitModelInits




def main(argv):
    

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
    modelvals,startdate,enddate = Utils.getModelVals(Model)
    
    # load the vaccination data
    vaccinationdata = Utils.getVaccinationData(Model,modelvals)
    
    # load the humidity data
    humiditydata = Utils.getHumidityData(Model,modelvals)
        
    # load the essentialvisit file
    encountersdata = Utils.getEncountersData(Model,modelvals)
    
    
    # Load the parameters
    ParametersInputData = Utils.getParametersFile()
    
    ##### Do not delete
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is - this left here for compatibility - deprecated
    ######
    
    
    #### For loading history data to start at
    historyCaseData,currentHospitalData = Utils.getHistoryData(Model,modelvals)
    
    ## alter values related to transmission in Utils file
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
    
    if not os.path.exists(os.path.join('data',Model,modelvals['FitValFile'])) or modelvals['FitValFile'] == '':
        print("Error! Invalid fit file. Cannot find: '" + modelvals['FitValFile'] + "'. Please check that file exists and try running again!")
        exit()
    
    ParameterVals = FitModelInits.getFitModelParameters(Model,ParameterSet.FitModelRuns,append=False)
    
    if len(ParameterVals) < 1:
        print("Error creating parametervals for fitting")
        exit()           
    ######################################
    dateTimeObj = datetime.now()
    resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                  str(dateTimeObj.microsecond)
    for i in range(0,len(ParameterVals)):
        
        fitinfo, fitdates, fitdatesX = runRegionFit(FolderContainer,OutputRunsFolder,resultsName,Model,modelvals,enddate,ParameterVals[i],historyCaseData=historyCaseData,saveRun=False,SavedRegionFolder=os.path.join("data",Model,ParameterSet.SavedRegionContainer),encountersdata=encountersdata,humiditydata=humiditydata,vaccinationdata=vaccinationdata,burnin=True)
    
        try:
            addHeader = False
            if not os.path.exists(os.path.join(OutputResultsFolder,"ParameterVals"+resultsName+".csv")):
                addHeader = True
            
            with open(os.path.join(OutputResultsFolder,"ParameterVals"+resultsName+".csv"), 'a+') as f:
                
                lpvals = ParameterVals[i]
                if addHeader:
                    for key2 in lpvals.keys():
                        f.write(key2+",")
                    if len(fitinfo['numFitHospitalizations']) > 0:
                        for x in range(min(fitdatesX),max(fitdatesX)):
                            f.write("HospDay"+str(x)+",")
                    if len(fitinfo['numFitDeaths']) > 0:
                        for x in range(min(fitdatesX),max(fitdatesX)):
                            f.write("DeathDay"+str(x)+",")
                    if len(fitinfo['numFitCases']) > 0:
                        for x in range(min(fitdatesX),max(fitdatesX)):
                            f.write("CaseDay"+str(x)+",")        
                    f.write("\n")
                for key in lpvals.keys():
                    f.write(str(lpvals[key])+",")
                if len(fitinfo['numFitHospitalizations']) > 0:
                    for x in range(min(fitdates),max(fitdates)):
                        f.write(str(fitinfo['numFitHospitalizations'][x])+",")
                if len(fitinfo['numFitDeaths']) > 0:
                    for x in range(min(fitdates),max(fitdates)):
                        f.write(str(fitinfo['numFitDeaths'][x])+",")
                if len(fitinfo['numFitCases']) > 0:
                    for x in range(min(fitdates),max(fitdates)):
                        f.write(str(fitinfo['numFitCases'][x])+",")        
                f.write("\n")
    
        except:
            if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                print(traceback.format_exc())
        
        if time.time() > starttimer + ParameterSet.PERIOD_OF_TIME : exit()         
            
def runRegionFit(FolderContainer,OutputRunsFolder,resultsName,Model,modelvals,enddate,PVals,historyCaseData={},saveRun=True,SavedRegionFolder=ParameterSet.SavedRegionFolder,encountersdata={},humiditydata={},vaccinationdata={},burnin=True):
    #### Now get all the parameters to fit the model    
    startdate = Utils.dateparser(PVals['startDate'])
       
    ### For fitting purposes
    
    fitdates = []
    fitdatesorig = []
    hospitalizations = []
    deaths = []
    cases = []
    fitper = .3
    
    if not os.path.exists(os.path.join('data',Model,modelvals['FitValFile'])):
        print("Fitting file does not exist")
        exit()
        
    try:
        fitper = float(modelvals['FitPer'])
        #print(modelvals['FitValFile'])
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
    for fitdate in fitdatesorig:
        fitdates.append((fitdate - startdate).days)
        
    xdate = Utils.dateparser('2020-01-01')
    fitdatesX = []
    for fitdateX in fitdatesorig:
        fitdatesX.append((fitdateX - xdate).days)
        
    #agecohort 0 -- 0-4
    AG04GammaScale = 6
    AG04GammaShape = 2.1
    
    #agecohort 1 -- 5-17
    AG517GammaScale = 6
    AG517GammaShape = 3
    
    #agecohort 2 -- 18-49
    AG1849GammaScale = 6
    AG1849GammaShape = 2.5
     
    #agecohort 3 -- 50-64
    AG5064GammaScale = 6
    AG5064GammaShape = 2.3
            
    #agecohort 4 -- 65+
    AG65GammaScale = 6
    AG65GammaShape = 2.1
    
    AgeCohortInteraction = {0:{0:1.39277777777778,1:0.328888888888889,2:0.299444444444444,3:0.224444444444444,4:0.108333333333333},
                    1:{0:0.396666666666667,1:2.75555555555556,2:0.342407407407407,3:0.113333333333333,4:0.138333333333333},
                    2:{0:0.503333333333333,1:1.22666666666667,2:1.035,3:0.305185185185185,4:0.180555555555556},
                    3:{0:0.268888888888889,1:0.164074074074074, 2:0.219444444444444,3:0.787777777777778,4:0.27},
                    4:{0:0.181666666666667,1:0.138888888888889, 2:0.157222222222222,3:0.271666666666667,4:0.703333333333333}}

    PopulationParameters = {}                        
    PopulationParameters['AGGammaScale'] = [AG04GammaScale,AG517GammaScale,AG1849GammaScale,AG5064GammaScale,AG65GammaScale]
    PopulationParameters['AGGammaShape'] = [AG04GammaShape,AG517GammaShape,AG1849GammaShape,AG5064GammaShape,AG65GammaShape]
    PopulationParameters['AgeCohortInteraction'] = AgeCohortInteraction
    PopulationParameters['householdcontactRate'] = float(PVals['householdcontactRate'])
    
    DiseaseParameters = {}
    DiseaseParameters['AGHospRate'] = [float(PVals['AG04HospRate']),float(PVals['AG517HospRate']),float(PVals['AG1849HospRate']),float(PVals['AG5064HospRate']),float(PVals['AG65HospRate'])]
    DiseaseParameters['AGAsymptomaticRate'] = [float(PVals['AG04AsymptomaticRate']),float(PVals['AG517AsymptomaticRate']),float(PVals['AG1849AsymptomaticRate']),float(PVals['AG5064AsymptomaticRate']),float(PVals['AG65AsymptomaticRate'])]
    DiseaseParameters['AGMortalityRate'] = [float(PVals['AG04MortalityRate']),float(PVals['AG517MortalityRate']),float(PVals['AG1849MortalityRate']),float(PVals['AG5064MortalityRate']),float(PVals['AG65MortalityRate'])]
    
    # Disease Progression Parameters
    DiseaseParameters['IncubationTime'] = float(PVals['IncubationTime'])
    
    # gamma1
    DiseaseParameters['mildContagiousTime'] = float(PVals['mildContagiousTime'])
    DiseaseParameters['AsymptomaticReducationTrans'] = float(PVals['AsymptomaticReducationTrans'])
    
    # gamma2
    DiseaseParameters['preContagiousTime'] = float(PVals['preContagiousTime'])
    DiseaseParameters['symptomaticTime'] = float(PVals['symptomaticTime'])
    DiseaseParameters['postContagiousTime'] = float(PVals['postContagiousTime'])
    DiseaseParameters['symptomaticContactRateReduction'] = float(PVals['symptomaticContactRateReduction'])
    
    DiseaseParameters['preHospTime'] = float(PVals['preHospTime'])
    DiseaseParameters['hospitalSymptomaticTime'] = float(PVals['hospitalSymptomaticTime'])
    DiseaseParameters['ICURate'] = float(PVals['ICURate'])
    DiseaseParameters['ICUtime'] = float(PVals['ICUtime'])
    DiseaseParameters['PostICUTime'] = float(PVals['PostICUTime'])
    DiseaseParameters['hospitalSymptomaticContactRateReduction'] = float(PVals['hospitalSymptomaticContactRateReduction'])
    
    DiseaseParameters['pdscale1'] = .25
    DiseaseParameters['pdscale2'] = .001
    
    DiseaseParameters['EDVisit'] = float(PVals['EDVisit'])
    
    DiseaseParameters['ProbabilityOfTransmissionPerContact'] = float(PVals['ProbabilityOfTransmissionPerContact'])
    
    DiseaseParameters['CommunityTestingRate'] = 0.05    
    DiseaseParameters['humidityversion'] = -1
    
    DiseaseParameters['TestIncreaseDate'] = (Utils.dateparser("2020-07-01") - startdate).days
    DiseaseParameters['TestIncrease'] = float(PVals['TestIncrease'])
    
           
    # This sets the interventions
    interventions = ParameterInput.InterventionsParameters(Model,modelvals['FitInterventionFile'],startdate)
    if len(interventions) == 0:
        print("Interventions input error. Please confirm the intervention file exists and is correctly specified")
        exit() 
    
    
    interventions['baseline']['InterventionReductionPerMin'] = float(PVals['InterventionRate'])
    interventions['baseline']['InterventionReductionPerMax'] = float(PVals['InterventionRate'])
    interventions['baseline']['InterventionReductionPerLowMin'] = float(PVals['InterventionRateLow'])
    interventions['baseline']['InterventionReductionPerLowMax'] = float(PVals['InterventionRateLow'])
    interventions['baseline']['InterventionEndPerIncrease'] = float(PVals['InterventionEndPerIncrease'])
    #interventions['baseline']['InterventionEndPerIncrease'] = float(PVals['InterventionPerIncrease'])
    #print(interventions)                
    stepLength = 1
                
    DiseaseParameters['ImportationRate'] = int(PVals['ImportationRate'])
    randomstate = random.getstate()
    mprandomseed = random.randint(100000,99999999)
    np.random.seed(seed=mprandomseed)
    endTime = (enddate - startdate).days
    DiseaseParameters['startdate'] = startdate
    DiseaseParameters['enddate'] = enddate
        
    key = 'baseline'
    DiseaseParameters = ParameterInput.setInfectionProb(interventions,key,DiseaseParameters,Model,fitdates=fitdates,encountersdata=encountersdata,humiditydata=humiditydata)
    print("FitModelRegions:TransProb_AH Len:",len(DiseaseParameters['TransProb_AH']))
    DiseaseParameters['VaccinationType'] = interventions['baseline']['VaccinationType']
    
    StartInfected = -1
        
    ##### Do not delete
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is - this left here for compatibility - deprecated
    ######
        
    if ParameterSet.LoadHistory:                
        for reportdate in historyCaseData.keys():
            if reportdate != 'currentHospitalData':
                historyCaseData[reportdate]['timeval'] = (historyCaseData[reportdate]['ReportDateVal'] - startdate).days

                       
    fitinfo = GlobalModel.RunBurnin(Model,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper,FolderContainer=os.path.join(FolderContainer,resultsName),saveRun=saveRun,historyData=historyCaseData,SavedRegionFolder=SavedRegionFolder,burnin=burnin,vaccinationdata=vaccinationdata)
            
    return fitinfo, fitdates, fitdatesX
    
if __name__ == "__main__":
    # execute only if run as a script    
    main(sys.argv[1:])
