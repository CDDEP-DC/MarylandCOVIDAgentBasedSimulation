import random
import pickle
import os
import ParameterSet

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
    
def FileRead(fileName):
    pickle_in = open(os.path.abspath(os.getcwd())+"/"+fileName,"rb")
    obj = pickle.load(pickle_in)
    pickle_in.close()
    return obj
    
def FileWrite(fileName,Obj):
    with open(os.path.abspath(os.getcwd())+"/"+fileName,"wb+") as f:
        pickle.dump(Obj, f)
    #pickle_out = open(os.path.abspath(os.getcwd())+"/"+fileName,"wb+")
    #pickle.dump(Obj, pickle_out)
    #pickle_out.close()

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
    