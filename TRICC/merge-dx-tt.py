#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from pyxform import xls2xform
from datetime import datetime
import summary
import re
from bs4 import BeautifulSoup
from groupwrap import groupwrap
import cleanhtml as clh
import breakpoints as bp # implement the PAUSE function in CHT
from formconverters import df2xlsform # makes xlsforms out of dataframes
import translation
from datetime import datetime
import os
import shutil
import glob
import yaml
import sys

import warnings
warnings.filterwarnings("ignore")

# Load parameter send via sys.argv
conversion_ID = sys.argv[1]

# Get the working directory of the script
working_dir = os.getcwd()

# Config
config_path = "/app/uploads/"

# Function to load yaml configuration file
def load_config(config_name):
    with open(os.path.join(config_path, config_name)) as file:
        config = yaml.safe_load(file)

    return config

config = load_config(conversion_ID+"_config.yaml")

conversion_ID = config["conversion_ID"]
user_ID = config["user_ID"]
description = config["description"]
target_platform = config["target_platform"]


# Join the scripts path with "src/scripts/TRICC_MSF/TRICC/merge-dx-tt.py"
os.chdir(os.path.join(os.getcwd(), "/app/src/scripts/TRICC_MSF/"))

# In[2]:

#form_id = 'ped' # for MSFeCARE PED
form_id = 'ped' # for Almanach Lybia

#%% Parameters
# import params as p # for almanach Somalia
if form_id == 'ped':
    import params_ped as p # for msfecare Ped
elif form_id == 'almlib':
    import params_libya_rk as p


# In[6]

diagnose_order=p.diagnosis_order
cafile = p.folder+'ca.xlsx' #logic table for the relevance field of caretaker advice elements

#%% Run old legacy diagnostic jupyter notebook, that has been exported to a python file
os.system(f'python3 {p.repo_folder}tricc_dx.py')

#%% Run new tricc_tt script
os.system(f'python3 {p.repo_folder}tricc_tt.py')

# In[10]:
df_survey_dx = pd.read_excel(p.folder+p.form_id+'_dx.xlsx',sheet_name='survey')
df_survey_tt = pd.read_excel(p.output_xls,sheet_name='survey')
df_choices_dx = pd.read_excel(p.folder+p.form_id+'_dx.xlsx',sheet_name='choices')
df_choices_tt = pd.read_excel(p.output_xls,sheet_name='choices')

#%% Delete intermediate xls forms from disk
os.remove(p.folder+p.form_id+'_dx.xlsx') # for diagnostic
os.remove(p.output_xls) # for treatment

#%% Combine survey tabs of dx and ttos.remove(p.output_xls) # for treatment
df_dx = df_survey_dx
df_tt = df_survey_tt

#%% dropping standalone elements from the treatment

# in df_tt, drop all calculates, that have a name that is in diagnosis_order.csv
df_diagnoses = pd.read_csv(p.diagnosis_order)
df_tt.drop(df_tt.loc[df_tt['name'].isin(df_diagnoses['id'])].index, inplace=True)
# all rows that also appear in the headerfile
df_header = pd.read_excel(p.headerfile)
df_tt.drop(df_tt.loc[df_tt['name'].isin(df_header['name'])].index, inplace=True)
# all rows that also appear in the drugsfile
df_drugs = pd.read_excel(p.drugsfile)
df_tt.drop(df_tt.loc[df_tt['name'].isin(df_drugs['name'])].index, inplace=True)
# the rows with the combo 'note-data_loader'
df_tt.drop(df_tt.loc[(df_tt['type']=='note') & (df_tt['name']=='data_loader')].index, inplace=True)
# the rows with 'select_multiple select_diagnosis'
df_tt.drop(df_tt.loc[(df_tt['type']=='select_multiple select_diagnosis')].index, inplace=True)
# the rows with 'select_multiple select_dataload'
df_tt.drop(df_tt.loc[(df_tt['type']=='select_multiple select_dataload')].index, inplace=True)


#%% wrap treatment in a group
dfa = pd.DataFrame(columns=df_tt.columns)
tt_relevance = df_dx.loc[df_dx['label::en']=='TREATMENT','relevance'].values[0] # get relevance field for TT group
dfa.loc[0,['type','name','label::en', 'appearance', 'relevance']]=['begin group','g_tt', 'Treatment and Management', 'field-list', tt_relevance]
dfa.fillna('',inplace=True)
df_tt = pd.concat([dfa,df_tt],ignore_index=True)
dfa.loc[0]=''
dfa.loc[0,'type']='end group'
df_tt = pd.concat([df_tt, dfa],ignore_index=True)


# In[15]:


# insert treatment
df = df_dx
cut = df.loc[df['label::en']=='TREATMENT'].index[0]
df = pd.concat([df.iloc[:cut], df_tt, df.iloc[cut+1:]],ignore_index=True)

df.fillna('',inplace=True)

# drop the diagnoses and dm_ messages from the tt 
drops = df.loc[df.duplicated(subset='name',keep='first') & (df['name']!='') & (df['name']!='data_load') & ~df['type'].str.contains('group')].index
df.drop(drops,inplace=True)


# In[18]:


# drop duplicates after stitch
df.drop(df.loc[df.duplicated(subset='name', keep=False) & (df['name']!='') & (df['name']!='data_load')].index, inplace=True)


# ### Insert summary / report

# In[19]:


import pickle

# open a file, where you stored the pickled data
file = open(p.folder+'df_summary.pickle', 'rb')

# load information from that file
df_summary = pickle.load(file)

# close the file
file.close()


# In[20]:


# include into the form
df.reset_index(drop=True, inplace=True)
cut = df.loc[df['label::en']=='SUMMARY'].index[0]
df = pd.concat([df.iloc[:cut], df_summary, df.iloc[cut+1:]],ignore_index=True)


# ### Load contextual parameters from facility

# In[21]:


df_dataload = pd.read_excel(p.headerfile)
df = pd.concat([df_dataload,df],ignore_index=True)
df.fillna('', inplace = True)

if p.context_params_from_facility==True: 
    # the context parameters from the facility are stored in the calculate called data_load
    # when the user is allowed to manually set context parameters, this row is renamed to 'place_data_load' 
    # and there is a select_multiple with the name 'data_load"
    # in order to switch from manual context params to loading them from facility, one needs to drop the
    # select_multiple row
    df.drop(df.loc[(df['name']=='data_load') & df['type'].str.contains('select_', na=False)].index, inplace=True)  # drop manual data_load selector
    #df.loc[df['name']=='place_data_load', 'name'] = 'data_load'  # rename facility data_load


# In[22]:


df_survey = df.copy()


# In[ ]:





# ### Combine choices lists from dx and tt

# In[23]:


df_dx = df_choices_dx
df_tt = df_choices_tt


# In[24]:


# remove diagnoses from df_tt
diagnoses = list(pd.read_csv(diagnose_order)['id'])
df_tt.drop(df_tt.loc[df_tt['name'].isin(diagnoses)].index, inplace = True)
df_tt.reset_index(drop=True, inplace = True)
df_tt['label::en'] = df_tt['label::en'].apply(clh.html2plain)

# drop rows in df_tt that already exist in df_dx (they would be duplicated after concat)
# do a inner merge to get all those rows from df_dx (survey-options), that are repeated in df_tt (TT-options)
droprows = df_tt[['list_name', 'name']].reset_index().merge(df_dx[['list_name', 'name']], how='inner', on=['list_name', 'name']).set_index('index').index
df_tt.drop(droprows, inplace = True)


# In[25]:


# finally, the option from dx, that were included in tt to make it standalone 
df_tt.drop(df_tt.loc[(df_tt['list_name']=='data_load') & ~df_tt['name'].str.contains('load_')].index, inplace=True)


# In[26]:


# merge the two option lists
df_choices = pd.concat([df_dx, df_tt], ignore_index = True)
df_choices.fillna('', inplace = True)


# In[27]:


df = pd.concat([df_dx,df_tt],ignore_index=True)
# following step now obsolete as you sort the options based on 'y' value
# df.sort_values(by=['list_name','name'],inplace=True)  
df_choices=df


# ### Make a settings tab

# In[28]:


now = datetime.now()
version=now.strftime('%Y%m%d%H%M')
indx=[[1]]

settings={'form_title':p.form_title,'form_id':form_id,'version':version,'default_language':'en','style':'pages'}
df_settings=pd.DataFrame(settings,index=indx)


# ### clean html

# In[29]:


# # keep the tables, so that their html is not modified in the next step. 
df_tables = df_survey.loc[df_survey['name'].str.contains('table')]


# In[30]:


# mask for all columns containing text
m = df_survey.columns.str.contains('label') | df_survey.columns.str.contains('help')
textcols = df_survey.columns[m]
df_survey[textcols] = df_survey[textcols].applymap(clh.clean_html)


# In[31]:


# mask for help columns
m = df_survey['name'].str.contains('help_')
df_survey.loc[m,'label::en'] = df_survey.loc[m,'label::en'].apply(clh.make_green_background)


# In[32]:


# bring back the tables
df_survey.update(df_tables)


#%% Implement and export translations

#Extract strings from the dataframes and write them into an excel file for translation

# load the translation table
dft = pd.read_excel(p.input_trans)
dft.fillna('', inplace = True)
# Extracting strings from xls form:
dfl = translation.make_transtable(df_survey, df_choices)

# update the translation table by new and modified strings of the xls form
# print('In the new translation file:, \n')
dft_updated = translation.update_trans(dfl, dft)
# store it
dft_updated.to_excel(p.updated_trans, index = False)


# integrated translation

# import the new strings into the xls file: 
df_survey = translation.import_trans(df_survey, dft)
df_choices = translation.import_trans(df_choices, dft)


#%% Add a timestamp and name of the node to the text for higher convenience during testing

if p.testing == True: 
    m = (df_survey['name']!='') & ~df_survey['type'].str.contains('group', na=False)
    df_survey.loc[m, 'label::en']='---' + df_survey.loc[m, 'name'] + '---\n' + df_survey.loc[m, 'label::en']
    df_survey.loc[m, 'label::fr']='---' + df_survey.loc[m, 'name'] + '---\n' + df_survey.loc[m, 'label::fr']
    
    timestamprow_i = df_survey.loc[df_survey['name']=='data_load'].index-0.5
    timestamprow_i
    time = datetime.now()
    timestamprow = pd.DataFrame({'type':'note', 'name':'timestamp', 'label::en': 'Timestamp of build: '+str(time)}, index=timestamprow_i)
    df_survey = pd.concat([df_survey, timestamprow])
    df_survey = df_survey.sort_index()
    df_survey.reset_index(drop=True, inplace = True)


# ### hardcode add select_option filters for PED

# In[37]:


if form_id == 'ped':
    df_survey['choice_filter']=''
    df_survey.loc[df_survey['name']=='select_symptoms_other', 'choice_filter']='Min_age_months<=${p_age}'
    df_survey.loc[df_survey['name']=='major_symptoms', 'choice_filter']='Max_p_temp>=${p_temp}'
    df_choices['Min_age_months']=''
    df_choices['Max_p_temp']=''
    df_choices.loc[(df_choices['list_name']=='select_symptoms_other'),'Min_age_months']='2'
    df_choices.loc[(df_choices['list_name']=='major_symptoms'), 'Max_p_temp']='45'
    df_choices.loc[(df_choices['list_name']=='select_symptoms_other') & df_choices['name'].isin(['opt_9', 'opt_10']),'Min_age_months']='24'
    df_choices.loc[(df_choices['list_name']=='select_symptoms_other') & df_choices['name'].isin(['opt_9', 'opt_10']),'Min_age_months']='24'
    df_choices.loc[(df_choices['list_name']=='major_symptoms') & df_choices['name'].isin(['opt_1']), 'Max_p_temp']='37.5'


#%%Implement breakpoints

# the inputgroup has been concatenated before on top, so we know that we have to drop the first rows = length
if p.interrupt_flow:
    df_inputgroup = pd.read_excel(p.headerfile)
    df_inputgroup_a = pd.read_excel(p.headerfile_pause)

    endrow = len(df_inputgroup)
    df_survey_a = df_survey.drop(df_survey.iloc[:endrow].index)
    df_inputgroup_a.drop(0, inplace = True) # drop the begin inputs group row, because it is created by the make_breakpoints function

    df_pause = pd.read_csv(p.breakpoints)
    breaks = df_survey.loc[df_survey['name'].isin(df_pause['name'])].index
    breaknames = df_survey[df_survey['name'].isin(df_pause['name'])]['name']
    d={}
    
    # correct the relevance of the after pause message in the global flow
    # keep the old relevance before overwriting it
    # make it dependent on previous text field, if not it will appear also if form is not paused
    pause_old_relevance = df_survey.loc[df_survey['name']=='label_form_pause', 'relevance']
    pause_old_relevance = '(' + pause_old_relevance + ') and ${text_end}!=\'\''

#%% Delete the breakpoints csv-file
os.remove(p.breakpoints)

# In[39]:


if p.interrupt_flow:
    for i in breaks:
        dfa, hidden_names = bp.make_breakpoints(df_survey_a, i)
        tasks_strings = bp.get_tasksstrings(hidden_names, df_survey)
        breakname = breaknames[i]
        xlsname = p.output[:-5] + '_' + breakname + '.xlsx'
        xfname = p.output[:-5] + '_' + breakname + '.xml'
        #new settings tab:
        newsettings_frame= 'df_settings_' + '_' + breakname
        d[newsettings_frame] = df_settings.copy()
        d[newsettings_frame]['form_id'] = d[newsettings_frame]['form_id'] + '_' + breakname

        # where group inputs end, paste all the stuff from ped_
        endinputsrow = dfa.loc[(dfa['type']=='end group') & (dfa['name']=='inputs')].index[0]
        df_inputgroup_a.index = df_inputgroup_a.index /(len(df_inputgroup_a)+1)-1+endinputsrow
        # shift the elements that do not belong to group input out of group input
        index_a = df_inputgroup_a.loc[(df_inputgroup_a['type']=='end group') & (df_inputgroup_a['name']=='inputs')].index[0]
        df_inputgroup_a.loc[index_a:].index = df_inputgroup_a.loc[index_a:].index +1
        dfa = pd.concat([df_inputgroup_a, dfa])
        dfa.sort_index(inplace=True)
        # drop second end-group-inputs row
        duplicateendgrouprow = dfa.loc[(dfa['type']=='end group') & (dfa['name']=='inputs')].index[1]
        dfa.drop(duplicateendgrouprow, inplace = True)
        df2xlsform(dfa, df_choices, d[newsettings_frame], xlsname)
        # df2xlsform(df_survey, df_choices, df_settings, './'+xlsname)
        # print('Form to continue the algorithm after', breakname, 'created as file', xlsname)
        with open(p.output_folder+str(i)+'tasksjs.txt', 'w') as f:
            for i in tasks_strings:
                f.write(i+'\n')
        f.close()

    # missing: 
    # add acknowledge button that sends the user to the end
    # do this BEFORE you make the subflows, so that they include it automatically 


# In[40]:


if p.interrupt_flow:
    # interrupt after the pause question:
    df_survey.reset_index(drop=True, inplace=True)
    breakrow = df_survey.loc[df_survey['name']=='label_form_pause'].index[0]
    afterlab_indices = list(df_survey[breakrow:].index)
    m = df_survey.index.isin(afterlab_indices) & (df_survey['relevance']!='')
    df_survey.loc[m, 'relevance'] = '( ' + df_survey.loc[m, 'relevance'] + ') and (${ask_pause}=\'No\' or ${ask_pause}=\'\')'
    
    # write back the old relevance of the label_pause_form 
    df_survey.loc[df_survey['name']=='label_form_pause', 'relevance'] = pause_old_relevance

#%% for deceased cases in ped the ca is showing, find out later why.... no, don't, I don't want to know that. 
if form_id == 'ped':
    df_survey.loc[df_survey['name']=='g_tt', 'relevance'] = '(' + df_survey.loc[df_survey['name']=='g_tt', 'relevance'] + ') and ${d_deceased}=0'

#%% making the add missing diagnose field mandatory
df_survey.loc[df_survey['name']=='text_missing_diagnose_add', 'required']='true()'

#%% make the global flow
df2xlsform(df_survey, df_choices, df_settings, p.output)

#%% Zip the output
os.makedirs(p.folder + 'output_for_zip/',  exist_ok=True)
os.makedirs(p.folder + 'output/',  exist_ok=True)  # recursively create mediafolder, do nothing if it exists

# shutil.make_archive(p.zipfile, 'zip', p.output_folder)
shutil.make_archive(p.folder+'output/'+str(conversion_ID)+'_output', 'zip', p.output_folder)

# Move the file to another folder
shutil.move(p.folder+'output/'+str(conversion_ID)+'_output.zip', '/app/downloads/')

shutil.rmtree(p.output_folder)