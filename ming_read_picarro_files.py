def read_picarro(picarro_gases_filenames_i, lagtime, Hour_micros):
   picarro_data = [] 
   for i in range(len(picarro_gases_filenames_i)):
       with open(picarro_gases_filenames_i[i]) as f:
          picarro_data1 = f.readlines()[1:]
          picarro_data = np.hstack((picarro_data,picarro_data1))

#reads everything as a string, and does the row split    

   tt = [row.split()[0:2] for row in picarro_data]
   cavity_pressure = [row.split()[8] for row in picarro_data]
   cavity_temperature = [row.split()[9] for row in picarro_data]
   switch_state = [row.split()[16] for row in picarro_data]   
   ch4_air = [row.split()[17] for row in picarro_data]
   ch4_dry = [row.split()[18] for row in picarro_data]
   co2_air = [row.split()[19] for row in picarro_data]
   co2_dry = [row.split()[20] for row in picarro_data]
   h2o = [row.split()[21] for row in picarro_data]
 
   # datetimeList based on the timestamp from the PC
   datetimeList = [datetime.strptime(' '.join(row),'%Y-%m-%d   %H:%M:%S.%f') for row in tt]
   datetimeList_jul = [round(ii,1) for ii in [datetimeToTimestamp(row, withMilliseconds=True) for row in datetimeList]]
   if np.isnan(lagtime) or Hour_micros[-1]> datetimeList_jul[-1] or Hour_micros[0]< datetimeList_jul[0] or len(datetimeList_jul)<80000:
       hour_start_index = 0
       hour_end_index = 0
   else:
       hour_start_index = datetimeList_jul.index(round(Hour_micros[0] - lagtime,1))
       hour_end_index = datetimeList_jul.index(round(Hour_micros[-1] - lagtime,1))
   # Alternative datetimeList based on Picarro timestamp
#   tts = []
#   for j in range(len(cavity_pressure_torr)):
#       mlsec = repr(float(seconds[j])).split('.')[1][:3]
#       tts.append(time.strftime('%a %b %d %H:%M:%S.{} %Y'.format(mlsec), time.localtime(float(seconds[j]))))    
#   datetimeList = [datetime.strptime(row,'%a %b %d %H:%M:%S.%f %Y') for row in tts]
   length = hour_end_index - hour_start_index + 1
   gases_picarro_raw = np.zeros((length, 6))*0.
   k = 0
   for j in range(hour_start_index, hour_end_index+1):
      gases_picarro_raw[k,0] = float(datetimeList_jul[j])
      gases_picarro_raw[k,1] = float(co2_dry[j])
      gases_picarro_raw[k,2] = float(ch4_dry[j])
      gases_picarro_raw[k,3] = float(cavity_pressure[j])
      gases_picarro_raw[k,4] = float(cavity_temperature[j])
      gases_picarro_raw[k,5] = float(switch_state[j]) - 32.0
      k += 1
 
   gases_picarro_mean = np.nanmean(gases_picarro_raw, axis = 0)
   gases_picarro_4std = np.nanstd(gases_picarro_raw, axis = 0)*4
   gases_picarro = np.zeros((36000,6)) 
   gases_picarro[:,1:] = np.nan
   gases_picarro[:,0] = Hour_micros
   k = 0
   for j in range(36000):
      if k < len(gases_picarro_raw[:,0]) and round(Hour_micros[j] - lagtime,1) == gases_picarro_raw[k,0]: 
          if gases_picarro_raw[k,1] > 0 and gases_picarro_raw[k,1] < 500 and gases_picarro_raw[k,2] > 0 and gases_picarro_raw[k,2] < 10 \
             and gases_picarro_raw[k,3] > 140 and gases_picarro_raw[k,3] < 160 and gases_picarro_raw[k,4] > 50 and gases_picarro_raw[k,4] < 70 :
#             and abs(gases_picarro_raw[k,1]-gases_picarro_mean[1]) < gases_picarro_4std[1] and abs(gases_picarro_raw[k,2]-gases_picarro_mean[2]) < gases_picarro_4std[2]:
              gases_picarro[j,1] = gases_picarro_raw[k,1]
              gases_picarro[j,2] = gases_picarro_raw[k,2]
              gases_picarro[j,3] = gases_picarro_raw[k,3]
              gases_picarro[j,4] = gases_picarro_raw[k,4]
              gases_picarro[j,5] = gases_picarro_raw[k,5]
              k += 1
          else:
              k += 1
#   nan_where = np.where(np.isnan(gases_picarro[:,1])==0)  
#   id_nan = np.array(nan_where)[0]    
#      
#   if len(id_nan)/float(len(gases_picarro)) > 0.90:       
#        f_co2 = interpolate.interp1d(id_nan,gases_picarro[nan_where,1][0], kind = 'slinear', fill_value = 'extrapolate')  
#        f_ch4 = interpolate.interp1d(id_nan,gases_picarro[nan_where,2][0], kind = 'slinear', fill_value = 'extrapolate')  
#        f_cP = interpolate.interp1d(id_nan,gases_picarro[nan_where,3][0], kind = 'slinear', fill_value = 'extrapolate')  
#        f_cT = interpolate.interp1d(id_nan,gases_picarro[nan_where,4][0], kind = 'slinear', fill_value = 'extrapolate')  
#        f_sw = interpolate.interp1d(id_nan,gases_picarro[nan_where,5][0], kind = 'slinear', fill_value = 'extrapolate')  
#
#        gases_picarro[:,1] = f_co2(range(36000))
#        gases_picarro[:,2] = f_ch4(range(36000))
#        gases_picarro[:,3] = f_cP(range(36000))
#        gases_picarro[:,4] = f_cT(range(36000))
#        gases_picarro[:,5] = f_sw(range(36000))
#
#   else:
#        gases_picarro[:,:] = np.nan

 
   # Work out the decorrelation between the cavity pressure and the gas (CO2 and CH4)
   # rather than doing a simple mean, produce a linear fit
   # Create an array of same size as input_gas which increments at 0.1
#   time_s_array = np.zeros(len(fco2_air))*0.
#   for ss in range(len(fco2_air)):
#      time_s_array[ss] = float(ss)*0.1
#
#   m_press,press_c = np.polyfit(time_s_array,fcavity_pressure_torr,1)
#   press_lin = press_c + m_press*time_s_array
#   press_prime = fcavity_pressure_torr - press_lin
#
#   m_co2,co2_c = np.polyfit(time_s_array,fco2_dry,1)
#   co2_lin = co2_c + m_co2*time_s_array
#   co2_prime = fco2_dry - co2_lin
#
#   m_ch4,ch4_c = np.polyfit(time_s_array,fch4,1)
#   ch4_lin = ch4_c + m_ch4*time_s_array
#   ch4_prime = fch4 - ch4_lin
#   
#   press_cov = co2_prime*press_prime
#   mu_CO2 = np.mean(press_cov)/np.var(press_prime)
#
#   press_cov = ch4_prime*press_prime
#   mu_ch4 = np.mean(press_cov)/np.var(press_prime)
#
#   fco2_dry = fco2_dry - mu_CO2*press_prime
#   fch4 = fch4 - mu_ch4*press_prime
   return gases_picarro