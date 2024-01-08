# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 12:42:08 2022

@author: kluera
"""

import pandas as pd

def make_summary(df, df_choices, diagnose_id_hierarchy, summaryfile):
    df_diagnose=df.loc[diagnose_id_hierarchy]
    df_diagnose['relevance']='number(${' + df['name'] + '})=1'
    df_diagnose['appearance']='center'
    df_diagnose['type']='note'
    df_diagnose['label::en']='<p>' + df_diagnose['label::en'] + '</p>'
    df_diagnose['name']=df_diagnose['name'].replace({'d_':'label_'},regex=True)

    df_diagnose.index=df_diagnose.index+'label'
    
    intro = pd.read_excel(summaryfile).iloc[:5]
    
    extro = pd.read_excel(summaryfile).iloc[-3:]
    
    danger_signs = df_choices.loc[df_choices['list_name'].str.contains('select_signs') & ~df_choices['name'].str.contains('none')].copy()
    danger_signs['relevance']='selected(${' + danger_signs['list_name'] + '},\'' + danger_signs['name'] + '\')'
    danger_signs['type']='note'
    danger_signs['name']='label_' + danger_signs['name']
    danger_signs.index = danger_signs.index+'danger'
    
    df_summary = pd.concat([intro, df_diagnose, pd.read_excel(summaryfile).iloc[6:8], danger_signs, extro])
    
    
    df_summary.drop(columns=['list_name'], inplace = True)
    
    df_summary.fillna('', inplace=True)
    
    return df_summary
