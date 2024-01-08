# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:10:58 2022

@author: kluera

Make a follow up message
"""
import pandas as pd
from bs4 import  BeautifulSoup

def clean_name(s):
    s = s.lower()
    s = s.replace(' ','')
    return s

def fup(introfile,extrofile,fupfile,diagnosefile,df_survey):


    dfup= pd.read_excel(fupfile)
    dfd = pd.read_csv(diagnosefile)

    dfup['Diseases'] = dfup['Diseases'].apply(clean_name)
    dfd['Name'] = dfd['Name'].apply(clean_name)

    dfup = dfup.merge(dfd[['Name','id']],how='left',left_on='Diseases',right_on='Name')

    # check if all diseases were matched
    if dfup['id'].isna().sum() != 0:
        print('Some diagnoses were not matched in the Follow Up message table.')
    

    with open(introfile) as fp:
        soup = BeautifulSoup(fp, 'html.parser')
        intro = soup.find('div')
        intro = intro.decode_contents()
        
        with open(extrofile) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
        extro = soup.find('div')
        extro = extro.decode_contents()

    fup_specific = dfup.columns[1]
    fupmessage = intro + '\n' + fup_specific + '\n' + extro
    label = [s for s in df_survey.columns if 'label' in s][0]
    fup = pd.DataFrame({'type':'note','name':'label_cta',label:fupmessage},index=['fup'])

    dfup['expression'] = '${' + dfup['id'] + '}*' + dfup.iloc[:,1].astype(str)
    
    calculate_expression = ' '.join(dfup.expression)
    relevance = calculate_expression.replace('*1','=1 or ')
    calculate_expression = 'min(' + calculate_expression + ')'
    
    daysfup = pd.DataFrame({'type':'calculate','name':'daysfup','calculation':calculate_expression},index=['daysfup'])
    begingroup = pd.DataFrame({'type':'begin group','name':'g_fup','relevance':relevance},index=['beginfupgroup'])
    endgroup = pd.DataFrame({'type':'end group'},index=['endfupgroup'])
    df = pd.concat([df_survey,begingroup,fup,daysfup,endgroup]) 
    
    return df


