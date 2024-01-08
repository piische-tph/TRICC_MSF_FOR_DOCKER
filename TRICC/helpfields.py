# -*- coding: utf-8 -*-
"""
Created on Wed Jul 20 10:21:16 2022

@author: kluera

change the appearance of help-fields: 
put the help field into a new label
put the label the help field comes from and the new help label itself in a group 
replace the label that contains the help field with that group
colorize the new help-label green and add as a heading: INFORMATION
"""

import pandas as pd

def concat_str(help_id):
    intro_en = 'For more information on '
    extro_en = ' click here'
    
    d_en = {'select_danger_signs':'convulsions',\
            'select_symptoms_further': 'apnoea and diarrhoea',\
            'select_danger_signs_additional': 'how to check for jaundice',\
            'label_phenobarbital': 'causes of convulsions',\
            'select_signs_warning_below31': 'normal developmental milestones',\
            'select_signs_warning_above31': 'normal developmental milestones',\
            'ask_spoonfeeding': 'how to feed a baby with a cup or spoon',\
            'ask_past_convulsions': 'convulsions'}


    if help_id in d_en.keys():
        en = d_en[help_id]
        en = intro_en + en + extro_en
    else:
        en = 'For more information click here:'

    return en    

def helpfields(df):
            
    df.reset_index(inplace=True)
    df.fillna('',inplace=True)
    I = df.loc[df['help::en']!=''].index
    print(I)
    
    for i in I:
        help_id = df.loc[i,'name']
        str_ackn = concat_str(help_id)
        
        begingroup = pd.DataFrame({'index':df.loc[i]['index']+'_begingroup',\
                                   'type': 'begin group', \
                                   'name':'g' + df.loc[i]['name'][5:], \
                                   'label::en':'NO_LABEL', \
                                   'appearance':'field-list', \
                                   'relevance':df.loc[i]['relevance']}, index=[i-0.1])
        acknowledge = pd.DataFrame({'index':df.loc[i]['index']+'_bool',\
                                    'type': 'acknowledge', \
                                    'name':'bool' + df.loc[i]['name'][5:], \
                                    'label::en':str_ackn}, index=[i])
        endgroup = pd.DataFrame({'index':df.loc[i]['index']+'_endgroup', 'type':'end group'}, index=[i+0.3])
        helpmessage = pd.DataFrame({'index':df.loc[i]['index']+'_help','type': 'note', \
                                    'name':'help_' + df.loc[i]['name'][5:], \
                                    'label::en': df.loc[i]['help::en'],\
                                    'relevance':'${bool' + df.loc[i]['name'][5:] + '}=\'OK\''}, index=[i+0.2])
        df.loc[i,'help::en']=='' # delete the help message inside the labels itself
        df.loc[i,'relevance']=='' # delete the relevance (it is now in the group)
        
        df = pd.concat([df, begingroup, acknowledge, helpmessage, endgroup])

    # colorize the help message and the acknowledge
    #m = df['name'].str.contains('help_',na=False)
    #color_p = '<p style="background-color:LightGray;color:MediumSeaGreen;font-size:80%;">'
    #df.loc[m,'label::en'] = color_p + df.loc[m,'label::en'] + '</p>'
    
    # sort rows
    df = df.sort_index()
    df.set_index('index',inplace=True)
    
    return df