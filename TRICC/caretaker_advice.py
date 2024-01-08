#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 09:58:58 2022
This file makes and appends a caretaker advice to the treatment
The TT drawing has a tab 'caretaker advice' that has all the fields
The relevance is derived from an excel table, in a file called 'cafile'

@author: rafael
"""

import pandas as pd

def ca_expressions(df_raw, cafile):
    df_ca = pd.read_excel(cafile)
    cols_cond = df_ca.columns[df_ca.columns.str.contains('cond')]
    cols_ca = df_ca.columns[~df_ca.columns.str.contains('cond')]
    
    # adding xform syntax:
    for i in cols_cond:
        df_ca.loc[~df_ca[i].isna(), i] = '${' + df_ca[i] + '}=1'
    
    df_ca.fillna('', inplace = True)
    
    # join all conditions with an 'and'
    df_ca['relevance'] = df_ca[cols_cond].apply(lambda x: ' and '.join(filter(None,x)) , axis=1)
    
    d = {}
    # replace x by condition
    for i in cols_ca:
        df_ca[i].loc[df_ca[i]=='x'] = df_ca['relevance']
        d[i] = ' or '.join(filter(None, df_ca[i]))
    
    return d

def update_ca_relevance(df, d):
    df.loc[df['name'].isin(d.keys()), 'relevance'] = [d[i] for i in df.loc[df['name'].isin(d.keys()), 'name']]   
    return(df)