import pandas as pd
import numpy as np
import os
import sys
# from datetime import datetime
import datetime
from datetime import timedelta
import random

testRegions = ['DC', 'MD']
resultsFileName = 'ResultsByDay_MDDCVAregion_distance.lowslowDensityFit'

start_day = '2020-02-10'
time_folder = sys.argv[1]
date_diff = datetime.datetime.fromisoformat(time_folder) - datetime.datetime.fromisoformat(start_day)
date_diff = date_diff.days


USStates = ['Alaska', 'Alabama', 'Arkansas', 'Arizona', 'California', 'Colorado', 'Connecticut', 'District of Columbia', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Iowa', 'Idaho', 'Illinois', 'Indiana', 'Kansas', 'Kentucky', 'Louisiana', 'Massachusetts', 'Maryland', 'Maine', 'Michigan', 'Minnesota', 'Missouri', 'Mississippi', 'Montana', 'North Carolina', 'North Dakota', 'Nebraska', 'New Hampshire', 'New Jersey', 'New Mexico', 'Nevada', 'New York', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Virginia', 'Vermont', 'Washington', 'Wisconsin', 'West Virginia', 'Wyoming']
USStatesAbbr = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']
USStatesCode = ['02', '01', '05', '04', '06', '08', '09', '11', '10', '12', '13', '15', '19', '16', '17', '18', '20', '21', '22', '25', '24', '23', '26', '27', '29', '28', '30', '37', '38', '31', '33', '34', '35', '32', '36', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '51', '50', '53', '55', '54', '56']
# colName = ['Day', 'Susceptible', 'Incubating', 'Infected', 'Colonized', 'Recovered', 'Dead', 'Hospitalized', 'NewAdmissions', 'EDVisits', 'ICU', 'Tests', 'Quarantined', 'numHousholdQuarantined', 'InfectiousEventsPrevented', 'confirmedcases']
quantiles = [0.010,0.025,0.050,0.100,0.150,0.200,0.250,0.300,0.350,0.400,0.450,0.500,0.550,0.600,0.650,0.700,0.750,0.800,0.850,0.900,0.950,0.975,0.990]
order = ["forecast_date","target","target_end_date","location","location_name","type","quantile","value"]
s = ['point']
s.extend(['quantile']*len(quantiles))
w = ['NA']
w.extend(quantiles)


def getData(input_folder, days_ahead, compartment, region):
    date_unformatted = datetime.datetime.fromisoformat(time_folder) + datetime.timedelta(days_ahead)
    time_next = date_unformatted.strftime('%Y-%m-%d')
  
    l_allfiles = []
    l_types = []
    for root, dirs, files in os.walk(input_folder, topdown=False):
        for filename in files:
            if resultsFileName in filename:
                datain = pd.read_csv(os.path.join(root, filename))
                compartment_ragion = compartment + '_' + region
                l_allfiles.append(datain.loc[date_diff+days_ahead,compartment_ragion])

    l_types.append(np.mean(l_allfiles))
    for i in quantiles:
        l_types.append(np.quantile(l_allfiles, i))

    d = pd.DataFrame(l_types,columns=['value'])
    d['forecast_date'] = time_folder
    if compartment == 'Dead':
        compartment_forCDC = 'death'
    d['target'] = str(days_ahead) + ' day ahead cum ' + compartment_forCDC
    d['target_end_date'] = time_next
    d['location'] = USStatesCode[USStatesAbbr.index(region)]
    d['location_name'] = USStates[USStatesAbbr.index(region)]
    d['type'] = s
    d['quantile'] = w
    d = d[order]

    return d    

############################ main ############################ 
final_df_list = []
for i in range(1, 101): 
    state_df_list = []
    for r in testRegions:
        state_df_list.append(getData(sys.argv[1],i,'Dead',r))

    state_df = pd.concat(state_df_list)

    final_df_list.append(state_df)

final_df = pd.concat(final_df_list)


final_df.to_csv(time_folder + '-CDDEP-GlobalAgentBasedModel.csv')

