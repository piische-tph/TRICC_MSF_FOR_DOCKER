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
import params as p # for almanach Somalia
#import params_ped as p # for msfecare Ped

#%% Parse diagram
objects = inputs.parse_drawio(p.inputfile_tt) # parse drawing

# Put diagram elements in df_raw
df_raw = inputs.treetodataframe(objects) # import drawing elements into a df
df_raw.fillna('', inplace = True) 
df_raw.loc[df_raw['label']!='','value'] = df_raw['label'] # all content into the same column

#%% Focus on treatment only and strip off the follow up (FOR NOW)
df_raw = df_raw.loc[df_raw['activity']!='Follow up advise']

#%% Quality checks
qcpd.check_node_type(df_raw) # check if all objects have an odk_type
qcpd.check_rhombus_refer(df_raw) # check if all rhombus refer to an existing node
qcpd.check_edge_connection(df_raw) # check if all edges are well connected
types = ['rhombus', 'select_one yesno']
qcpd.check_edge_yesno(df_raw, types) # check if all edges leaving rhombus and select_one yesno have Yes/No

#%% assign diagnosis names to rows in df_raw
df_raw = oh.assign_diagnosisname(p.diagnosis_order, df_raw)

#%% Split multiple header lines into singleton objects (for Alm Som)
if p.form_id=='almsom':
    df_raw = mhs.split_mh(df_raw)
    
#%% Build the choices tab
df_choices=df_raw.loc[df_raw['odk_type']=='select_option']
df_choices=df_choices.merge(df_raw[['name','odk_type','id']],how='left',left_on='parent',right_on='id')
df_choices=df_choices[['name_y','name_x','value']]
df_choices.rename({'name_y':'list_name','name_x':'name','value':'label::en'},axis=1,inplace=True)

# add rows for yesno
yes=pd.DataFrame({'list_name':'yesno','name':'Yes','label::en':'Yes'}, index=['zzz_yes'])
no=pd.DataFrame({'list_name':'yesno','name':'No','label::en':'No'}, index=['zzz_no'])
df_choices = pd.concat([df_choices, yes, no])

#%% DAG 
# build a CDSS graph without images, WITH dataloader
dag = gt.build_graph_cdss(df_raw)

# make edge parents -> children (for select_xxx and pages and container-hint-media this does not exist per default)
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

#%% Write help and hint fields as node attributes
dag = gt.make_help_attributes(dag)

#%% Add diagnosis selector and dataloader to DAG
'''
diagnosis_id_hierarchy = gt.get_diagnosis_sorting_id(df_raw, p.diagnosis_order) # make diagnosis id hierarchy list

n = 'select_diagnosis'
n_attrib = {'name':'select_diagnosis', 'type':'select_multiple', 'content':'Select diagnosis', 'group' : 1}
dag = gt.add_calculate_selector(dag, n, n_attrib, diagnosis_id_hierarchy)
# add the content from the calculates as content to their predecessor select_options
dag = gt.add_text_calculate_options(dag, 'select_diagnosis')

# connect the dataloader with the 'select_multiple diagnosis' node
# this insures that the dataloader elements show up on top of the form and not at the bottom
id_dataloader = df_raw.loc[df_raw['value']=='Load Data', 'id'].iloc[0] # get ID of the dataloader
dag.add_edge(id_dataloader, 'select_diagnosis') # connect dataloader to select_diagnosis

# add a 'data_load' multiple choice that points to the calculates of the dataloader
# this will allow to set them on startup
n = 'data_load'
n_attrib={'name':'data_load', 'type':'select_multiple', 'content':'Select previous data', 'group' : 1}
dataloader_calculates = [i for (i,j) in dag.in_edges(id_dataloader) if dag.nodes[i]['type']=='calculate']

dag = gt.add_calculate_selector(dag, n, n_attrib, dataloader_calculates)
# add the content from the calculates as content to their predecessor select_options
dag = gt.add_text_calculate_options(dag, 'data_load')
'''
#%% Making duplicate calculates unique and adding a 'calculate sink'
dag = gt.number_calculate_duplicates(dag, df_raw)

#%% Write 'expression' into NON rhombus edges

logic = {} # {edge-tuple : sympy symbol for the logical expression, the negation ~ is not part of the symbolic expression}
logicmap = {} # {sympy symbol of a logical expression: logical expression itself}
negated_logicmap = {} #map between negated sympy symbols and negated odk expressions (needed for converting sympy boolean expressions into odk-conform expressions)
# on edges starting in nodes without any decision to be taken, just write S.true
# apply this also to select_one and select_multiple because the logic is on the edges starting from 
# the 'select_option'
types = ['note', 'decimal', 'integer', 'text', 'container_page', 'container_hint_media', \
         'goto', 'hint-message', 'help-message', 'select_one', 'select_multiple', '']
logic = el.edge_assign_true(dag, logic, types)

# on edges of calculate and diagnosis assign the souce_name. 
# it subsitutes the expression but the source name. 
# this happens because calculates are not contracted -> conceptual document for more information
types = ['calculate', 'diagnosis']
logic, logicmap, negated_logicmap = el.edge_assign_sourcename(dag, logic, logicmap, negated_logicmap, types)

# edges which have a source with type 'select_one yesno' get the tuple (name, value); 
# value can be 'Yes' or 'No'
logic, logicmap, negated_logicmap = el.edge_add_name_to_logic(dag, logic, logicmap, negated_logicmap, ['select_one yesno'])

# edges starting from 'select_option' write the tuple of names of the predecessor and the select_option
# this will result in (select_xxx_name,select_option_name) 
# (just like for select_one yesno, but for select_one, select_multiple, the select_option is not written on the edge)
logic, logicmap, negated_logicmap = el.edge_select_options(dag, logic, logicmap, negated_logicmap, ['select_option'])

# update edge logic
nx.set_edge_attributes(dag, logic, name = 'logic')

#%% Write expression into rhombus edges

# types a rhombus can potentially refer to
refer_types = ['select_one', 'select_one yesno', 'select_multiple', 'calculate', 'diagnosis', 'count', 'integer', 'decimal']

# build expression for rhombus referring to nodes of type calculate, diagnosis
refers_to = ['calculate', 'diagnosis']
for value in ['Yes', 'No']:
    dag = el.assign_refername_to_edges(dag, refer_types, refers_to, value)

# build expression for rhombus referring to nodes of type select_one and select_multiple
refers_to = ['select_one', 'select_multiple']
for value in ['Yes', 'No']:
    dag = el.assign_refername_and_content_to_edges(dag, refer_types, refers_to, value)

# build expression for rhombus referring to nodes of type select_one yesno
refers_to = ['select_one yesno']
for value in ['Yes', 'No']:
    dag = el.assign_refername_and_edgevalue_to_edges(dag, refer_types, refers_to, value)
    
# build expression for rhombus referring to nodes of types integer and decimal
refers_to = ['integer', 'decimal']
for value in ['Yes', 'No']:
    dag, logicmap, negated_logicmap = el.assign_refername_and_content_equation(dag, logicmap, negated_logicmap, refer_types, refers_to, value)
    
#%% Build relevance for all nodes and assign as attribute
dag = gt.write_node_relevance(dag) # make and write relevance to nodes (full root relevance)


# flatten relevance by combining it with 'contracted' relevances in each node
#[gt.make_node_relevance(dag, n) for n in dag.nodes if 'contraction' in dag.nodes[n]]

#%% Reset group relevance in group children
# set group relevance to true for all nodes inside that group (example caretaker advice in Ped TT)

# get ids of all groups
group_ids = [n for n in dag.nodes if dag.nodes[n]['type']=='container_page']

# get ids of all nodes that are in groups 
nodes_in_groups = [n for n in dag.nodes if dag.nodes[n]['group'] in group_ids]

# substitute in relevance the group relevance by S.true
[gt.substitute_group_relevance(n, dag) for n in nodes_in_groups]


#%% CDSS adapted topological sort
# this approach is good, but not for Treatment
# topo_order = gt.topo_sort_cdss_attrib(dag, 'distance_from_root') # the complete sorting of the graph

#%% Get a CDSS topological sort for each disease. 
# as described in the concept doc, we need to use the stackoverflow approach to sorting, 
# in first step we build a list of lists, but in a dictionary type
# here we get the topological sort for each diagnosis
diagnosis_id_hierarchy = gt.get_diagnosis_sorting_id(df_raw, p.diagnosis_order) # make diagnosis id hierarchy list
opt_prio = gt.hierarchy_select_options(df_raw) # hierarchy of select_options in the form

# list of lists with proper sorting for each diagnosis, each node is written in the tuple (n, name, type)
d = gt.make_sorted_nodes_list(dag, diagnosis_id_hierarchy, opt_prio)

d_name_type = gt.map_node_to_name_type(d, dag)

# make a graph with root nodes being the diagnosis and have as successors the line of topologically sorted nodes ("linear DAG")
linear_graph = gt.make_linear_diagnosis_graph(d)  # graph is built based on node_id only

counter = [str(i) for i in list(range(len(d)+1))]  
counter.sort() # lexicographically sorted list for the lexicographical topological sort

## WRONG, Y OU NEED TO BUILD THE GRAPH BASED ON NAME-TYPE COMBO, IT MIGHT LEAD TO CYCLES WHICH YOU HAVE TO RESOLVE FIRST!


def sort_function(item):
    # item is node_id only; based on that we lookup the (name,type) in the dag amd check if it is in d_name_type
    item_name_type = (dag.nodes[item]['name'], dag.nodes[item]['type']) 
    for i in range(len(diagnosis_id_hierarchy)):       
        if item_name_type in d_name_type[i]:
            return counter[i]
            break
    else:
        print('Error, node', item, 'not found for any diagnosis')
        

# topo order with duplicates, they will be deleted during node contraction
topo_order = list(nx.lexicographical_topological_sort(linear_graph, sort_function))

#%% Contract duplicates in topo order
# get all nodes that need to be deleted
# delete those nodes from the real dag, but first combine the relevant

# types where duplicates we look for repeating duplicates. If there are successive nodes with duplicate (name-topo) combos, we 
# keep the first one only
types = ['note', 'select_one', 'select_one yesno', 'select_multiple', 'integer', 'decimal', 'select_option', 'page']
topo_order_stripped = [n for n in topo_order if dag.nodes[n]['type'] in types]

topo_order_stripped_contracted = [topo_order_stripped[0]]

for i in range(1, len(topo_order_stripped)):
    i_data = (dag.nodes[topo_order_stripped[i-1]]['name'], dag.nodes[topo_order_stripped[i-1]]['type'])
    i1_data = (dag.nodes[topo_order_stripped[i]]['name'], dag.nodes[topo_order_stripped[i]]['type'])
    if i1_data != i_data:
        topo_order_stripped_contracted.append(i1_data)
        
        
    


#%% Handle duplicate names
''' Not contracted nodes still have duplicate names, that needs to be dealt with. This solution is not
working for select_xxx because it renames those but not the relevance expressions. Fix needed'''

# types of nodes where a duplicate name is a problem
types =  ['decimal', 'integer', 'note', 'select_one yesno', 'select_one', 'select_multiple', 'container-page']
dag = gt.rename_duplicates(dag, types)


#%% Replace sympy expressions with ODK-expressions
''' The relevance logic expressions are generic Sympy expressions. As we will be using Enketo based solutions, 
we must convert them into odk conform expressions. The maping between sympy expressions and odk is given in the 
dictionaries negated_logicmap and logicmap'''
        
for n in dag.nodes:
    dag.nodes[n]['relevance'] = el.parse_sympy_logic(dag.nodes[n]['relevance'], negated_logicmap, logicmap)

#%% Build choices tab from dag
#list_name = {n:dag.nodes[list(dag.predecessors(n))[0]]['name'] for n in dag.nodes if dag.nodes[n]['type']=='select_option'}
#df_listname = pd.DataFrame.from_dict(list_name, orient='index')
#d = {n:dag.nodes[n] for n in dag.nodes if dag.nodes[n]['type']=='select_option'}
#df_choices = pd.DataFrame.from_dict(d, orient='index')

#%% Replace note headings with content from html files
# first, insure that all html files are encoded in UTF-8
if p.form_id == 'almsom':
    for n in dag.nodes:
        if dag.nodes[n]['type'] in ['note', 'select_one', 'select_one yesno', 'select_multiple']:
            utf8(p.htmlfolder + dag.nodes[n]['content'] + '.htm')
            
if p.form_id == 'almsom':
    content = {n:ch.cleanhtml_fromfile(p.htmlfolder + dag.nodes[n]['content'] + '.htm')  for n in dag.nodes if dag.nodes[n]['type'] in ['note', 'select_one', 'select_one yesno', 'select_multiple']}
    nx.set_node_attributes(dag, content, 'content')


#%% Convert html strings to markdown for inferiour platforms
# exclude nodes which have no content (None)
if p.platform == 'commcare':
    content = {n:md(dag.nodes[n]['content'], escape_underscores=False)  for n in dag.nodes if dag.nodes[n]['type'] in ['note', 'select_one', 'select_one yesno', 'select_multiple'] and dag.nodes[n]['content'] is not None}
    content.update({n:dag.nodes[n]['name']  for n in dag.nodes if dag.nodes[n]['type'] in ['note', 'select_one', 'select_one yesno', 'select_multiple'] and dag.nodes[n]['content'] is None})
    nx.set_node_attributes(dag, content, 'content')
    # next step so that for missing files, there is the filename at least
    

#%% Move from graph to dataframe
df = oh.dag_to_df(dag)

df = df.reindex(topo_order) # sort the dataframe according to the CDSS topo sorting

# types to be kept in df
types = ['decimal', 'integer', 'diagnosis', 'select_multiple', 'select_one', 'calculate', \
        'note', 'select_one yesno', 'container_page']
df.drop(df.loc[~df['type'].isin(types)].index, inplace=True)

#%% Group page-elements
'''The sorting is ignoring pages, therefore we group them independently here.'''
df = oh.group_pages(df)
df.drop(columns=['group'], inplace=True)

#%% Make df conform to odk
df = oh.frame_to_odk(df, p.drugsfile, p.form_id)

#%% Add the header specific for defined platform (such as CHT) 
'''The merge script that would add the dx part, cleans this away'''
df = oh.add_header(df, p.headerfile)
#%% Update relevance expression of caretaker advice messages
d = ca.ca_expressions(df_raw, p.cafile)
df = ca.update_ca_relevance(df, d)

#%% For CHT put help fields in a standard note field, just below the row the help is attached to
# necessary for CHT but not for Commcare because it natively supports help pop up fields
if p.platform == 'cht':
    df = oh.helpfields(df)
#%% Make a settings tab
now = datetime.now()
version=now.strftime('%Y%m%d%H%M')
indx=[[1]]

settings={'form_title':p.form_title,'form_id':p.form_id,'version':version,'default_language':'en','style':'pages'}
df_settings=pd.DataFrame(settings,index=indx)

#%% Add select_diagnosis and data_load to df_choices
'''Currently done by hand, later based on graph. See issue posted on github'''
def diagnosis_to_dfchoices(dag, df_choices, listname):
    d = {n:dag.nodes[n] for n in dag.nodes if (dag.nodes[n]['type']=='select_option') and (dag.nodes[n]['group']==listname)}
    df_select_diagnosis = pd.DataFrame.from_dict(d, orient='index')
    df_select_diagnosis = df_select_diagnosis[['group', 'name', 'content']]
    df_select_diagnosis.rename(columns={'group':'list_name', 'content':'label::en'}, inplace=True)
    df_choices = pd.concat([df_select_diagnosis, df_choices])
    
    return df_choices

# df_choices = diagnosis_to_dfchoices(dag, df_choices, 'select_diagnosis')
# df_choices = diagnosis_to_dfchoices(dag, df_choices, 'data_load')

#%% Make a summary  -> this has moved to the DX jupyter script, because there you get the real relevance for diagnosis

'''The summary is built based on the triggered diagnosis. It is built here and saved to disk. 
It is then re-used by the merge script'''
'''
import summary
df_summary = summary.make_summary(df, df_choices, diagnosis_id_hierarchy, p.summaryfile)

# store df_summary
import pickle

with open(p.folder+'df_summary.pickle', 'wb') as handle:
    pickle.dump(df_summary, handle, protocol=pickle.HIGHEST_PROTOCOL)
'''
#%% Write xls form to file
df2xlsform(df, df_choices, df_settings, p.output_xls)
if p.platform == 'cht':
    df2xlsform(df, df_choices, df_settings, '/home/rafael/cht-local-setup/upgrade/cht-core/config/raf/forms/app/ped.xlsx')

#%% Convert xlsform to xform
if p.platform == 'commcare':
    xls2xform(p.output_xls, p.output_xml)

#%% Make xform compatible to Commcare
if p.platform == 'commcare':
    xt.xform2commcare(p.output_xml, p.output_commcare)


#%% Compile and upload into local CHT instance
if p.platform == 'cht':
    import os
    os.system('cd /home/rafael/cht-local-setup/upgrade/cht-core/config/ecare/ | cht --url=https://medic:password@localhost --accept-self-signed-certs convert-app-forms upload-app-forms -- almsom')

