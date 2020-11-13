
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
            print("HumidityDataMaxDate:",maxdate)
    
        except Exception as e:
            print("Humidity values error. Please confirm the Humidity file exists and is correctly specified")
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
                
    
    
    ## alter values related to transmission in Utils file
    dateTimeObj = datetime.now()
    overallResultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                  str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                  str(dateTimeObj.minute)
    
    if not os.path.exists(os.path.join('data',Model,modelvals['FitValFile'])) or modelvals['FitValFile'] == '':
        print("Error! Invalid fit file. Cannot find: '" + modelvals['FitValFile'] + "'. Please check that file exists and try running again!")
        exit()
    
    ParameterVals = FitModelInits.getFitModelParameters(Model,ParameterSet.FitModelRuns,append=True)
    
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
        
        fitinfo, fitdates = runRegionFit(FolderContainer,OutputRunsFolder,resultsName,Model,modelvals,enddate,ParameterVals[i],historyCaseData=historyCaseData,saveRun=False,SavedRegionFolder=os.path.join("data",Model,ParameterSet.SavedRegionContainer),encountersdata=encountersdata,humiditydata=humiditydata,burnin=False)
    
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
                        for x in range(min(fitdates),max(fitdates)):
                            f.write("HospDay"+str(x)+",")
                    if len(fitinfo['numFitDeaths']) > 0:
                        for x in range(min(fitdates),max(fitdates)):
                            f.write("DeathDay"+str(x)+",")
                    if len(fitinfo['numFitCases']) > 0:
                        for x in range(min(fitdates),max(fitdates)):
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
                
        PERIOD_OF_TIME = 39600 # 11 hours
    
        if time.time() > starttimer + PERIOD_OF_TIME : exit()         
            
def runRegionFit(FolderContainer,OutputRunsFolder,resultsName,Model,modelvals,enddate,PVals,historyCaseData={},saveRun=True,SavedRegionFolder=ParameterSet.SavedRegionFolder,encountersdata={},humiditydata={},burnin=True):
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
    
    StartInfected = -1
        
    ##### Do not delete
    modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is - this left here for compatibility - deprecated
    ######
        
    if ParameterSet.LoadHistory:                
        for reportdate in historyCaseData.keys():
            if reportdate != 'currentHospitalData':
                historyCaseData[reportdate]['timeval'] = (historyCaseData[reportdate]['ReportDateVal'] - startdate).days

                    
    fitinfo = GlobalModel.RunBurnin(Model,modelvals,modelPopNames,resultsName,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper,FolderContainer=os.path.join(FolderContainer,resultsName),saveRun=saveRun,historyData=historyCaseData,SavedRegionFolder=SavedRegionFolder,burnin=burnin)
            
    return fitinfo, fitdates
    
if __name__ == "__main__":
    # execute only if run as a script    
    main(sys.argv[1:])
