# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 14:03:33 2022
Load calculate rows into df_survey (drug dosages, zscore calculations,...)
@author: kluera
"""
import pandas as pd

def loadcalc(df,filename, algotype):
    # first drop the row containing calculate - load_zscore
    df.drop(df.loc[df['name']=='load_z_score'].index,inplace=True)
    df.drop(df.loc[df['name']=='load_z_score_wa'].index,inplace=True)
    # df_choices.drop(df_choices.loc[df_choices['name']=='load_z_score'].index,inplace=True) # remove the option 'zscore' from the data_loader
    # df_choices.drop(df_choices.loc[df_choices['name']=='load_z_score_wa'].index,inplace=True) # remove the option 'zscore_wa' from the data_loader
    dfz=pd.read_excel(filename)
    
    dfz = dfz.loc[dfz['category'].str.contains(algotype)]
    
    dfz.fillna('',inplace=True)
    dfz.drop(labels=['category'], axis=1, inplace = True)
    dfz['index']=dfz['name'] + '_' + dfz['type']
    dfz.set_index('index', inplace=True)
    df=pd.concat([dfz,df])
    
    return df