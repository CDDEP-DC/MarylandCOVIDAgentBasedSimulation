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

import random
import pickle
import os
import unicodedata
import string
import ParameterSet
from datetime import datetime
import sys, getopt
import traceback
import datetime as dt
import csv
import pandas as pd

def Multinomial(listvals):
    return multinomial(listvals,sum(listvals)) 

def multinomial(listvals,tot):
    totR = tot*random.random()
    idx = -1
    numtries = 0
    while totR > 0:
        idx = idx + 1
        totR = totR - listvals[idx]
        if numtries > 100:
            #print(HHSize+1," ",maxval," ",numdefinedagents, " " , infectperson)
            print("LOOP ERROR")
            break
    return idx
    
def PickleFileRead(fileName):
    pickle_in = open(os.path.abspath(os.getcwd())+"/"+fileName,"rb")
    obj = pickle.load(pickle_in)
    pickle_in.close()
    return obj
    
def PickleFileWrite(fileName,Obj):
    with open(os.path.abspath(os.getcwd())+"/"+fileName,"wb+") as f:
        pickle.dump(Obj, f)
    #pickle_out = open(os.path.abspath(os.getcwd())+"/"+fileName,"wb+")
    #pickle.dump(Obj, pickle_out)
    #pickle_out.close()

def WriteLogFile(logFile,errorstring):
    try:
        with open(logFile, 'w+') as f:
            f.write("***************************************************")
            dateTimeObj = datetime.now()
            timeNow = str(dateTimeObj.year) + "-" + str(dateTimeObj.month) + "-" + \
                  str(dateTimeObj.day) + " " + str(dateTimeObj.hour) + ":" +  \
                  str(dateTimeObj.minute) 
    
            f.write(timeNow)
            f.write(errorstring)
            
    except IOError:
        print("I/O error")
    
valid_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
char_limit = 255

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace spaces
    for r in replace:
        filename = filename.replace(r,'_')
    
    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    
    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename)>char_limit:
        print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]    

def deleteAllFilesInFolder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    
def dateparser(dateval):
    if isinstance(dateval,dt.date):
        return dateval
        
    # if in yyyy-mm-dd format
    if "-" in dateval:
        datelist = dateval.split("-")
        if int(datelist[0]) < 1900 or int(datelist[0]) > 2051:
            print(dateval,"year is greater than 2022 or less than 2020 or not in yyyy-mm-dd format correctly")
            raise Exception("Date Error")
        if int(datelist[1]) < 1 or int(datelist[1]) > 12:
            print(dateval,"month is greater than 12 or less than 1 or not in yyyy-mm-dd format correctly")
            raise Exception("Date Error")
        if int(datelist[2]) < 1 or int(datelist[2]) > 31:
            print(dateval,"day is greater than 31 or less than 1 or not in yyyy-mm-dd format correctly")
            raise Exception("Date Error")
        try:
            retdate = datetime.strptime(dateval, '%Y-%m-%d').date()        
            return retdate
        except:
            print(dateval," is not correctly formatted as yyyy-mm-dd.")
            raise Exception("Date Error")
            
    elif "/" in dateval:
        datelist = dateval.split("/")
        yearval = int(datelist[2])
        if yearval < 30:
            yearval += 2000
            dateval = datelist[0]+"/"+datelist[1]+"/"+str(yearval)
        if yearval < 2020 or yearval > 2022:
            print(dateval,"year is greater than 2022 or less than 2020 or not in mm/dd/yyyy format correctly")
            raise Exception("Date Error")
        if int(datelist[0]) < 1 or int(datelist[0]) > 12:
            print(dateval,"month is greater than 12 or less than 1 or not in mm/dd/yyyy format correctly")
            raise Exception("Date Error")
        if int(datelist[1]) < 1 or int(datelist[1]) > 31:
            print(dateval,"day is greater than 31 or less than 1 or not in mm/dd/yyyy format correctly")
            raise Exception("Date Error")
        try:
            retdate = datetime.strptime(dateval, '%m/%d/%Y').date()        
            return retdate
        except:
            print(dateval," is not correctly formatted as mm/dd/yyyy.")    
            raise Exception("Date Error")
    else:
        print(dateval,": Only yyyy-mm-dd and mm/dd/yyyy formats accepted now.")
        raise Exception("Date Error") 

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
                    
def ModelFolderStructureSetup(argv,paramsfile=False):

    try:
        runs = 100 # sets the number of times to run model - results print after each run to ensure that if the job fails the data is still there
        debug = False
        generatePresentationVals = False
        Model = 'MDDCVAregion'
        ParameterSet.FitMD = True
        ParametersFileName = ''
        # Function for passing in a job name for the containing folder - so this can be run multiple times in the same folder
        dateTimeObj = datetime.now()
        FolderContainer = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        try:
            opts, args = getopt.getopt(argv,"j:n:m:dgqf:hr:p:",["job=","nruns=","model="])
        except getopt.GetoptError as e:
            print('Error:',e)
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-j':
                fname = arg
                FolderContainer = clean_filename(fname)
            if opt == '-n':
                try:
                    nval = int(arg)
                    runs = nval
                except:
                    print("input number not an integer")
                
            if opt == '-d':
                 ParameterSet.logginglevel = "debug"   
                
            if opt == '-g':
                generatePresentationVals = True
                   
            if opt == '-q':
                ParameterSet.UseQueuesForQueues = True
            
            if opt == '-m':
                Model = arg        
                if Model != 'MDDCVAregion' and Model != 'MarylandFit':
                    ParameterSet.FitMD = False
                    
            if opt == '-f':
                ParameterSet.FitModel = True
                fval = arg
                if RepresentsInt(fval):
                    ParameterSet.FitModelRuns = int(fval)
                
            if opt == '-h':
                ParameterSet.LoadHistory = True
                    
            if opt == '-r':
                ParameterSet.UseSavedRegion = True    
                fname = arg
                ParameterSet.SavedRegionContainer = clean_filename(fname)
                
            if opt == '-p':
                fname = arg
                ParametersFileName = clean_filename(fname)
        
        if FolderContainer == ParameterSet.PopDataFolder or \
                FolderContainer == ParameterSet.QueueFolder or \
                FolderContainer == ParameterSet.ResultsFolder or \
                FolderContainer == ParameterSet.OutputFolder or \
                FolderContainer == "__pycache__":
            FolderContainer = FolderContainer + str(random.randint(100000,999999))
                    
        ParameterSet.PopDataFolder = os.path.join(ParameterSet.OperationsFolder,FolderContainer,ParameterSet.PopDataFolder)
        ParameterSet.QueueFolder = os.path.join(ParameterSet.OperationsFolder,FolderContainer,ParameterSet.QueueFolder)
        ParameterSet.ResultsFolder = os.path.join(ParameterSet.OperationsFolder,FolderContainer,ParameterSet.ResultsFolder)
        OutputResultsFolder = os.path.join(ParameterSet.OutputFolder,FolderContainer)
        SavedRegionFolder = os.path.join(ParameterSet.SavedRegionFolder,FolderContainer)
        
        if os.path.exists(os.path.join(ParameterSet.OperationsFolder,FolderContainer)):
            if os.path.exists(ParameterSet.PopDataFolder):
                deleteAllFilesInFolder(ParameterSet.PopDataFolder)
            if os.path.exists(ParameterSet.QueueFolder):
                deleteAllFilesInFolder(ParameterSet.QueueFolder)
            if os.path.exists(ParameterSet.ResultsFolder):
                deleteAllFilesInFolder(ParameterSet.ResultsFolder)
        else:
            os.makedirs(os.path.join(ParameterSet.OperationsFolder,FolderContainer))
                
        ### Below here is model runs and should not be altered
        if not os.path.exists(ParameterSet.PopDataFolder):
            os.makedirs(ParameterSet.PopDataFolder)
            
        if not os.path.exists(ParameterSet.QueueFolder):
            os.makedirs(ParameterSet.QueueFolder)
        
        if not os.path.exists(ParameterSet.ResultsFolder):
            os.makedirs(ParameterSet.ResultsFolder)
       
        if not os.path.exists(OutputResultsFolder):
            os.makedirs(OutputResultsFolder)    
        
        if not os.path.exists(SavedRegionFolder):
            os.makedirs(SavedRegionFolder)            
            
        if generatePresentationVals:
            OutputRunsFolder = os.path.join(ParameterSet.OutputFolder,FolderContainer,"runs")
            if not os.path.exists(OutputRunsFolder):
                os.makedirs(OutputRunsFolder)    
        else:
            OutputRunsFolder = OutputResultsFolder
    except:
        print(traceback.format_exc())
        raise Exception("Error in setup")
       
                     
    if paramsfile: 
        return runs, OutputResultsFolder, FolderContainer, generatePresentationVals, OutputRunsFolder, Model, ParametersFileName
    else:     
        return runs, OutputResultsFolder, FolderContainer, generatePresentationVals, OutputRunsFolder, Model

def getModelVals(Model):
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
                            startdate = dateparser(rows[i])
                        elif headers[i] == 'enddate':
                            enddate = dateparser(rows[i])
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
    return modelvals,startdate,enddate
        
def getHumidityData(Model,modelvals):
    humiditydata = {}
    if os.path.exists(os.path.join('data',Model,modelvals['humiditydatafile'])):
        try: 
            mindate = dateparser('2030-12-31')
            maxdate = dateparser('1976-05-31')
            maxdatestr = ''
            with open(os.path.join('data',Model,modelvals['humiditydatafile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    dateval = rows[headers.index('Date')]
                    addrow = False
                    try:
                        testdate = dateparser(dateval)
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
    return humiditydata
    
def getEncountersData(Model,modelvals):
    encountersdata = {}
    if os.path.exists(os.path.join('data',Model,modelvals['encountersfile'])):
        try: 
            mindate = dateparser('2030-12-31')
            maxdate = dateparser('1976-05-31')
            maxdatestr = ''
            with open(os.path.join('data',Model,modelvals['encountersfile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    dateval = rows[headers.index('Date')]
                    addrow = False
                    try:
                        testdate = dateparser(dateval)
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
                        try:
                            encountersdata[dateval]['RestNum50'] = rows[headers.index('RestNum50')]
                        except:
                            encountersdata[dateval]['RestNum50'] = 0
                        try:
                            encountersdata[dateval]['RestNum25'] = rows[headers.index('RestNum25')]
                        except:
                            encountersdata[dateval]['RestNum25'] = 0
                        try:
                            encountersdata[dateval]['RestNumClosed'] = rows[headers.index('RestNumClosed')]
                        except:
                            encountersdata[dateval]['RestNumClosed'] = 0

                            
        except Exception as e:
            print("Encounters values error. Please confirm the Encounters file exists and is correctly specified")
            if ParameterSet.logginglevel == "debug":
                print(traceback.format_exc())
            exit()    
    
    return encountersdata

def getParametersFile():
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
    
    return ParametersInputData
    
def getHistoryData(Model,modelvals):
    historyCaseData = {}
    currentHospitalData = []
    if ParameterSet.LoadHistory:
        if not os.path.exists(os.path.join('data',Model,modelvals['historyCaseFile'])):
            print("Case history file does not exists")
            exit()
            
        try: 
            mindate = dateparser('2030-12-31')
            maxdate = dateparser('1976-05-31')
            maxdatestr = ''
            with open(os.path.join('data',Model,modelvals['historyCaseFile']),mode='r') as infile:
                reader = csv.reader(infile)      
                headers = next(reader,None)
                for rows in reader:
                    dateval = rows[headers.index('ReportDate')]
                    addrow = False
                    try:
                        testdate = dateparser(dateval)
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
                        j = Multinomial(hospperlist)
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
                 	
    return historyCaseData, currentHospitalData    
    