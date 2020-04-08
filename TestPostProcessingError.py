
import ParameterSet
import os
import Utils

endTime = 181
modelPopNames = 'ZipCodes'
RegionalList = []
for i in range(0,88):
    RegionalList.append(i)
model = 'Maryland' 
resultsName = '2020315211826283462'
HospitalNames = {0: 'Meritus Health System (Wash. Co.)', 1: 'University of Maryland', 2: 'Prince Georges', 3: 'Holy Cross Hospital', 4: 'Frederick Memorial', 5: 'Mercy Medical Center', 6: 'Johns Hopkins', 7: 'UM Shore Medical Center at Dorchester ', 8: 'St. Agnes Hospital', 9: 'Lifebridge Sinai Hospital', 10: 'Washington Adventist', 11: 'Garrett County', 12: 'MedStar Montgomery General', 13: 'Peninsula Regional', 14: 'Suburban Hospital', 15: 'Anne Arundel Medical Center', 16: 'MedStar Union Memorial', 17: 'Western MD Health System ', 18: 'MedStar Saint Marys Hospital', 19: 'Johns Hopkins Bayview (acute)', 20: 'UM Shore Medical Center Chestertown (Formerly Chester River)', 21: 'Carroll County General', 22: 'MedStar Harbor Hospital', 23: 'UM Charles Regional Medical Center (Formerly Civista)', 24: 'UM Shore Medical Center at Easton ', 25: 'UMM Center Midtown Campus (chronic) (Formerly Maryland General)', 26: 'Calvert Memorial', 27: 'Lifebridge Northwest Hospital', 28: 'UM Baltimore Washington Medical Center', 29: 'Greater Baltimore Medical Center', 30: 'Howard General Hospital', 31: 'Doctors Community Hospital', 32: 'Greater Laurel Hospital (Formerly Gladys Spellman)', 33: 'MedStar Good Samaritan', 34: 'Shady Grove Adventist', 35: 'Fort Washington', 36: 'Atlantic General', 37: 'MedStar Southern Maryland (Formerly 210054)', 38: 'UM Saint Joseph (Formerly 210007)', 39: 'Holy Cross Hospital- Germantown', 40: 'Queens Annes Freestanding ER', 41: 'MedStar Franklin Square', 42: 'Bon Secours ', 43: 'Union of Cecil', 44: 'Upper Chesapeake Medical Center', 45: 'McCready', 46: 'Harford Memorial Hospital'}
HospitalOccupancyByDay = {}
for day in range(0, endTime + 1):
    hoc = []
    for h in range(0, len(HospitalNames)):
        hoc.append(0)
    HospitalOccupancyByDay[day] = hoc

for i in range(0,len(RegionalList)):
    if os.path.exists(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle"):
        CurrentHospOccList = Utils.FileRead(ParameterSet.PopDataFolder + "/" + str(modelPopNames) + str(i) + "HOSPLIST.pickle")
        for key in CurrentHospOccList.keys():
            lpdict = CurrentHospOccList[key]
            for key2 in lpdict:
                for h in range(0,len(lpdict[key2])):
                    if len(HospitalOccupancyByDay[key]) < len(lpdict[key2]):
                        k = len(lpdict[key2]) - len(HospitalOccupancyByDay[key])
                        if k > 0:
                            for kk in range(0,k):
                                HospitalOccupancyByDay[key].append(0)
                    HospitalOccupancyByDay[key][h] += lpdict[key2][h]

csvFile = ParameterSet.ResultsFolder+"/HospitalOccupancyByDay_"+model+"_"+resultsName+".csv"
try:
    with open(csvFile, 'w') as f:
        f.write("day")
        for h1 in range(0, len(HospitalNames)):
            f.write(",%s" % HospitalNames[h1])
        f.write("\n")        
        for key in HospitalOccupancyByDay.keys():
            f.write("%s" % key)
            for h in range(0, len(HospitalOccupancyByDay[key])):
                f.write(",%s" % HospitalOccupancyByDay[key][h])
            f.write("\n")

except IOError:
    print("I/O error")