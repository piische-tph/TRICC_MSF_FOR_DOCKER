# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 12:49:48 2022

group the treatment part into a group. 
Due to a bug in CHT, the 'Is referral possible?' question must be outside of the group. It triggers note fields that then have
no drugs dosages and weight loaded. 
The workaround is to start the group right after that question and not before. 
There are many other questions inside the MSF TT YI flow, that probably lead to the same issue. I have no solution for this. 

@author: kluera
"""

import pandas as pd

def groupwrap(df):       
    df.reset_index(inplace=True)
    df.fillna('',inplace=True)
    i = df.loc[df['label::English (en)']=='Is referral possible?'].index[0]
    print(i)   
    begingroup = pd.DataFrame({'index':'g_' + str(df.loc[i]['index']),\
                               'type': 'begin group', \
                               'name':'g_tt', \
                               'label::English (en)':'Treatment and Management', \
                               'label::French (fr)':'Traitement et Accompagnement', \
                               'appearance':'field-list'}, index=[i+0.1])

    endgroup = pd.DataFrame({'index':'g_end' + str(df.loc[i]['index']), 'type':'end group'}, index=[len(df)+0.1])
 
    
    df = pd.concat([df, begingroup, endgroup])

    
    # sort rows
    df = df.sort_index()
    df.set_index('index',inplace=True)
    
    return df