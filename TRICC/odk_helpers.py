# -*- coding: utf-8 -*-
"""
Created on Thu Sep 15 12:39:42 2022
Function to create a df that contains all the select_options in the propper odk format
@author: kluera
"""

import pandas as pd
import cleanhtml as ch
import loadcalculations as lc

# get edges that originate in images
def make_imageframe(df_raw):
    # make an edge dataframe
    df_edges = make_edgeframe(df_raw)
    
    df_image_edges = df_edges[['source', 'target']] # extract from df_edges only the edges with source being an image
    df_image = df_raw.loc[df_raw['style'].str.contains("image",na=False)] # make an image df
    # merge images-edges with images:
    df_image_edges = df_image_edges.merge(df_image[['id', 'style']], how = 'inner', left_on = 'source', right_on = 'id')
    df_image = df_image_edges[['id', 'target', 'style']] # only keep relevant columns

    # add a column for the future filename and extract image type (png, jpeg,...) into it
    df_image['imagename'] = df_image['style'].str.extract(r'image=data:image/(.+?),')
    df_image['imagename'] = df_image['id'] + '.' + df_image['imagename'] # add filetype extension to imagename
    df_image = df_image[['imagename', 'target', 'style']] # only keep relevant columns
    
    return df_image


def make_edgeframe(df_raw):
    # edges have 'edgeStyle' in their style and do not have emtpy source AND target at the same time:
    m = df_raw['style'].str.contains('edgeStyle') & (~df_raw['source'].isnull() & ~df_raw['target'].isnull())
    df_edges = df_raw.loc[m]
    
    return df_edges


def make_choicesframe(df_raw):
    df = df_raw.loc[df_raw['odk_type']=='select_option']
    df = df[['value', 'parent', 'name', 'y', 'id']]
    # KEEP  odk_type  ONLY IN THE MEANTIME TO MAINTAIN COMPATIBILITY WITH OLD SCRIPT, REMOVE LATER
    df = df.merge(df_raw[['id', 'name', 'odk_type']], how = 'left', left_on = 'parent', right_on = 'id', suffixes = ('_opt', '_parent'))
    df = df[['id_opt', 'name_parent', 'name_opt', 'value', 'odk_type', 'y']]

    # include images
    df_image = make_imageframe(df_raw)
    df = df.merge(df_image[['imagename', 'target']], how = 'left', left_on = 'id_opt', right_on = 'target')
    
    
    # sort the options as in the drawing
    df['y'] = df['y'].astype(int)
    df.sort_values(by = ['name_parent', 'y'], ascending = [True, True], inplace = True)
    # KEEP  id and odk_type  ONLY IN THE MEANTIME TO MAINTAIN COMPATIBILITY WITH OLD SCRIPT, REMOVE LATER
    df = df[['id_opt', 'name_parent', 'name_opt', 'value', 'odk_type', 'imagename']]
    df.fillna('', inplace = True)
    df.columns=['id', 'list_name', 'name', 'label', 'odk_type', 'image']
    
    # add yesno rows
    d = {'id': ['yes', 'no'], 'list_name': ['yesno', 'yesno'], 'name': ['Yes', 'No'], 'label': ['Yes', 'No']}
    df_yesno = pd.DataFrame(d, columns = df.columns)
    df = pd.concat([df, df_yesno])
    df.set_index('id', inplace = True)
    
    return df

def make_choicesframe_jupyter(df_raw):
    df = df_raw.loc[df_raw['odk_type']=='select_option']
    df = df[['value', 'xml-parent', 'name', 'y', 'id']]
    # KEEP  odk_type  ONLY IN THE MEANTIME TO MAINTAIN COMPATIBILITY WITH OLD SCRIPT, REMOVE LATER
    df = df.merge(df_raw[['id', 'name', 'odk_type']], how = 'left', left_on = 'xml-parent', right_on = 'id', suffixes = ('_opt', '_parent'))
    df = df[['id_opt', 'name_parent', 'name_opt', 'value', 'odk_type', 'y']]

    # include images
    df_image = make_imageframe(df_raw)
    df = df.merge(df_image[['imagename', 'target']], how = 'left', left_on = 'id_opt', right_on = 'target')
    
    
    # sort the options as in the drawing
    df['y'] = df['y'].astype(int)
    df.sort_values(by = ['name_parent', 'y'], ascending = [True, True], inplace = True)
    # KEEP  id and odk_type  ONLY IN THE MEANTIME TO MAINTAIN COMPATIBILITY WITH OLD SCRIPT, REMOVE LATER
    df = df[['id_opt', 'name_parent', 'name_opt', 'value', 'odk_type', 'imagename']]
    df.fillna('', inplace = True)
    df.columns=['id', 'list_name', 'name', 'label', 'odk_type', 'image']
    
    # add yesno rows
    d = {'id': ['yes', 'no'], 'list_name': ['yesno', 'yesno'], 'name': ['Yes', 'No'], 'label': ['Yes', 'No']}
    df_yesno = pd.DataFrame(d, columns = df.columns)
    df = pd.concat([df, df_yesno])
    df.set_index('id', inplace = True)
    
    return df

def add_calculate_to_choices(dag, n, list_name,  df_choices):
    '''To add elements to df_choices dataframe
    :param dag The graph
    :param n A list of tuples (id, name, text) that shall be added to df_choices
    :param df_choices Current choices tab in dataframe format    
    '''
    n_choices = [{'id':n[0], 'name':n[1], 'label::en':n[2]} for n in n]
    dfa = pd.DataFrame(n_choices)
    dfa.set_index('id', inplace=True)
    dfa['list_name']=list_name
    dfa['odk_type']='select_multiple'
    df_choices = pd.concat([df_choices, dfa])
    return df_choices

def assign_diagnosisname(diagnose_order_file, df):
    '''This function readas the diagnose order csv file and assigns the 'name' to 
    the diagnosis calculates, based on a match with the content of that object.'''
    # properly name the diagnose calculates in the TT drawing
    diagnose_hierarchy = pd.read_csv(diagnose_order_file)
    
    diagnose_hierarchy['map']= diagnose_hierarchy['Name'].apply(ch.clean_name) 
    df['map'] = df['value'].astype(str)
    df['map'] = df['map'].apply(ch.clean_name)
    
    m = df['map'].isin(diagnose_hierarchy['map']) & (df['odk_type'].isin(['calculate', 'diagnosis']))
    dfa = df.loc[m].reset_index()
    dfa = dfa[['index','map']].merge(diagnose_hierarchy[['id','map']],how='left',on='map')
    dfa.set_index('index',inplace=True)
    dfa.rename(columns={'id':'name'},inplace=True)
    df.update(dfa)
    
    df.drop(columns=['map'],inplace=True)
    
    return df


def dag_to_df(dag):
    d = {n:dag.nodes[n] for n in dag.nodes}
    df = pd.DataFrame.from_dict(d, orient='index')    
    # rename columns
    d_rename = {'help-message':'help::en', 'hint-message':'hint::en', 'content':'label::en'}
    df.rename(columns=d_rename, inplace=True)
    drop_cols = df.filter(['distance_from_root', 'contraction']) # check if columns that need to be dropped actually exist
    df.drop(drop_cols, inplace=True, axis=1)    

    return df


def group_pages(df):
    pageids = df.loc[df['type']=='container_page'].index
    df.reset_index(drop=False, inplace=True)
    df['new_index']=pd.to_numeric(df.index)
    df = df.merge(df[['index','new_index']], how='left', left_on='group', right_on='index', suffixes = ('', '_p'))
    df.loc[df['new_index_p'].notna(), 'new_index'] = df['new_index_p']
    df.drop(columns=['index_p','new_index_p'], inplace=True)
    
    g = df.groupby('group') # group by pages
    for name, frame in g:  # for each page
        k=0.001
        for i in frame.index: # for each element in that page
            if df.loc[i,'group'] in pageids: # if we are in a real page and not in root
                df.loc[i,'new_index'] = df.loc[i,'new_index']+k # add to the new index a small step
                k+=0.001
                
    df.set_index('new_index', drop=True, inplace = True)
    df.sort_index(inplace=True)
    df.set_index('index', drop=True, inplace=True)
    
    # add 'end group' rows
    # get the last objects of each page
    df.reset_index(drop=False, inplace=True)
    # index of the end group rows after the df index has been reset: index of 'begin_group'+_end
    indexname_endgrouprows = df.loc[~df.duplicated(subset='group', keep='last') & df['group'].isin(pageids), 'group']
    indexname_endgrouprows = indexname_endgrouprows + '_end'
    indexname_endgrouprows.index = indexname_endgrouprows.index+0.1
    indexname_endgrouprows.rename('index', inplace=True)
    df_endgroup = pd.DataFrame(indexname_endgrouprows)
    df_endgroup['type']='end group'
    
    df = pd.concat([df_endgroup, df])
    df.sort_index(inplace=True)
    df.set_index('index', drop=True, inplace=True)
    
    return df

def frame_to_odk(df, drugsfile, form_id):
    '''Adapt the survey dataframe so that it fits to ODK requirements. This is necessary for
    ODK/Enketo based solutions, such as CHT, Commcare, ODK Collect'''
    newcols = ['repeat_count', 'appearance', 'required', 'required message::en', 'calculation', \
               'constraint', 'constraint message::en', 'image::en']
    df[newcols]=''

    # short term workaround for select_xxx + NAME to add the same name as list_name
    m = df['type'].isin(['select_one','select_multiple'])
    df.loc[m,'type'] = df.loc[m,'type'] + ' ' + df.loc[m,'name']

    # rename begin group
    df.replace({'container_page':'begin group'}, inplace=True)
    # add 'field-list'
    df.loc[df['type']=='begin group','appearance']='field-list'
    
    # rename 'diagnosis' into 'calculate' as this is not a odk type
    df.loc[df['type']=='diagnosis', 'type']='calculate'

    # in 'calculate' fields move 'relevance' to calculate
    df.loc[df['type']=='calculate','calculation'] = df.loc[df['type']=='calculate','relevance']
    # add 'number() to fit with odk '
    df.loc[df['type']=='calculate','calculation'] = 'number(' + df.loc[df['type']=='calculate','calculation'] + ')'
    # delete entry in relevance column of 'calcuate' rows
    df.loc[df['type']=='calculate','relevance'] = ''

    # populate constraint message to all select_multiple
    df.loc[df['type'].str.contains('select_multiple',na=False),'constraint']='.=\'opt_none\' or not(selected(.,\'opt_none\'))'
    df.loc[df['type'].str.contains('select_multiple',na=False),'constraint message::en']='**None** cannot be selected together with symptoms.'

    # include external xlsx file with complex calculates such as drug dosages
    df = lc.loadcalc(df, drugsfile, form_id)

    # Countdown timer
    df.loc[df['label::en'].str.contains('START',na=False),'appearance']='countdown-timer'
    
    # populate required condition
    df.loc[~df['type'].isin(['note','calculate', 'diagnosis', 'begin group', 'end group', 'text', 'acknowledge', 'decimal', 'integer']) & (df['required']==''),'required']='true()'
    # but not to contextual parameters
    df.loc[df['name']=='data_load','required']=''
    
    # where relevance = True, delete
    df.loc[df['relevance']=='True', 'relevance']=''
    
    return df


def concat_str(help_id):
    '''Hardcoded strings for help message click-on'''
    
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
    if 'help::en' in df.columns:        
        I = df.loc[df['help::en']!=''].index
    
        for i in I:
            help_id = df.loc[i,'name']
            str_ackn = concat_str(help_id)
            
            begingroup = pd.DataFrame({'index':df.loc[i]['index']+'_begingroup',\
                                       'type': 'begin group', \
                                       'name':'g_' + df.loc[i]['name'] + '_help', \
                                       'label::en':'NO_LABEL', \
                                       'appearance':'field-list', \
                                       'relevance':df.loc[i]['relevance']}, index=[i-0.1])
            acknowledge = pd.DataFrame({'index':df.loc[i]['index']+'_bool',\
                                        'type': 'acknowledge', \
                                        'name':'bool_' + df.loc[i]['name'], \
                                        'label::en':str_ackn}, index=[i+0.1])
            endgroup = pd.DataFrame({'index':df.loc[i]['index']+'_endgroup', 'type':'end group'}, index=[i+0.3])
            helpmessage = pd.DataFrame({'index':df.loc[i]['index']+'_help','type': 'note', \
                                        'name':'help_' + df.loc[i]['name'], \
                                        'label::en': df.loc[i]['help::en'],\
                                        'relevance':'${bool_' + df.loc[i]['name'] + '}=\'OK\''}, index=[i+0.2])
            df.loc[i,'help::en']='' # delete the help message inside the labels itself
            df.loc[i,'relevance']='' # delete the relevance (it is now in the group)
            
            df = pd.concat([df, begingroup, acknowledge, helpmessage, endgroup])
    
        # colorize the help message and the acknowledge
        #m = df['name'].str.contains('help_',na=False)
        #color_p = '<p style="background-color:LightGray;color:MediumSeaGreen;font-size:80%;">'
        #df.loc[m,'label::en'] = color_p + df.loc[m,'label::en'] + '</p>'
        
        # sort rows
        df = df.sort_index()
    else:
        print('No help fields found in the diagram. ')
    
    df.set_index('index',inplace=True, drop=True)
    
    return df

def add_header(df, headerfile):
    '''This function adds a header to the survey dataframe. The header contains platform specific rows, 
    for instance, for CHT you have there the dataloader from facility, loading user, etc. 
    It could also be used to insert specific functionalities like the MSFeCARE password checker.
    @df: the survey dataframe
    @headerfile: the full path to the xlsx file container the header'''
    df_header = pd.read_excel(headerfile)
    df_header.set_index(df_header['type']+ '_' + df_header['name'], inplace=True)
    # there might be duplicates in the header, especially in CHT, so we enumerate them
    #index_duplicates = df_header.index[df_header.index.duplicated(keep=False)].unique()
    df_header.reset_index(inplace=True)
    df_header.loc[df_header.duplicated(subset=['index'],keep=False),'index']=df_header['index']+'_'+df_header.index.astype('str')
    #for i in index_duplicates:
    #    newindex = list(enumerate(df_header.loc[df_header['index']==i, 'index']))
    #    newindex = [n[1] + '_' + str(n[0]) for n in newindex]
    #    df_header.loc[df_header['index'].str.contains(i), 'index'] = newindex
    
    df_header.set_index('index', drop=True, inplace = True)
    
    df = pd.concat([df_header, df])
    return df