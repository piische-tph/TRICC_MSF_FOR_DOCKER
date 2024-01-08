#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 22:37:11 2022

@author: rafael
"""
import pandas as pd
import cleanhtml as ch
import re

def split_mh(df):
    '''Takes action on nodes that contain several text field headers at once it splits them into single notes and generates the proper edges
    takes as input the dataframe, when it still contains all elements, including edges returns the complete data frame. To be used before a 
    DAG is created.'''
    
    # first clean content of the nodes to be split (TTBox suffix, etc.)
    m = df['odk_type']=='note' # only note fields can be combined, so we work on those only
    df.loc[m,'value'] = df.loc[m,'value'].apply(lambda x: ch.clean_multi_headings(x)) 
    
    for i, row in df.loc[(df['odk_type']=='note')].iterrows():
        if len(row['value'])==1:
            row['value'] = row['value'][0]
            df.update(row.to_frame().transpose())
        else:
            row0 = row.copy()
            k = 0
            newrow = ''
            for j in row['value']:
                oldnewrow = newrow
                newrow = row0.copy()
                newrow.name = str(newrow.name)+str(k)
                newrow['id']=row0['id']+'-{:02d}'.format(k)
                newrow['value']=j
                df = pd.concat([df,newrow.to_frame().transpose()])
                if k == 0: #make incoming edges point to the first created node
                    df['target'] = df['target'].replace(row0['id'],newrow['id'])
                else:
                    d = {'id':row0['id']+'-{:03d}'.format(k), 'edge':'1', 'source':oldnewrow['id'],\
                     'target':newrow['id']}
                    df = pd.concat([df, pd.DataFrame(d, index = [str(newrow.name)+str(k)])])
                    if k == len(row['value'])-1: # make out-edges leave the last created node
                        df['source'] = df['source'].replace(row['id'],newrow['id'])
                k+=1
            df.drop(i, inplace = True)
    df.reset_index(drop=True, inplace = True)
    df.fillna('', inplace=True)
    
    # get rid of junk characters around the heading like 'TT Box «'
    df['value'] = [re.search('(?<=«).*?(?=»)',i).group(0) if re.search('(?<=«).*?(?=»)',i)!=None \
           else i for i in df['value']]

    m = df['odk_type']=='note'
    df.loc[m,'value'] = df.loc[m,'value'].apply(lambda x: ch.html2plain(x))
    df.loc[m, 'name'] = df['value']  # finally push the content of each note box into the name
    df['name'] = [re.sub(' ', '_', s) for s in df['name']]   # no spaces are allowed in odk names, replace with underscore
    
    return df