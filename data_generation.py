
import pandas as pd
import numpy as np
import itertools
import matplotlib.pylab as plt
from ChannelAttribution import markov_model
import os
import uuid

def generate_unique_id():
    return str(uuid.uuid4())

def save_df_to_csv(df, filename):
    # Get the current directory
    current_dir = os.getcwd()
    
    # Define the path to the neighboring 'datasets' folder
    datasets_dir = os.path.join(current_dir, '..', 'improved_datasets')
    
    # Create the 'datasets' directory if it doesn't exist
    os.makedirs(datasets_dir, exist_ok=True)
    
    # Create the full file path
    file_path = os.path.join(datasets_dir, filename)
    
    # Save the DataFrame to CSV
    df.to_csv(file_path, index=False)


# auth.authenticate_user()

# plt.style.use("fivethirtyeight")

# project_id = 'dataset-querying'

def listToString(df):
    str1 = ""
    for i in df['medium']:
        str1 += i + ' > '
    return str1[:-3]




def summarised_data_generation(data,datafilename):
  
  map_dictionary = {'organic': 'Search', '(none)': 'Direct',
                  'referral': 'Referral', 'cpc':'Paid Search',
                  'affiliate': 'Affiliate', 'cpm': 'Display Ad', '(not set)': 'Direct'}


  channel_conversion = data.copy()
  channel_conversion['conversion'] = channel_conversion['conversion'].fillna(0)
  channel_conversion['medium'] = channel_conversion['medium'].map(map_dictionary)

  channel_conversion = channel_conversion.groupby('medium').agg({'conversion':'sum', 'fullVisitorId': lambda x: x.nunique()}).sort_values('conversion',ascending=False).reset_index()
  channel_conversion['conversion_rate'] = (channel_conversion['conversion']/channel_conversion['fullVisitorId'])*100
  channel_conversion['conversion_rate'] = channel_conversion['conversion_rate'].map('{:,.1f}%'.format)

#   print(channel_conversion.head(10))


  medium_df = data.copy()
  medium_df = medium_df.fillna(0)


  medium_df['medium'] = medium_df['medium'].map(map_dictionary)

#   print(medium_df['medium'].value_counts())

  medium_df.loc[medium_df['conversion'] >= 1,'conversion']  = 1
#   print(medium_df['conversion'].value_counts())

  path_df = medium_df.groupby('fullVisitorId')['medium'].agg(lambda x: x.tolist()).reset_index()

#   print(path_df.head(5))

  visitor_df = medium_df.drop(columns=['medium'])

  path_df = pd.merge(path_df,visitor_df, how='left',on='fullVisitorId')
#   print(path_df.head(5))
#   print(path_df['conversion'].value_counts())


  path_df['medium'] = path_df.apply(listToString, axis=1)

#   print(path_df.head())
#   print(path_df['medium'].value_counts())



  path_df.drop(columns = 'fullVisitorId', inplace = True)
  path_df['null'] = np.where(path_df['conversion'] == 0 ,1,0)

  attribution_df = path_df.groupby(['medium'], as_index = False).sum()
  attribution_df.rename(columns={"conversion": "total_conversions", "null": "total_null", "value": "total_value"}, inplace = True)

#   print(attribution_df.head(10))
#   print(attribution_df['total_conversions'].value_counts())

  # week = i//7 + i


  #
  #
  #
  #

#   attribution_df.to_csv(f'path_week{week}.csv')
#   channel_conversion.to_csv(f'channel_conversion_week{week}.csv')


  M=markov_model(attribution_df, "medium", "total_conversions", var_value="total_value", flg_adv=False,verbose=True,out_more=True)

  # M['result']['attribution_conversion'] = M['result']['total_conversions']/M['result']['total_conversions'].sum()
  # M['result']['attribution_conversion_value'] = M['result']['total_conversion_value']/M['result']['total_conversion_value'].sum()

  for i in range(0,len(M['transition_matrix']['channel_to'])):
    if len(M['transition_matrix']['channel_to'][i])==1:
      M['transition_matrix']['channel_to'][i] = M['result']['channel_name'][int(M['transition_matrix']['channel_to'][i])-1]

    if len(M['transition_matrix']['channel_from'][i])==1:
      M['transition_matrix']['channel_from'][i] = M['result']['channel_name'][int(M['transition_matrix']['channel_from'][i])-1]

#   print(M['result'])
#   print(M['transition_matrix'])
#   print(M['removal_effects'])

  print('60% Complete')

  cuj = []
  ncuj = []


  for index, row in channel_conversion.iterrows():

    converted_user_joureney = []
    non_converted_user_joureney = []

    filtered_df =attribution_df[attribution_df['medium'].str.contains(row['medium'])]

    for filter_index,filter_row in filtered_df.iterrows():
      if filter_row['total_conversions'] > 0:
        converted_user_joureney.append([filter_row['medium'],filter_row['total_conversions']])
      if filter_row['total_null'] > 5:
        non_converted_user_joureney.append([filter_row['medium'],filter_row['total_null']])

    cuj.append(converted_user_joureney)
    ncuj.append(non_converted_user_joureney)

  channel_conversion['converted_user_journey'] = cuj
  channel_conversion['non_converted_user_journey'] = ncuj

  to_links = []
  from_links = []


  for index,row in channel_conversion.iterrows():
    tl = []
    fl = []

    filtered_df = M['transition_matrix'][M['transition_matrix']['channel_from'].str.contains(row['medium'])]

    for filter_index,filter_row in filtered_df.iterrows():
      tl.append([filter_row['channel_to'],filter_row['transition_probability']])

    to_links.append(tl)

    filtered_df = M['transition_matrix'][M['transition_matrix']['channel_to'].str.contains(row['medium'])]

    for filter_index,filter_row in filtered_df.iterrows():
      fl.append([filter_row['channel_from'],filter_row['transition_probability']])

    from_links.append(fl)

  channel_conversion['to_state'] = to_links
  channel_conversion['from_state'] = from_links

  channel_conversion = pd.merge(channel_conversion, M['result'], left_on='medium', right_on='channel_name', how='left')
  channel_conversion = pd.merge(channel_conversion, M['removal_effects'], left_on='medium', right_on='channel_name', how='left')


#   print(channel_conversion.head(10))


#   channel_conversion.to_csv(f'Master_week{week}.csv')
  
  # id = generate_unique_id()
  # save_df_to_csv(channel_conversion,datafilename)
  channel_conversion.drop(columns=['channel_name_x','channel_name_y','fullVisitorId'],inplace=True)
  channel_conversion.to_csv(f'./improved_datasets/{datafilename}')

  return id