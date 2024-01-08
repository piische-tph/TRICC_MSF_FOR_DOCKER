# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 12:02:01 2022
Collection of function that make
- xls form out of three dataframes (survey, choices and settings)
@author: kluera
"""

import pandas as pd
import os

def df2xlsform(df_survey, df_choices, df_settings, xlsfile):
 
    #create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(xlsfile, engine='xlsxwriter')
    
    df_survey.to_excel(writer, sheet_name='survey',index=False)
    df_choices.to_excel(writer, sheet_name='choices',index=False)
    df_settings.to_excel(writer, sheet_name='settings',index=False)
    
    writer.close()

    
def xls2xform(xlsfile, xmlfile):
    os.system('xls2xform ' + xlsfile + ' ' + xmlfile)


