#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Mon Nov 28 20:08:01 2022

@author: rafael kluender
'''
import inputs
import qualitychecks_pd as qcpd
import graphtools as gt
import odk_helpers as oh
import pandas as pd
import edgelogic as el
import networkx as nx
import cleanhtml as ch
import caretaker_advice as ca
import multiheadlinesplit as mhs
from datetime import datetime
from markdownify import markdownify as md
from utf8encoder import encodeUTF8 as utf8
from formconverters import df2xlsform # makes xlsforms out of dataframes
from formconverters import xls2xform # makes xlsforms out of dataframes
import xml_tools as xt

#%% Parameters - > choose your form (ped, yi, almsom) here
#import params_almsom_tt as p # for almanach Somalia
import params_test as p # for playing around
#import params_ped_tt as p # for msfecare Ped
#import params_libya as p # for Almanach Lybia treatment
#import params_libya_dx as p # for Almanach Lybia diagnostic
##%% Parse diagram
objects = inputs.parse_drawio(p.inputfile) # parse drawing

# Put diagram elements in df_raw
df_raw = inputs.treetodataframe(objects) # import drawing elements into a df
df_raw.fillna('', inplace = True) 
df_raw.loc[df_raw['label']!='','value'] = df_raw['label'] # all content into the same column

#%% Focus on treatment only and strip off the follow up (FOR NOW, in Almsom TT)
df_raw = df_raw.loc[df_raw['activity']!='Follow up advise']

#%% DAG 
# build a CDSS graph without images, WITH dataloader
dag = gt.build_graph_cdss(df_raw)

# make edge parents -> children (for select_xxx and pages)
dag = gt.connect_to_parents(dag, df_raw)

# connect shortcuts
dag = gt.connect_shortcuts(dag, df_raw)

# assign 'type', 'name', 'value' and group membership as attributes to nodes
dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['name'].apply(ch.html2plain), 'name')
dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['odk_type'], 'type')
dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['parent'], 'group')
#dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['y'], 'y')
# if you want to keep the html in the text:
if p.htmlcontent:
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['value'], 'content')
else: 
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['value'].apply(ch.html2plain), 'content')

# assign content of edges as their 'logic' attribute -> there are edges in the form that contain 'Yes' or 'No'
dag = gt.add_edgeattrib(dag, df_raw, 'logic')
