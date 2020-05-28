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
    # if in yyyy-mm-dd format
    if "-" in dateval:
        datelist = dateval.split("-")
        if int(datelist[0]) < 2020 or int(datelist[0]) > 2022:
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
                    
def ModelFolderStructureSetup(argv):

    try:
        runs = 100 # sets the number of times to run model - results print after each run to ensure that if the job fails the data is still there
        debug = False
        generatePresentationVals = False
        Model = 'MDDCVAregion'
        ParameterSet.FitMD = True
        # Function for passing in a job name for the containing folder - so this can be run multiple times in the same folder
        dateTimeObj = datetime.now()
        FolderContainer = str(dateTimeObj.year) + str(dateTimeObj.month) + \
                      str(dateTimeObj.day) + str(dateTimeObj.hour) + \
                      str(dateTimeObj.minute) + str(dateTimeObj.second) + \
                      str(dateTimeObj.microsecond)
        try:
            opts, args = getopt.getopt(argv,"j:n:m:dgqf:",["job=","nruns=","model="])
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
                if Model != 'MDDCVAregion':
                    ParameterSet.FitMD = False
                    
            if opt == '-f':
                ParameterSet.FitModel = True
                if arg != 'hospitalizations' and arg != 'deaths' and arg != 'both':
                    print("Can only fit to 'hospitalizations' or 'deaths' or 'both'")
                    raise Exception("Invalid fitting command")
                else:
                    ParameterSet.FitValue = arg
                    
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
        
        if generatePresentationVals:
            OutputRunsFolder = os.path.join(ParameterSet.OutputFolder,FolderContainer,"runs")
            if not os.path.exists(OutputRunsFolder):
                os.makedirs(OutputRunsFolder)    
        else:
            OutputRunsFolder = OutputResultsFolder
    except:
        print(traceback.format_exc())
        raise Exception("Error in setup")
                    
    return runs, OutputResultsFolder, FolderContainer, generatePresentationVals, OutputRunsFolder, Model
        
#def JiggleParameters(case='reg'):
#    #B1=0.49997542 B2=0.49990543 gamma1=0.32194843 gamma2=0.0300116  gamma3=0.21929508    
#    #agecohort 0 -- 0-4                     
#    baseAG04AsymptomaticRate = .99
       
#    #agecohort 1 -- 5-17
#    baseAG517AsymptomaticRate = .93
            
#    #agecohort 2 -- 18-49
#    baseAG1849AsymptomaticRate = .7
            
#    #agecohort 3 -- 50-64
#    baseAG5064AsymptomaticRate = .6
            
#    #agecohort 4 -- 65+
#    baseAG65AsymptomaticRate = .5

    
#    baseEDVisit = .8
    
#    ParameterSet.IncubationTime = random.randint(5,7)
#    ParameterSet.totalContagiousTime = random.randint(5,9)
#    ParameterSet.symptomaticTime = random.randint(5,9)
#    ParameterSet.hospitalSymptomaticTime = random.randint(6,12)
#    ParameterSet.hospTime = random.randint(3,5) 
#    ParameterSet.preContagiousTime = random.randint(1,3)
#    ParameterSet.postContagiousTime = random.randint(1,3)
#    ParameterSet.ICUtime = random.randint(12,15)
#    ParameterSet.PostICUTime = random.randint(5,9)
    
#    ParameterSet.householdcontactRate = random.randint(6,9)
    
#    ParameterSet.AG04AsymptomaticRate = min(baseAG04AsymptomaticRate+random.choice((-1, 1))*baseAG04AsymptomaticRate*.02*random.random(),1)
#    ParameterSet.AG04HospRate = random.randint(0,75)/10000
       
#    #agecohort 1 -- 5-17
#    ParameterSet.AG517AsymptomaticRate = min(baseAG517AsymptomaticRate+random.choice((-1, 1))*baseAG517AsymptomaticRate*.05*random.random(),1)
#    ParameterSet.AG517HospRate = random.randint(80,160)/10000
            
#    #agecohort 2 -- 18-49
#    ParameterSet.AG1849AsymptomaticRate = min(baseAG1849AsymptomaticRate+random.choice((-1, 1))*baseAG1849AsymptomaticRate*.05*random.random(),1)
#    ParameterSet.AG1849HospRate = random.randint(5,10)/100
#    ParameterSet.AG1849MortalityRate = 0.01
        
#    #agecohort 3 -- 50-64
#    ParameterSet.AG5064AsymptomaticRate = min(baseAG5064AsymptomaticRate+random.choice((-1, 1))*baseAG5064AsymptomaticRate*.05*random.random(),1)
#    ParameterSet.AG5064HospRate = random.randint(5,10)/100
#    ParameterSet.AG5064MortalityRate = 0.08

#    #agecohort 4 -- 65+
#    ParameterSet.AG65AsymptomaticRate = min(baseAG65AsymptomaticRate+random.choice((-1, 1))*baseAG65AsymptomaticRate*.1*random.random(),1)
#    ParameterSet.AG65HospRate = random.randint(16,25)/100
#    ParameterSet.AG65MortalityRate = 0.20

        
#    ParameterSet.EDVisit = min(baseEDVisit+random.choice((-1, 1))*baseEDVisit*.05*random.random(),1)
#    ParameterSet.ProbabilityOfTransmissionPerContact = random.randint(95,105)/1000
#    ParameterSet.ICURate = random.randint(40,60)/100
       
#    ParameterSet.symptomaticContactRateReduction = random.randint(30,40)/100 
    
#    ParameterSet.AGHospRate = [ParameterSet.AG04HospRate,ParameterSet.AG517HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG1849HospRate,ParameterSet.AG5064HospRate,ParameterSet.AG65HospRate]
#    ParameterSet.AGAsymptomaticRate = [ParameterSet.AG04AsymptomaticRate, ParameterSet.AG517AsymptomaticRate, ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate,ParameterSet.AG1849AsymptomaticRate, ParameterSet.AG5064AsymptomaticRate,ParameterSet.AG65AsymptomaticRate]
#    ParameterSet.AGMortalityRate = [ParameterSet.AG04MortalityRate,ParameterSet.AG517MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG1849MortalityRate,ParameterSet.AG5064MortalityRate,ParameterSet.AG65MortalityRate]

#    ParameterSet.ImportationRate = random.randint(10,25)
#    ParameterSet.AsymptomaticReducationTrans = random.randint(60,70)/100
    