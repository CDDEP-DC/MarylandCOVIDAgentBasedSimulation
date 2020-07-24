
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
    
    ## Setup the folder structure and the settings   
    try:
        runs, OutputResultsFolder, FolderContainer, generatePresentationVals, OutputRunsFolder, Model, ParametersRunFileName = Utils.ModelFolderStructureSetup(argv,paramsfile=True)
    except:
        print("Setup error. There was an error setting up the folders for output. Please ensure that you have permission to create files and directories on this system.")
        if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
            print(traceback.format_exc())
        exit()
    
        
    # check that the model exists in the Models file
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
    
    
    if not os.path.exists(os.path.join('data',Model,modelvals['FitValFile'])) or modelvals['FitValFile'] == '':
        print("Error! Invalid fit file. Cannot find: '" + modelvals['FitValFile'] + "'. Please check that file exists and try running again!")
        exit()
    
    # if the parameter file is passed in then we don't need to create     
    if len(ParametersRunFileName) == 0:
        print(ParametersRunFileName)
        ParametersFileName = "CurrentFittingParams.csv"
        
        FitModelInits.createParametersFile(Model,ParametersFileName,NumberMeanRuns = runs)
    
    ## Lock parameter file
    lockname = random.randint(1000000,9999999)
    continuerunning = True
    while continuerunning:
        
        waittime = 0
        while os.path.exists(os.path.join("data",Model,"CurrentFittingParams.lock")):
            time.sleep(1)
            waittime+=1
            print("waiting for lockfile")
            if waittime > 100:
                break
                
        try:            
            try:
                with open(os.path.join("data",Model,"CurrentFittingParams.lock"), 'w') as f:
                    f.write(str(lockname))
                    f.write("\n")
            except IOError:
                print("I/O error")        
                
            ParameterVals = {}                
            xrows = 0
            foundrow = -1
            csvFile = os.path.join('data',Model,ParametersFileName)
            foundfreerow = False
            with open(csvFile, mode='r') as infile:
                reader = csv.reader(infile)
                headers = next(reader, None)
                num = 0
                for rows in reader:
                    ParameterVals[num] = {}
                    hnum = 0
                    for h in headers:
                        if h == "locked":
                            if foundfreerow:
                                ParameterVals[num][h] = rows[hnum]
                                if rows[hnum] == "0":
                                    xrows+=1
                            else:
                                if rows[hnum] == "0":
                                    foundfreerow = True
                                    ParameterVals[num][h] = lockname
                                    foundrow = num
                                else:
                                    ParameterVals[num][h] = rows[hnum]
                        else:
                            ParameterVals[num][h] = rows[hnum]
                        hnum += 1
                    num+=1  
                      
            if foundfreerow:
                print("Still running ... found free parameter row. Still ",xrows," left")
                try:
                    with open(csvFile, 'w') as f:
                        lpvals = ParameterVals[0]
                        for key2 in lpvals.keys():
                            f.write(key2+",")
                        f.write("\n")
                        for key in ParameterVals.keys():
                            lpvals = ParameterVals[key]
                            for key2 in lpvals.keys():
                                f.write(str(lpvals[key2])+",")
                            f.write("\n")
            
                except Exception as e:
                    print("I/O Error writing CurrentFittingParams.")
                    if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                        print(traceback.format_exc())
                    exit()        
            else:
                continuerunning = False
                print("Finished running ... no more free parameter rows ... exiting")
                if os.path.exists(os.path.join("data",Model,"CurrentFittingParams.lock")):
                    os.remove(os.path.join("data",Model,"CurrentFittingParams.lock"))    
                exit()
                    
            if os.path.exists(os.path.join("data",Model,"CurrentFittingParams.lock")):
                os.remove(os.path.join("data",Model,"CurrentFittingParams.lock"))
                
        except:
            print("Error in getting Parameters")
            if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                print(traceback.format_exc())
            if os.path.exists(os.path.join("data",Model,"CurrentFittingParams.lock")):
                os.remove(os.path.join("data",Model,"CurrentFittingParams.lock"))    
            exit()   
        
        #### Now get all the parameters to fit the model    
        startDate = ParameterVals[foundrow]['startDate']              
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
        print(hospitalizations)
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
        PopulationParameters['householdcontactRate'] = float(ParameterVals[foundrow]['householdcontactRate'])
        
        DiseaseParameters = {}
        DiseaseParameters['AGHospRate'] = [float(ParameterVals[foundrow]['AG04HospRate']),float(ParameterVals[foundrow]['AG517HospRate']),float(ParameterVals[foundrow]['AG1849HospRate']),float(ParameterVals[foundrow]['AG5064HospRate']),float(ParameterVals[foundrow]['AG65HospRate'])]
        DiseaseParameters['AGAsymptomaticRate'] = [float(ParameterVals[foundrow]['AG04AsymptomaticRate']),float(ParameterVals[foundrow]['AG517AsymptomaticRate']),float(ParameterVals[foundrow]['AG1849AsymptomaticRate']),float(ParameterVals[foundrow]['AG5064AsymptomaticRate']),float(ParameterVals[foundrow]['AG65AsymptomaticRate'])]
        DiseaseParameters['AGMortalityRate'] = [float(ParameterVals[foundrow]['AG04MortalityRate']),float(ParameterVals[foundrow]['AG517MortalityRate']),float(ParameterVals[foundrow]['AG1849MortalityRate']),float(ParameterVals[foundrow]['AG5064MortalityRate']),float(ParameterVals[foundrow]['AG65MortalityRate'])]
        
        # Disease Progression Parameters
        DiseaseParameters['IncubationTime'] = float(ParameterVals[foundrow]['IncubationTime'])
        
        # gamma1
        DiseaseParameters['mildContagiousTime'] = float(ParameterVals[foundrow]['mildContagiousTime'])
        DiseaseParameters['AsymptomaticReducationTrans'] = float(ParameterVals[foundrow]['AsymptomaticReducationTrans'])
        
        # gamma2
        DiseaseParameters['preContagiousTime'] = float(ParameterVals[foundrow]['preContagiousTime'])
        DiseaseParameters['symptomaticTime'] = float(ParameterVals[foundrow]['symptomaticTime'])
        DiseaseParameters['postContagiousTime'] = float(ParameterVals[foundrow]['postContagiousTime'])
        DiseaseParameters['symptomaticContactRateReduction'] = float(ParameterVals[foundrow]['symptomaticContactRateReduction'])
        
        DiseaseParameters['preHospTime'] = float(ParameterVals[foundrow]['preHospTime'])
        DiseaseParameters['hospitalSymptomaticTime'] = float(ParameterVals[foundrow]['hospitalSymptomaticTime'])
        DiseaseParameters['ICURate'] = float(ParameterVals[foundrow]['ICURate'])
        DiseaseParameters['ICUtime'] = float(ParameterVals[foundrow]['ICUtime'])
        DiseaseParameters['PostICUTime'] = float(ParameterVals[foundrow]['PostICUTime'])
        DiseaseParameters['hospitalSymptomaticContactRateReduction'] = float(ParameterVals[foundrow]['hospitalSymptomaticContactRateReduction'])
        
        DiseaseParameters['pdscale1'] = .25
        DiseaseParameters['pdscale2'] = .001
        
        DiseaseParameters['EDVisit'] = float(ParameterVals[foundrow]['EDVisit'])
        
        DiseaseParameters['ProbabilityOfTransmissionPerContact'] = float(ParameterVals[foundrow]['ProbabilityOfTransmissionPerContact'])
        
        DiseaseParameters['CommunityTestingRate'] = 0.05    
               
        # This sets the interventions
        interventions = ParameterInput.InterventionsParameters(Model,modelvals['intfile'],startdate)
        if len(interventions) == 0:
            print("Interventions input error. Please confirm the intervention file exists and is correctly specified")
            exit() 
        
        print(interventions)    
        interventions['baseline']['InterventionReductionPerMin'] = float(ParameterVals[foundrow]['InterventionRate'])
        interventions['baseline']['InterventionReductionPerMax'] = float(ParameterVals[foundrow]['InterventionRate'])
        interventions['baseline']['InterventionReductionPerLowMin'] = float(ParameterVals[foundrow]['InterventionRateLow'])
        interventions['baseline']['InterventionReductionPerLowMax'] = float(ParameterVals[foundrow]['InterventionRateLow'])
                    
        stepLength = 1
        dateTimeObj = datetime.now()
        resultsName = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        
                
        DiseaseParameters['ImportationRate'] = int(ParameterVals[foundrow]['ImportationRate'])
        randomstate = random.getstate()
        mprandomseed = random.randint(100000,99999999)
        np.random.seed(seed=mprandomseed)
        endTime = (enddate - startdate).days
        DiseaseParameters['startdate'] = startdate
            
        key = 'baseline'
        DiseaseParameters = ParameterInput.setInfectionProb(interventions,key,DiseaseParameters,Model,fitdates=fitdates)
        
        resultsNameP = key + "_" + resultsName
                    
        StartInfected = -1
            
        ##### Do not delete
        modelPopNames = 'ZipCodes' # variable for namic files, is not important what it is - this left here for compatibility - deprecated
        ######
            
        fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases = GlobalModel.RunBurnin(Model,modelvals,modelPopNames,resultsNameP,PopulationParameters,DiseaseParameters,endTime,mprandomseed,stepLength=1,writefolder=OutputRunsFolder,startDate=startdate,fitdates=fitdates,hospitalizations=hospitalizations,deaths=deaths,fitper=fitper,FolderContainer=os.path.join(FolderContainer,resultsName),saveRun=True)
        
        waittime = 0
        while os.path.exists(os.path.join("data",Model,"CurrentRunningParams.lock")):
            time.sleep(1)
            waittime+=1
            print("waiting for lockfile")
            if waittime > 100:
                break
                
        try:
            try:
                with open(os.path.join("data",Model,"CurrentRunningParams.lock"), 'w') as f:
                    f.write(str(lockname))
                    f.write("\n")
            except IOError:
                print("I/O error")        
        
            
            try:
                addHeader = False
                if not os.path.exists(os.path.join("data",Model,"CurrentRunningParams.csv")):
                    addHeader = True
                
                with open(os.path.join("data",Model,"CurrentRunningParams.csv"), 'a+') as f:
                    lpvals = ParameterVals[foundrow]
                    if addHeader:
                        for key2 in lpvals.keys():
                            f.write(key2+",")
                        f.write("fitted, SLSH, SLSD, SLSC, avgperdiffhosp, avgperdiffdeaths, avgperdiffcases")
                        f.write("\n")
                    for key in lpvals.keys():
                        f.write(str(lpvals[key])+",")
                    if fitted:
                        f.write(str(fitted) + "," + str(SLSH) + "," + str(SLSD) + "," + str(SLSC) + "," + str(avgperdiffhosp) + "," + str(avgperdiffdeaths) + "," + str(avgperdiffcases))
                    else:
                        f.write(str(fitted) + "," + str(99999999) + "," + str(99999999) + "," + str(99999999) + "," + str(99999999) + "," + str(99999999) + "," + str(99999999))
                    f.write("\n")
        
            except IOError:
                print("I/O error")
                if os.path.exists(os.path.join("data",Model,"CurrentRunningParams.lock")):
                    os.remove(os.path.join("data",Model,"CurrentRunningParams.lock"))  
        except:
            if ParameterSet.logginglevel == "debug" or ParameterSet.logginglevel == "error":
                print(traceback.format_exc())
            if os.path.exists(os.path.join("data",Model,"CurrentRunningParams.lock")):
                os.remove(os.path.join("data",Model,"CurrentRunningParams.lock"))      
                
        if os.path.exists(os.path.join("data",Model,"CurrentRunningParams.lock")):
            os.remove(os.path.join("data",Model,"CurrentRunningParams.lock"))                  
            
if __name__ == "__main__":
    # execute only if run as a script    
    main(sys.argv[1:])
