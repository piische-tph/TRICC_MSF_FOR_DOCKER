# OLD LEGACY JUPYTER NOTEBOOK for Ped DX

# In[1]:

import pandas as pd
import networkx as nx
import re
import os
import base64 # to extract images from base64 strings (as they are stored in xml files)
from datetime import datetime
import html2text
import cleanhtml as ch #my own helper functions
from loadcalculations import loadcalc
import odk_helpers as oh
from combinecalculates import calcombo
from treetodataframe import treetodataframe
import graphtools as gt
import qualitychecks_pd as qcpd
import inputs


#%% Parameters
import params_ped as p # for msfecare Ped
# import params_libya_rk as p

import warnings
warnings.filterwarnings("ignore")


#%% Parse diagram
objects = inputs.parse_drawio(p.inputfile_dx) # parse drawing

# Put diagram elements in df_raw
df_raw = inputs.treetodataframe(objects) # import drawing elements into a df
df_raw.fillna('', inplace = True) 
df_raw.loc[df_raw['label']!='','value'] = df_raw['label'] # all content into the same column



df_raw = treetodataframe(objects)

# maintain compatibility with old script:
df_raw.fillna('', inplace = True)
df_raw['tag']=''
df_raw.loc[df_raw['label']!='','value'] = df_raw['label']
df_raw['label_userObject']=''
df_raw['xml-parent']=df_raw['parent']

df_raw = df_raw[['tag', 'id', 'value', 'label_userObject', 'style', 'xml-parent', 'edge',
       'source', 'target', 'name', 'odk_type', 'min', 'max', 'required',
       'constraint_message', 'x', 'y']]




#%% Quality checks
# do not work with 'xml-parent', only with 'parent'

#qcpd.check_node_type(df_raw) # check if all objects have an odk_type
#qcpd.check_rhombus_refer(df_raw) # check if all rhombus refer to an existing node
#qcpd.check_edge_connection(df_raw) # check if all edges are well connected
#types = ['rhombus', 'select_one yesno']
#qcpd.check_edge_yesno(df_raw, types) # check if all edges leaving rhombus and select_one yesno have Yes/No



#%% Identify break points for the PAUSE function (colored green)
df_pause = df_raw.loc[df_raw['style'].str.contains('fillColor=#cdeb8b', na=False),['id', 'name', 'odk_type']]
df_pause['flowtype'] = 'diagnostic'
df_pause.to_csv(p.breakpoints)


#%% make a constraint column
df=df_raw.copy()
df.drop(columns=['x','y'],inplace=True)
df['constraint']=''
df.loc[df['min']!='','constraint']='.>=' + df['min']
df.loc[df['max']!='','constraint']=df['constraint'] + ' and .<=' + df['max']
df.drop(columns=['min','max'],inplace=True)


#%% Required fields
# if integers and decimals are not REQUIRED, the expression towards the downstream fields must be removed. See below under **Expression for each row**
df.loc[df['required']=='yes','required']='true()'


#%% Improve html and formatting


# that solution is actually working best. From the answer of 'FrBrGeorge'
# https://stackoverflow.com/questions/14694482/converting-html-to-text-with-python

from html.parser import HTMLParser

class HTMLFilter(HTMLParser):
    text = ""
    def handle_data(self, data):
        self.text += data

def html2plain(data): 
    f = HTMLFilter()
    f.feed(data)
    return f.text

# the soup.text strips off the html formatting also
def remove_html(string):
    text = html2text.html2text(string) # retrieve pure text from html
    text = text.strip('\n') # get rid of empty lines at the end (and beginning)
    text = text.split('\n') # split string into a list at new lines
    text = '\n'.join([i.strip(' ') for i in text if i]) # in each element in that list strip empty space (at the end of line) 
    text = text.replace('\n',' ')
    # and delete empty lines
    return text

def remove_html_value(string):
    text = string.strip('\n') # get rid of empty lines at the end (and beginning)
    text = text.split('\n') # split string into a list at new lines
    text = '\n'.join([i.strip(' ') for i in text if i]) # in each element in that list strip empty space (at the end of line) 
    # and delete empty lines
    return text

# remove html formatting and keep text inside rhombus
m = df['odk_type']=='rhombus'
df.loc[m,'value'] = df.loc[m,'value'].apply(lambda x: remove_html(x) if x!=None else None)
#df.loc[m,'value'] = df.loc[m,'value'].replace('\n',' ',regex=True)

# remove html formatting in questions and select_options (not allowed here)
# df.loc[df['odk_type'].str.contains('select_',na=False),'value'] = df.loc[df['odk_type'].str.contains('select_',na=False),'value'].apply(lambda x: remove_html(x) if x!=None else None)
# df.loc[df['odk_type']=='hint-message','value'] = df.loc[df['odk_type']=='hint-message','value'].apply(lambda x: remove_html(x) if 
m = ~df['odk_type'].isin(['note','help-message'])
df.loc[m,'value'] = df.loc[m,'value'].apply(lambda x: html2plain(x) if x!=None else None)

#%% Duplicates


# add id to name of objects with duplicate names, except for calculate, diagnosis, select_option, rhombus, shortcuts, container-hint-media and edges
df.loc[df.duplicated(subset=['name'],keep='first') & ~df['odk_type'].isin(['calculate', 'diagnosis', 'select_option', 'rhombus', 'goto', 'container_hint_media', 'help-message', 'hint-message']) & (df['edge']!='1'), 'name'] = df['name']+df['id']

df.set_index('id',inplace=True)



# replace NaN with empty strings
df.value.fillna('',inplace=True)



#%% Edges df_arrows


# make a dataframe with connectors only
#df_arrows=df_raw.loc[(df_raw['source']!='') & (df_raw['target']!=''),['source','target','value']]
df_arrows=df.loc[(df['source']!='') & (df['target']!=''),['source','target','value']]
#df_arrows=df.loc[df.source.notna() & df.target.notna(),['source','target','value']]

# remove html from the text on the arrows
df_arrows.loc[:,'value'] = df_arrows.loc[:,'value'].apply(lambda x: remove_html(x) if x!=None else None)

# drop arrows from df
df.drop(df_arrows.index,inplace=True)


#%% Shortcuts 

dfa = df_raw.loc[df_raw['odk_type']=='goto'].copy() # extract shortcut elements and put in a new dataframe
dfa.loc[dfa['odk_type']=='goto','name'] = dfa.loc[dfa['odk_type']=='goto','name'].str[9:] # remove prefix
# merge with raw-data to get the id of the exit element
dfa = dfa.reset_index().merge(df_raw.reset_index()[['id','name']],how = 'left', on='name') 
exitmap = dict(zip(dfa['id_x'],dfa['id_y'])) # convert into a dictionnary 
df_arrows['target'] = df_arrows['target'].replace(exitmap) # replace the shortcut elements by the exit-element in df_arrows
df.drop(df.loc[df['odk_type']=='goto'].index,inplace=True) # drop shortcuts from df_survey


#%% Make media folder

os.makedirs(p.media_folder, exist_ok=True)  # recursively create mediafolder, do nothing if it exists


#%% Extract images png


# finding png images that belong to container-hint-media (not included are those that belong to select_options)
df.loc[df['style'].str.contains("image/png",na=False),'odk_type']='png-image'+df.name+'.png'

# getting a dataframe with png-images only (better for joining with df later)
# images:rows where 'xml-parent' is inside the index of rows that have the entry 'container_hint_media' in odk_type column, 
# of those rows we extract those where the 'type' column contains the substring 'png-image'
# and of the result we just take the columns 'xml-parent', 'odk_type' and 'style'
# 'xml-parent' is the container it belongs to and the line that will contain the info about the image
# 'odk_type' contains also the file name .png
# 'style' contains the actual image data

df_png=df.loc[df['xml-parent'].isin(df.loc[df['odk_type']=='container_hint_media'].index) 
              & df['odk_type'].str.contains('png-image',na=False),
              ['xml-parent','odk_type','style']] # images that are in 'containers_hint_media'

# getting image data from 'style' column for all images (from containers AND select_options) and storing it to disk
df_pngAll=df.loc[df['odk_type'].str.contains('png-image',na=False),['xml-parent','odk_type','style']]
for index, row in df_pngAll.iterrows():
    string = row['style'] 
    img_data=re.search('image/png,(.+?);',string).group(1) # extract image data from 'style' column using regex
    with open(p.media_folder+row['odk_type'], "wb") as fh:
        fh.write(base64.decodebytes(img_data.encode('ascii'))) # encode image into ascii (binary) and save

df_png.rename({'xml-parent':'container_id','odk_type':'image::en'},axis=1,inplace=True)
index_delete=df_png.index
df_png.set_index('container_id',inplace=True)
df_png.drop('style',axis=1,inplace=True)

# joinging df and df_png (this adds the media-image column to df)
df=df.join(df_png)

# remove the rows with those 'png messages' in df as they are no longer needed
df.drop(index_delete,inplace=True)

# df.loc[df['image::en'].notna()].head()


#%% Extract images jpg


# finding jpeg images that belong to container-hint-media (not included are those that belong to select_options)
df.loc[df['style'].str.contains("image/jpeg",na=False),'odk_type']='jpeg-image'+df.name+'.jpeg'

# getting a dataframe with png-images only (better for joining with df later)
# images:rows where 'xml-parent' is inside the index of rows that have the entry 'container_hint_media' in odk_type column, 
# of those rows we extract those where the 'type' column contains the substring 'png-image'
# and of the result we just take the columns 'xml-parent', 'odk_type' and 'style'
# 'xml-parent' is the container it belongs to and the line that will contain the info about the image
# 'odk_type' contains also the file name .png
# 'style' contains the actual image data

df_png=df.loc[df['xml-parent'].isin(df.loc[df['odk_type']=='container_hint_media'].index) 
              & df['odk_type'].str.contains('jpeg-image',na=False),
              ['xml-parent','odk_type','style']] # images that are in 'containers_hint_media'

# getting image data from 'style' column for all images (from containers AND select_options) and storing it to disk
df_pngAll=df.loc[df['odk_type'].str.contains('jpeg-image',na=False),['xml-parent','odk_type','style']]
for index, row in df_pngAll.iterrows():
    string = row['style'] 
    img_data=re.search('image/jpeg,(.+?);',string).group(1) # extract image data from 'style' column using regex
    with open(p.media_folder+row['odk_type'], "wb") as fh:
        fh.write(base64.decodebytes(img_data.encode('ascii'))) # encode image into ascii (binary) and save

df_png.rename({'xml-parent':'container_id','odk_type':'image::en'},axis=1,inplace=True)
index_delete=df_png.index
df_png.set_index('container_id',inplace=True)
df_png.drop('style',axis=1,inplace=True)

# joinging df and df_png (this adds the media-image column to df)
#df=df.join(df_png)
df.update(df_png)

# remove the rows with those 'png messages' in df as they are no longer needed
df.drop(index_delete,inplace=True)


#%% Create and populate 'help' & 'hint' columns

for s in ['hint-message', 'help-message']:

    dfa=df_raw.loc[df_raw['odk_type']==s,['xml-parent','value']] # dataframe with help-fields / hint-fields only
    drop_index = df_raw.loc[df_raw['odk_type']==s, 'id']
    dfa.set_index('xml-parent', inplace = True) # in order to join dfa and df on index
    sa = s[:-8]+'::en'
    dfa.rename(columns = {'value':sa}, inplace = True) 
    df=df.join(dfa) # this adds the help message column to df
    df.drop(drop_index, inplace = True) # remove 'help' rows from df (that data is now in the 'help' column)
    
df.fillna('', inplace = True)


#%% DF that will be needed to replace sources in df_arrows inside containers, by the container itself

df_new_arrow_sources = df.loc[df['xml-parent'].isin(df.loc[df.odk_type=='container_hint_media'].index) 
                              | df['xml-parent'].isin(df.loc[df.odk_type=='container_page'].index),['xml-parent','odk_type']]
df_new_arrow_sources.rename({'xml-parent':'container_id','odk_type':'odk_type_of_content'},axis=1,inplace=True)

# add also the type of the container (page or hint-image)
df_new_arrow_sources = df_new_arrow_sources.merge(df[['odk_type']],how='left',left_on='container_id',right_index=True)


#%% replace 'container_hint_media' labels with those of their children & drop children from df

container_ids = df_raw[df_raw['odk_type']=='container_hint_media']['id']
m = df_raw['xml-parent'].isin(container_ids) & ~df_raw['style'].str.contains('image',na=False) & ~df_raw['odk_type'].isin(['hint-message', 'help-message'])
label_ids = list(df_raw[m]['id']) # used for dropping the labels from df after uploading info to container rows
df_label = df_raw.loc[m, ['xml-parent','value','odk_type','name', 'id']] # all the label-children of containers 
df_label.set_index('xml-parent', inplace=True)
# ATTENTION! df_raw still has duplicate names -> duplicates in df_label['name'], so fix it now:
df_label.loc[df_label.duplicated(subset = ['name']), 'name'] = df_label['name'] + df_label['id']
df.update(df_label) # update the containers' 'value', 'odk_type' and 'name'

df.drop(label_ids, inplace = True) # drop the children from df

#%% Connectors inside container-hint-media

# for connectors where the source is inside a container-hint-media, replace the source with the container itself
df_hint_media_objects = df_new_arrow_sources.loc[df_new_arrow_sources['odk_type']=='container_hint_media']
df_arrows = df_arrows.merge(df_hint_media_objects,how='left',left_on='source',right_index=True)
df_arrows.rename(columns={'odk_type':'container_type'},inplace=True)
m=(df_arrows['container_type']=='container_hint_media')
df_arrows.loc[m,'source']=df_arrows.loc[m,'container_id'] # replace the source by the container-hint-media itself
df_arrows.loc[m,'source_type']=df_arrows.loc[m,'odk_type_of_content']
df_arrows.drop(columns=['container_id','odk_type_of_content','container_type'],inplace=True)
df_arrows.fillna('',inplace=True)


#%% Make df_choices

# first you have to make yet another df_raw, just because in the original df_raw, the names are not yet dealth with duplicate
# thing. 
df_raw2 = df_raw.copy()
df_raw2.loc[df_raw2.duplicated(subset=['name'],keep='first') & ~df_raw2['name'].str.contains('opt_',na=False) & ~df_raw2['name'].str.contains('stored_',na=False)        & ~df_raw2['name'].str.contains('shortcut_',na=False), 'name']=df_raw2['name']+df_raw2['id']


# make df_choices
# takes into account the right order of options in the drawing, based on 'y' value. 
# the py files written in spyder maintain compatibility to this script, notable the output has the 'id' of  the option and
# the 'odk_type' --> as you move away from jupyter, modify the python functions, so that these are no longer included

df_choices = oh.make_choicesframe_jupyter(df_raw2)
df_choices.rename(columns = {'label': 'label::en', 'image': 'image::en'}, inplace = True)


#%% to maintain compatibility with legacy image extractor

# currently the images have prefix 'png' or 'jpeg'. This will be deprecated, and the new df_choices does not add it
# I add it here manually to maintain compatibility
df_choices.loc[df_choices['image::en'].str.contains('.png', na=False),'image::en']='png-image' + df_choices['image::en']
df_choices.loc[df_choices['image::en'].str.contains('.jpeg', na=False),'image::en']='jpeg-image' + df_choices['image::en']


#%% Remove the rows with 'choices' in df as they are no longer needed 
df.drop(df_choices.iloc[:-2].index,inplace=True)
# drop the remaining unspecified objects (pure xml formating related elements or drawing artefacts) 
df.drop(df.loc[df.value==''].index,inplace=True)


#%% preparing df_arrows for logic part:

# rename index of df_arrows to reduce confusion
df_arrows.index.rename('Arrow ID',inplace=True)

# make a logical expression for each arrow

# add names of the source from df (for the case when the source is NOT a select_xxx) (names are the odk id's)
# the value is only needed for the rhombus

'''
First we merge with df and then again with df_choices. The reason for that: at this stage, 
the arrows originate from select_xxx options (opt1,opt2,...), but do not point to them. 
However, at a later stage, those arrows are modified so they originate from the select_xxx itself. If that step was done 
before, we would not need to have to merge twice here. When improving the form builder, consider changing this. 
'''
# merging with df to get the odk_type
df_arrows=df_arrows.merge(df[['name','odk_type']],how='left',left_on='source',right_index=True)
# moving the type of the source into the column 'source_type'
df_arrows.loc[df_arrows['source_type']=='','source_type']=df_arrows.loc[df_arrows['source_type']=='','odk_type']
# droping the 'odk_type' column, it is no longer needed
df_arrows.drop(columns=['odk_type'],inplace=True)
df_arrows.fillna('',inplace=True)

# merging with df_choices to get the odk_type for when the source is a select_xxx
df_arrows=df_arrows.merge(df_choices[['list_name','name','odk_type']],how='left',left_on='source',right_index=True)
# as before for df, moving the type of the source into the column 'source_type'
df_arrows.loc[df_arrows['source_type']=='','source_type']=df_arrows.loc[df_arrows['source_type']=='','odk_type']
df_arrows.fillna('',inplace=True)

# merge names from df and df_choices into one column
df_arrows['source_name']=df_arrows['name_x']+df_arrows['list_name']
df_arrows.drop(['name_x','list_name','odk_type'],axis=1,inplace=True)
df_arrows.rename(columns={'name_y':'select_option'},inplace=True)


#%% Expression for each row

df_arrows['expression']=''

# add connectors to virtual objects (loaded objects)

# expression for yes no questions
df_arrows.loc[df_arrows['source_type']=='select_one yesno','expression'] = '${'+df_arrows['source_name'] + '}=' + '\'' + df_arrows.value + '\''

# expression for integers and decimals
#df_arrows.loc[(df_arrows['source_type']=='integer') | (df_arrows['source_type']=='decimal'),'expression'] = '${'+df_arrows['source_name'] + '}!=' + '\'\''
# for integers and decimals that are NOT required, the expression must be removed:
#m1 = df_arrows['source_type'].isin(['integer', 'decimal'])
#m2 = df_raw['odk_type'].isin(['integer', 'decimal'])
#df_arrow_int = df_arrows.loc[m1].reset_index().merge(df_raw.loc[m2, ['name', 'required']], how = 'left', left_on = 'source_name', right_on = 'name').set_index('Arrow ID')
# merge with df_raw to get the 'required'
#rowIDs = df_arrow_int.loc[df_arrow_int['required']=='no'].index
#df_arrows.loc[rowIDs, 'expression']=''

# expression for text-entry fields (the commented solution does not continue if the field is left empty)
# df_arrows.loc[df_arrows['source_type']=='text','expression'] = '${'+df_arrows['source_name'] + '}!=' + '\'\''
df_arrows.loc[df_arrows['source_type']=='text','expression'] = '(${'+df_arrows['source_name'] + '}!=' + '\'\' or ${'+df_arrows['source_name'] + '}=' + '\'\')'

# expression for all the other select_one
df_arrows.loc[df_arrows['source_type']=='select_one','expression'] = '${'+df_arrows['source_name'] + '}=' + '\'' + df_arrows['select_option'] + '\''

# expression for select_multiple
df_arrows.loc[df_arrows['source_type']=='select_multiple','expression'] = 'selected(${'+df_arrows['source_name'] + '},\'' + df_arrows['select_option'] + '\')'

# expression for source being a calculate
df_arrows.loc[df_arrows['source_type']=='calculate','expression'] = '${'+df_arrows['source_name'] + '}=1'


#%% Expression for COUNT targets

# expression for target being a count---> in this case the expression depends not on the source but on the target!
counters=df.loc[df['odk_type']=='count'].index
m = df_arrows['target'].isin(df.loc[df['odk_type']=='count'].index) # mask for connectors that point to 'count' objects
df_arrows.loc[m,'expression'] = 'number(' + df_arrows.loc[m,'expression'] + ')'

# add arrow weight to counter
m = df_arrows['value'].isin(['1','2','3']) & (df_arrows['target'].isin(df.loc[df['odk_type']=='count'].index))
df_arrows.loc[m,'expression'] =  df_arrows.loc[m,'value'] + ' * ' + df_arrows.loc[m,'expression']

# for counters you must combine the expression of all icoming arrows into the one expression of that counter. 
# from there on, a rhombus, referring to a counter can lookup the entire expression



#%% expression for rhombus

m = df_arrows['source_type']=='rhombus'
# remove prefix 'stored_'
# ATTENTION! There is a BUG in pandas, replace(.... inplace = True) is not working!
df_arrows.loc[m, 'source_name'] = df_arrows.loc[m, 'source_name'].replace(r'^stored_', r'', regex = True)

# look up the odk_type that the rhombus is refering to
df_arrows = df_arrows.merge(df[['odk_type','name']],how='left',left_on='source_name',right_on='name')
# get rid of the 'name' column (was just needed for merging) and rename 'odk_type' column, to avoid confusion
df_arrows.drop('name',axis=1,inplace=True)
df_arrows.rename(columns={'odk_type':'rhombus_refer_to_odk_type'},inplace=True)

# look up the value of the rhombus, it contains info about the logic
df_arrows = df_arrows.merge(df[['value']],how='left',left_on='source',right_index=True)
df_arrows.rename(columns={'value_x':'value','value_y':'value_of_rhombus'},inplace=True)
# set all 'NaN' to empty strings
df_arrows=df_arrows.fillna('')


# when rhombus refers to a an integer or decimal (OH BOY, IN YI, AGE IS A CALCULATE!!!)
m = ((df_arrows['source_type']=='rhombus') & (df_arrows['rhombus_refer_to_odk_type'].isin(['integer','decimal']))) | (df_arrows['source_name']=='p_age')
df_arrows.loc[m,'value_of_rhombus'] = df_arrows.loc[m,'value_of_rhombus'].str.replace(r'^[^<=>]+','',regex=True) # only keep what comes after <,= or >
df_arrows.loc[m,'value_of_rhombus'] = df_arrows.loc[m,'value_of_rhombus'].str.replace('?','',regex=False) # remove the '?' at the end
df_arrows.loc[m,'expression'] = '${'+df_arrows['source_name'] + '}' + df_arrows['value_of_rhombus']
df_arrows.loc[m & (df_arrows['value']=='No')] = df_arrows.loc[m & (df_arrows['value']=='No')].replace({'<=':'>','>=':'<','<':'>=','>':'<='},regex=True)

# when rhombus refers to a select_one yesno
m = (df_arrows['source_type']=='rhombus') & (df_arrows['rhombus_refer_to_odk_type']=='select_one yesno')
df_arrows.loc[m,'expression'] = '${'+df_arrows['source_name'] + '}=' + '\'' + df_arrows.value + '\''

# now the real select_ones:
# first line is for MSFeCARE PED, uncomment and comment 2nd when doing ped 
#m = (df_arrows['source_type']=='rhombus') & df_arrows['rhombus_refer_to_odk_type'].str.contains('select_',na=False) & (df_arrows['rhombus_refer_to_odk_type']!='select_one yesno') & (df_arrows['source_name']!='p_age')
m = (df_arrows['source_type']=='rhombus') & df_arrows['rhombus_refer_to_odk_type'].str.contains('select_',na=False) & (df_arrows['rhombus_refer_to_odk_type']!='select_one yesno')
df_arrows.loc[m,'value_of_rhombus'] = df_arrows.loc[m,'value_of_rhombus'].str.extract(r'\[(.*?)\]',expand=False)
# merge again with df_choices to get the 'name' of the selected option (also needed for select_multiple!)
df_arrows = df_arrows.merge(df_choices[['list_name','name','label::en']],                 how='left',left_on=['source_name','value_of_rhombus'],right_on=['list_name','label::en'])
# when the outgoing arrow is YES (means that what is in RHOMBUS is TRUE)
df_arrows.loc[m & (df_arrows['value']=='Yes'),'expression'] =  '${'+df_arrows['source_name'] + '}=' + '\'' + df_arrows['name'] + '\''
# when the outgoing arrow is NO (means that what is in RHOMBUS is FALSE)
df_arrows.loc[m & (df_arrows['value']=='No'),'expression'] =  '${'+df_arrows['source_name'] + '}!=' + '\'' + df_arrows['name'] + '\''

# when rhombus refers to select_multiple
#m = (df_arrows['source_type']=='rhombus') & (df_arrows['rhombus_refer_to_odk_type']=='select_multiple')
#df_arrows.loc[m,'value_of_rhombus'] = df_arrows.loc[m,'value_of_rhombus'].str.extract(r'\[(.*?)\]',expand=False)
# when the outgoing arrow is YES (means that what is in RHOMBUS is TRUE)
df_arrows.loc[m & (df_arrows['value']=='Yes'),'expression'] = 'selected(${'+df_arrows['source_name'] + '},\'' + df_arrows['name'] + '\')'
# when the outgoing arrow is NO (means that what is in RHOMBUS is FALSE)
df_arrows.loc[m & (df_arrows['value']=='No'),'expression'] = 'not(selected(${'+df_arrows['source_name'] + '},\'' + df_arrows['name'] + '\'))'


# when rhombus refers to calculate (AVOID THAT REFERENCE TO p_age GETS OVERWRITTEN!!! (SEE REFER TO INTEGER))
m = (df_arrows['source_type']=='rhombus') & (df_arrows['rhombus_refer_to_odk_type']=='calculate') & (df_arrows['source_name']!='p_age')
# when the outgoing arrow is YES (means that what is in RHOMBUS is TRUE)
df_arrows.loc[m & (df_arrows['value']=='Yes'),'expression'] = '${'+df_arrows['source_name'] + '}=1'
# when the outgoing arrow is NO (means that what is in RHOMBUS is False)
df_arrows.loc[m & (df_arrows['value']=='No'),'expression'] = '${'+df_arrows['source_name'] + '}=0'


# when rhombus refers to a count (in this case we must combine all 'expressions' of the incoming arrows into the count object 
# with ' + ') and put the result into the 'expression' of the rhombus that is refering to it
m = (df_arrows['source_type']=='rhombus') & (df_arrows['rhombus_refer_to_odk_type']=='count')
df_arrows.loc[m,'value_of_rhombus'] = df_arrows.loc[m,'value_of_rhombus'].str.replace(r'^[^<=>]+','',regex=True) # only keep what comes after <,= or >
df_arrows.loc[m,'value_of_rhombus'] = df_arrows.loc[m,'value_of_rhombus'].str.replace('?','',regex=False) # remove the '?' at the end

# new mask to get the df_arrows of all connectors that point to counters
m1 = df_arrows['target'].isin(df.loc[df['odk_type']=='count'].index) # mask for connectors that point to 'count' objects
gk = df_arrows.loc[m1].groupby('target') # group them by counters

for elem, group in gk:
    # for each counter (elem), combine the expressions of all incoming arrows into a single one, concatenated with +
    full_expression=' + '.join(filter(None,group['expression']))
    # put result into brackets, because comparison is executed BEFORE +
    full_expression = '(' + full_expression + ')'
    
    # lookup the 'name' of the counter in df, based on the id = target
    counter_name = df.loc[elem,'name']
    
    # check in df_arrows where the source_name is 'counter_name'
    # for the 'No' arrow we invert >, < and = of 'value of rhombus'
    m2 = (df_arrows['source_name']==counter_name) & (df_arrows['value']=='No')
    df_arrows.loc[m & m2,'value_of_rhombus'] = df_arrows.loc[m & m2,'value_of_rhombus'].replace({'<=':'>','>=':'<','<':'>=','>':'<=','=':'!=','!=':'='},regex=True)
    df_arrows.loc[m & (df_arrows['source_name']==counter_name),'expression'] = full_expression + df_arrows['value_of_rhombus']


# In[33]:


# also drop the arrows that point to counters
df_arrows = df_arrows[df_arrows['target'].isin(df.loc[df['odk_type']!='count'].index)]

# drop no longer necessary columns
df_arrows.drop(columns=['value','value_of_rhombus','source_name','rhombus_refer_to_odk_type','list_name','label::en','name'],inplace=True)

# also drop count objects from df, they are no longer needed
df.drop(df[df['odk_type']=='count'].index,inplace=True)


# In[34]:


'''A rhombus can refer to a field that is not in the drawing. For instance, in the TT flow, where values like fever are used
but not calculated. Or in CHT, when patient info or hospital info is loaded into the input section. 
For this, the symbols are drawn in the beginning of the flow, pointing to the note field 'Load Data'. 
Once this is done, it is handled correctly by the script and they get included. '''


#%% Change sources that are 'select_options' to the 'select_xxx' itself


# get the select_xxx for each select_option:
dfa = df_raw.loc[df_raw['odk_type']=='select_option',['id', 'xml-parent']]
# some select_xxx are in a container-hint-media, their ids have been replaced with the ids of the containers
# therefore lookup the xml-parent of the select_xxx:
dfa = dfa.merge(df_raw[['id', 'xml-parent']], how = 'left', left_on='xml-parent', right_on = 'id', suffixes=('', '_y'))
# and if it is a container-hint-media, replace the 'xml-parent' of the select_option with the id of the container
container_ids = list(df_raw.loc[df_raw['odk_type']=='container_hint_media', 'id'])
m = dfa['xml-parent_y'].isin(container_ids)
dfa.loc[m, 'xml-parent'] = dfa.loc[m, 'xml-parent_y']

# make a dictionnary for replacing sources in df_arrows
d = dict(zip(dfa.iloc[:,0], dfa.iloc[:,1]))
df_arrows['source'].replace(d, inplace = True) # replace


# In[36]:


# for connectors where the source is inside a container-hint-media, replace the source with the container itself
df_arrows = df_arrows.merge(df_new_arrow_sources,how='left',left_on='source',right_index=True)
df_arrows.fillna('',inplace=True)
df_arrows.rename(columns={'odk_type':'container_type'},inplace=True)
m=(df_arrows['container_type']=='container_hint_media')
df_arrows.loc[m,'source']=df_arrows.loc[m,'container_id']
df_arrows.loc[m,'source_type']=df_arrows.loc[m,'odk_type_of_content']


# In[37]:


# get container_ids of pages
container_ids = df_arrows.loc[df_arrows['container_type']=='container_page','container_id'].unique()

# the ids of objects which are inside the page - containers
page_objects = df.loc[df['xml-parent'].isin(container_ids)].index

# get those page_objects which are the starting point of the flow INSIDE the page
page_starts = page_objects[~page_objects.isin(df_arrows['target'])]

# get the page_starts that are a rhombus (needed for later)
page_starts_rhombus = df.loc[page_starts].loc[df['odk_type']=='rhombus'].index

# get the page_objects where all objects in a single page are notes (needed for later)

# get page_start - container_id pairs
dfnew_connectors = df.loc[page_starts,['xml-parent']].reset_index().rename(columns={'id':'target','xml-parent':'source'})

# add missing columns
dfnew_connectors = dfnew_connectors.reindex(columns=['source','target','source_type','expression','container_id','container_type'])
dfnew_connectors['source_type']='page'
dfnew_connectors.fillna('',inplace=True)

# concat that to df_arrows
df_arrows = pd.concat([df_arrows,dfnew_connectors])

# adding 'target_type' to df_arrows
df_arrows = df_arrows.merge(df['odk_type'],how='left',left_on='target',right_index=True)
df_arrows.rename(columns={'odk_type':'target_type'},inplace=True)



#%% Build a graph
df_edges = df_raw.loc[df_raw['edge']=='1']  # get all arrows from df_raw
df_edges = df_edges[(df_edges['source']!='') & (df_edges['target']!='')] # remove some artefact objects

dag = nx.from_pandas_edgelist(df_edges, source='source', target='target', create_using=nx.DiGraph) # build a graph

# check if there are loops
list(nx.simple_cycles(dag))

# get id of Data Loader: 
dataloader_id = df_raw[df_raw['value']=='Load Data']['id'].iloc[0]
# get edges that point to Data Loader:
dataloaderedges = dag.in_edges(dataloader_id)
# get parent nodes of data_loader
dataloaderelements = [x[0] for x in list(dataloaderedges)]

# drop data_loader and its predecessor nodes from dag
dag.remove_node(dataloader_id)
dag.remove_nodes_from(dataloaderelements)

# drop image nodes from dag
dag.remove_nodes_from(df_raw[df_raw['style'].str.contains('image',na=False)]['id'])


# In[40]:


# must run several times, because there might be elements without a single edge, 
# for instance a select_multiple at the beginning of a page
nodecount0 = 0
nodecount = len(dag)

while nodecount0 < nodecount:
    # get elements without incoming edges 
    # -> these are page roots or select_options, or elements inside a container_hint_media, or images, or hints, helps
    rootelements = [n for n,d in dag.in_degree() if d==0]  # elements that are origins

    # get the parents of the rootelements (pages or select_xxx or container_hint_media)
    m = df_raw['odk_type'].str.contains('container_',na=False) | df_raw['odk_type'].isin(['select_one', 'select_multiple'])
    parent_ids = list(df_raw[m]['id']) # ids of parents of root elements:
    df_roots = df_raw.loc[df_raw['id'].isin(rootelements) & df_raw['xml-parent'].isin(parent_ids)]  
    parent_root_edges = list(zip(df_roots['xml-parent'],df_roots['id']))

    # add parent_to_root_edges to dag
    dag.add_edges_from(parent_root_edges)
    nodecount0 = nodecount
    nodecount = len(dag)


# In[41]:


# taking into account shortcuts

df_shortcuts = df_raw.loc[df_raw['odk_type']=='goto',['id','name']]
df_shortcuts.replace({'name': r'^shortcut_'}, {'name': ''}, regex=True, inplace=True)
exit_nodes = df_raw[df_raw['name'].isin(df_shortcuts['name'].unique())]
exit_nodes_dict = dict(zip(exit_nodes['name'], exit_nodes['id']))

# dictionnary representing the edge towards a shortcut
node_to_shortcut = [x for x in dag.edges() if x[1] in list(df_shortcuts['id'])]
node_to_shortcut = dict(zip([x[1] for x in node_to_shortcut], [x[0] for x in node_to_shortcut]))

df_shortcuts['name'].replace(exit_nodes_dict, inplace = True) # replacing name of exit node by its id
df_shortcuts['id'].replace(node_to_shortcut, inplace = True) # replacing id of shortcut by id of parent node
# df_shortcuts now represents edges to be added to dag

# drop shortcut nodes in dag
shortcut_ids = df_raw[df_raw['odk_type']=='goto']['id']
dag.remove_nodes_from(shortcut_ids)

# add new edges
shortcut_edges = list(zip(df_shortcuts['id'], df_shortcuts['name']))
dag.add_edges_from(shortcut_edges)



#%% DAG 
# build a CDSS graph without images, WITH dataloader
dag = gt.build_graph_cdss(df_raw)

# make edge parents -> children (for select_xxx and pages and container-hint-media this does not exist per default)
dag = gt.connect_to_parents_old_jupyter(dag, df_raw)

# connect shortcuts
dag = gt.connect_shortcuts(dag, df_raw)

# assign 'type', 'name', 'value' and group membership as attributes to nodes
if p.form_id == 'almsom': # in Somalia TT, the 'name' is in the content
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['value'], 'name')
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['odk_type'], 'type')
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['xml-parent'], 'group')
    #dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['y'], 'y')
else: 
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['name'].apply(ch.html2plain), 'name')
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['odk_type'], 'type')
    # if you want to strip off html from text:
    # dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['value'].apply(ch.html2plain), 'content')
    # if you want to keep the html in the text:
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['value'], 'content')
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['xml-parent'], 'group')
    dag = gt.add_nodeattrib(dag, df_raw['id'], df_raw['y'], 'y')

# assign content of edges as their 'logic' attribute -> there are edges in the form that contain 'Yes' or 'No'
dag = gt.add_edgeattrib(dag, df_raw, 'logic')





# ## CDSS topological sort of the global graph

# In[234]:


# to make legacy solution work with new functions, make columns with new names in df_raw
df_raw['parent'] = df_raw['xml-parent']

diagnosis_id_hierarchy = gt.get_diagnosis_sorting_id_jupyter(df_raw, p.diagnosis_order) # make diagnosis id hierarchy list

opt_prio = gt.hierarchy_select_options(df_raw) # hierarchy of select_options in the form
# combine diagnosis_sorting with select_option sorting
#opt_prio = d | opt_prio

# add an edge between dataloader and the first node of the form
dataloader_id = list(df_raw.loc[df_raw['value']=='Load Data', 'id'])[0]

# elements that are origins, these can be:
    # nodes that point to the dataloader
    # images that point to select_options
    # the beginning of the form 
# we exclude images; images are identified because they have no 'content' text
rootelements = [n for n,d in dag.in_degree() if d==0 and dag.nodes[n]['content']!='']
# if we take out data_loader elements (nodes that are not successors of the Data Loader), there should be only the beginning of the 
# flow left. If not, raise error
if len([n for n in rootelements if dataloader_id not in list(dag.successors(n))]) != 1:
    print('Attention, more than 1 graph entry point found, this is not allowed')

# if of the real start of the form, the first question after the data_loader
non_dataloader_rootelement = [n for n in rootelements if dataloader_id not in list(dag.successors(n)) and dag.nodes[n]['content']!=''][0]
dag.add_edge(dataloader_id, non_dataloader_rootelement)


# cautious, this is not working the function does not take into account images, it was built
# when there was only somalia that has no images
#rootelement = gt.get_graph_entry_point(dag)
# a node that comes BEFORE the dataloader. Using this insures that dataloader elements get it into df
dataloader_rootelement = [n for n in rootelements if dataloader_id in list(dag.successors(n)) and dag.nodes[n]['content']!=''][0]
rootelement = dataloader_rootelement

# get the global, flattened list of nodes sorted accordingly to universal graph
sorting = gt.get_topo_sort_cdss(dag, rootelement, opt_prio)

# keep load_data elements from df in dfa because they will get dropped during sorting
#dfa = df[~df.index.isin(dag.nodes)]
#df.drop(dfa.index, inplace=True)
I = df.index 
# only keep nodes from nodes_sorted that also exist in df (drop those that only exist in df_raw)
I_new = [node for node in sorting if node in I]

df = df.reindex(I_new) # df is now sorted, but there are many rows from df_raw, that no longer exist in df


# ### Build the 'relevant' logic for each object

# Building the logic: 
# 1. It must be done for each object independently, not for all at once, so there is a for loop
# 2. Start on the very top and go down the tree. This is the reason why we have topologically sorted df in the previous step
# 3. For each object lookup all sources in df_arrows (get all rows from df_arrows where the object is the target). 
# 4. Each source -> target arrow has a logic expression and the entire 'relevant' of the target is just the logic expressions of 
#     all incoming arrows, combined with a OR. 
# 5. A particular attention must be paid when a source is a 'note': then the 'expression' is empty. 
#     That is because there is no decision taken for 'notes', there is only one arrow coming out from a note. 
#     In this case we must use the relevant of the 'note' and 'calculate' source itself as the expression of note -> target
#     This would also be the case for 'calculate' objects, but their 'expression' has been populated already.  
#     If we do not do that, then the target would pop up independently of the 'note/calculate' condition. That would be wrong. 
#     Therefore, in df_source, the 'expression' for 'note' and 'calculate' is the 'relevant' of those sources. 
#     To get those into df_sources, we merge it with df accordingly. 
#     Therefore it is also important to do the logic from top to bottom, to assure that the relevant of the previous objects 
#     has already been done. 
# 6. Another particular interest is for rhombus (previously entered data). Here we also need the relevant of the rhombus 
#     itself, because it must be combined with the expresion by an AND. The rhombus itself is not seen to the user, 
#     so the logic depends on his relevant. For the terms to be executed in the right order, the 'relevant' must be put 
#     into brackets first. 
# 7. After those steps we have a df_sources dataframe where the 'expression' is correct for each of the arrows (each row). 
#     As said in (4) they are combined with OR and written into the 'relevant' of the object we are looking at. 
# 8. Another major problem are pages that contain ONLY notes. As objects inside a page automatically inherit the relevant 
#     of the page itself, their expression is entirely empty, they are only governed by the relevant of the page. 
#     At the exit of such a page, a note without an expression is pointing to a target outside the page. 
#     The following object would then always be displayed (or never, if there are other arrows pointing to)
#     To deal with this we identify all those objects (groups that contain only notes and )
# 9. Another problem is when the first object in a page is a rhombus. It also gets no relevant generated. As a consequence, 
#     we would get just the expression with 'and ()'

# In[235]:


# This is necessary because there are pages that contain 'note' fields only. 
# In this case notes that point ouf of the page, have no 'expression'. This interrupts the flow. 
# The solution is to give those 'notes' as expression the 'relevant' of the page

df_pageObjects = df.loc[df['xml-parent'].isin(df.loc[df['odk_type']=='container_page'].index)]

# get ids of pages that ONLY contain 'notes'
pure_note_pages=[]
gk = df_pageObjects.groupby('xml-parent')
for elem,frame in gk: 
    if len(frame.index) == len(frame.loc[frame['odk_type']=='note']):
        pure_note_pages.append(elem)

# get all the 'notes' that point out pages:
df_notes_out_pages = df_arrows.loc[df_arrows['source'].isin(df_pageObjects.index) & ~df_arrows['target'].isin(df_pageObjects.index) & (df_arrows['source_type']=='note')]

# among those get those notes that belong to 'pure_note_pages' - these are the notes you are looking for
df_notes_outof_pure_notes_pages = df_notes_out_pages.loc[df_notes_out_pages['container_id'].isin(pure_note_pages)]
df_notes_outof_pure_notes_pages = df_notes_outof_pure_notes_pages[['source','container_id']]
df_notes_outof_pure_notes_pages.set_index('source',inplace=True)


# In[236]:


df['relevant']=''

for elem in df.index:     
    # df_sources: dataframe that contains all connections pointing to the object 'elem'
    df_sources = df_arrows.loc[df_arrows['target']==elem,['source','source_type','expression']]
    # pulling the relevant of the sources into df_sources. This corresponds to the logic to each elem. 
    # 'xml-parent' is needed for rhombus at beginning of a page
    df_sources = df_sources.merge(df[['relevant','xml-parent']],how='left',left_on='source',right_index=True) 

    # when the source is a rhombus and it's relevant IS empty and the rhombus is on a page
    # you have to combine the expression with the relevant of the page
    # first merge with df again to the the relevant of the page
    df_sources = df_sources.merge(df[['relevant']],how='left',left_on='xml-parent',right_index=True,suffixes=('', '_page'))
    m=df_sources['source_type'].isin(['rhombus']) & (df_sources['relevant']=='') & df_sources['xml-parent'].isin(container_ids)
    df_sources.loc[m,'expression'] = df_sources.loc[m,'expression'] + ' and (' + df_sources.loc[m,'relevant_page'] + ')'    
    
    # when the source is a rhombus and it's relevant is NOT empty, you have to combine both with AND
    m=df_sources['source_type'].isin(['rhombus']) & (df_sources['relevant']!='')
    df_sources.loc[m,'expression'] = df_sources.loc[m,'expression'] + ' and (' + df_sources.loc[m,'relevant'] + ')'
    
    # when the source is a note, just take its relevant and put it into expression
    m=df_sources['source_type'].isin(['note'])
    df_sources.loc[m,'expression'] = df_sources.loc[m,'relevant']    

    # when the source is a note that is pointing out of a page that only contains 'notes' use the page relevant as 
    # its expression 
    m=df_sources['source'].isin(df_notes_outof_pure_notes_pages.index) # Mask to get pure note elements
    df_sources.loc[m,'expression'] = df_sources.loc[m,'relevant_page']
    #page_id = df.loc[df_sources.loc[m,'source'],'xml-parent'] # # get the page_ids of the pages the elments are in
    # df_sources.loc[m,'expression'] = df.loc[page_id,'relevant'].to_list()
    
    df_sources.loc[df_sources['expression']!='','expression'] = '(' + df_sources.loc[df_sources['expression']!='','expression'] + ')'
    
    if df.loc[elem,'odk_type']!='count':
        expressions = set(filter(None,df_sources['expression'])) # to reduce repetitions in expression
        df.loc[elem,'relevant'] = ' or '.join(expressions)
        if '( and (' in df.loc[elem,'relevant'] or '( or (' in df.loc[elem,'relevant']:
            print(elem, 'error!')
            print(df.loc[elem,'relevant'])
    else:
        # for counters the joining is number + number
        df.loc[elem,'relevant'] = ' + '.join(filter(None,df_sources['expression'])) 
        if '( and (' in df.loc[elem,'relevant'] or '( or (' in df.loc[elem,'relevant']:
            print(elem, 'error!')
            print(df.loc[elem,'relevant'])


# In[ ]:





# ### Taking into account pages

# In[237]:


'''
The topological sorting does not take into account pages (page-containers). Objects that are on the same page, must be 
grouped in order to wrap them up in begin_group ... end_group in odk. The topological_sort does not know what. 
Therefore we resort df: all objects that belong the a page, get all ligned up below the page container, 
preserving their overall sorting in df.
'''
pageids = df.loc[df['odk_type']=='container_page'].index
df.reset_index(drop=False, inplace=True)
df['new_index']=pd.to_numeric(df.index)
pagerows = df.loc[df['odk_type']=='container_page'].index
df = df.merge(df[['id','new_index']], how='left', left_on='xml-parent', right_on='id', suffixes = ('', '_p'))
df.loc[df['new_index_p'].notna(), 'new_index'] = df['new_index_p']
df.drop(columns=['id_p','new_index_p'], inplace=True)

g = df.groupby('xml-parent') # group by pages
for name, frame in g:  # for each page
    k=0.001
    for i in frame.index: # for each element in that page
        if df.loc[i,'xml-parent'] in pageids: # if we are in a real page and not in root
            df.loc[i,'new_index'] = df.loc[i,'new_index']+k # add to the new index a small step
            k+=0.001
            
df.set_index('new_index', drop=True, inplace = True)
df.sort_index(inplace=True)
df.set_index('id', drop=True, inplace=True)


# In[238]:


# add 'end group' rows
# get the last objects of each page
df.reset_index(drop=False, inplace=True)
index_endgrouprows = df.loc[~df.duplicated(subset='xml-parent', keep='last') & df['xml-parent'].isin(pageids)].index+0.1

df_endgroup = pd.DataFrame(index=index_endgrouprows)
df_endgroup['odk_type']='end group'
df_endgroup['id']=df_endgroup.index

df = pd.concat([df_endgroup, df])
df.sort_index(inplace=True)
df.set_index('id', drop=True, inplace=True)


# In[239]:


# short term workaround for select_xxx + NAME to add the same name as list_name
m = df['odk_type'].isin(['select_one','select_multiple'])
df.loc[m,'odk_type'] = df.loc[m,'odk_type'] + ' ' + df.loc[m,'name']

# making df look like the 'survey' tab in an xls form
df[['repeat_count','appearance','required message::en','calculation']]=''
df=df[['odk_type','name','value','help::en','hint::en','appearance','relevant','constraint',        'constraint_message','required','required message::en','calculation','repeat_count','image::en']]
df.rename(columns={'odk_type':'type','value':'label::en','relevant':'relevance','constraint_message':'constraint message::en'},inplace=True)

# rename begin group
df.replace({'container_page':'begin group'}, inplace=True)
# add 'field-list'
df.loc[df['type']=='begin group','appearance']='field-list'

# keep the ids of the rhombus and drop the rhombus objects from df
# drop rhombus
df.drop(df.loc[df['type']=='rhombus'].index,inplace=True)

# in 'calculate' fields move 'relevance' to calculate
df.loc[df['type']=='calculate','calculation'] = df.loc[df['type']=='calculate','relevance']
# add 'number() to fit with odk '
df.loc[df['type']=='calculate','calculation'] = 'number(' + df.loc[df['type']=='calculate','calculation'] + ')'
# delete entry in relevance column of 'calcuate' rows
df.loc[df['type']=='calculate','relevance'] = ''


# In[240]:


# making df_choices look like the 'choices' tab in an xls form
df_choices.drop(columns=['odk_type'],inplace=True)


# In[241]:


# make a 'settings' tab
now = datetime.now()
version=now.strftime('%Y%m%d%H%M')
indx=[[1]]

settings={'form_title':p.form_title,'form_id':p.form_id,'version':version,'default_language':'en','style':'pages'}
df_settings=pd.DataFrame(settings,index=indx)


# In[242]:


# read the diagnoses and the corresponding ids
df_diagnoses = pd.read_csv(p.diagnosis_order)
diagnoses_dict=dict(zip(df_diagnoses.Name,df_diagnoses.id))


# ## make standalone

# In[243]:


# adding top questions and populating the 'calculate' column of the calculate fields in order to make the treatment flow 
# STANDALONE

# making the top questions 

# for the diagnostic flow as a shortterm we extract all the 'calculates' where the tooltip starts with 'load_'
# this is because, at this stage we no longer can distinguish the data-load-calculates from the normal calcualtes
# drawback is that now all data-loaders must have a tooltip starting with 'load_'. In the future this will be fixed, probably 
# by adding a new data_attribute 'load_data' and make a special data_loader object
tt_input_options = df.loc[(df['type']=='calculate') & df['name'].str.contains('load_',na=False),['type','name','label::en']]


tt_input_options.rename(columns={'type':'list_name'},inplace=True) # tt_input_options are 'contextual parameters'
tt_input_options['list_name']='data_load'
df_choices = pd.concat([df_choices,tt_input_options]) # concat the new options to df_choices

# make the first question for data load
# data_load = ['select_multiple calculate','data_load','Define adaptable parameters','','','','','','','','','','','']
data_load = ['select_multiple data_load','data_load','Define adaptable parameters','','','','','','','','','','','']

data_load = pd.DataFrame([data_load],columns=df.columns)
df = pd.concat([data_load,df])

# populate the load_ calculate fields
df.loc[(df['type']=='calculate') & df['name'].str.contains('load_',na=False),'calculation']='number(selected(${data_load}, \''+ df.loc[df['type']=='calculate','name'] + '\'))'


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[244]:


# populate constraint message to all select_multiple
df.loc[df['type'].str.contains('select_multiple',na=False),'constraint']='.=\'opt_none\' or not(selected(.,\'opt_none\'))'
df.loc[df['type'].str.contains('select_multiple',na=False),'constraint message::en']='**None** cannot be selected together with symptoms.'


# In[245]:


# load zscore_file containing drug dosages and zscore calculations into df
df = loadcalc(df, p.drugsfile, p.form_id)


# In[246]:


'''
From CHT Docs

Countdown Timer: A visual timer widget that starts when tapped/clicked, and has an audible alert when done. 
To use it create a note field with an appearance set to countdown-timer. 
The duration of the timer is the field’s value, which can be set in the XLSForm’s default column. 
If this value is not set, the timer will be set to 60 seconds.

Currently not implemented in TRICC, but hard coded here
'''
df.loc[df['name']=='label_rr_rate','appearance']='countdown-timer'


# ## quick fix hardcode some stuff for YI

# In[247]:


if p.form_id == 'yi':
    # hardcode calculation of age 'p_age'
    df.loc[df['name']=='p_age','calculation']= 'coalesce(${p_age_days},${p_age_weeks}*7)'


# In[248]:


# drop the Data Loader field, if not it will appear in the flow. 
df.drop(df.loc[df['label::en']=='Load Data'].index,inplace=True)

#%% add a 'diagnosis found' message after the diagnosis

# show the detected diagnosis right on detection
df.reset_index(inplace=True)
df.fillna('',inplace=True)
I = df.loc[df['name'].isin(diagnoses_dict.values())].index

for i in I:
    d_message = pd.DataFrame({'index':df.loc[i]['index']+'_dm','type': 'note',                                 'name':'dm_' + df.loc[i]['name'],'label::en':                                'Diagnosis found: ' + df.loc[i]['label::en'],                                'relevance':'number(${'+df.loc[i]['name']+'})=1'}, index=[i+0.1])
    
    #df = df.append(d_message, ignore_index=False)
    df = pd.concat([df, d_message], ignore_index = False)


# colorize the dm message
m = df['name'].str.contains('dm_',na=False)
df.loc[m,'label::en'] = '<span style="color: rgb(163, 92, 56);">' + df.loc[m,'label::en'] + '</span>'

# sort rows and reset index
df = df.sort_index()
df.set_index('index',inplace=True)


#%% Make CHT conform help fields
df = oh.helpfields(df)

#%% add required = true to all data entry fields shortterm to save some time

df.loc[~df['type'].isin(['note','calculate','begin group','end group','text', 'acknowledge', '']) & (df['required']==''),'required']='true()'

# but not to some and contextual parameters ()
skip = ['data_load', 'p_height', 'p_length', 'p_o2']

df.loc[df['name'].isin(skip),'required']='false()'


#%%for ped, add the proper p_age calculate row

# for 'ped' hardcode a 'p_age' calculate
if p.form_id == 'ped':
    df.loc[df['name']=='p_age', 'calculation'] = "if(${p_age_select}='2',2,if(${p_age_select}='4',4,if(${p_age_select}='6',6,if(${p_age_select}='12',12,if(${p_age_select}='24',24,if(${p_age_select}='36',36,48))))))"


#%% combine multiple instances of a calculate


df = calcombo(df, df_raw)


# put all calculates on top of df_survey

# because some are now below the treatment and then duplicates are preserved from df_tt which is wrong
df_calc = df.loc[df['type']=='calculate']
df.drop(df.loc[df['type']=='calculate'].index, inplace = True)
df = pd.concat([df_calc, df])


#%% make a summary xlx 


def make_summary(df, df_choices, diagnose_id_hierarchy, summaryfile):
    # need to reload diagnose_id_hierarchy, because the sorting here is wrong, because it is dervied from the 
    # drawing. There should be no diagnose_hierarchy in the dx flow, it makes no sense to me at all. 
    df_diagnose=df.loc[df['name'].isin(diagnose_id_hierarchy)].copy()
    df_diagnose['calculation']=''
    df_diagnose['relevance']='number(${' + df['name'] + '})=1'
    df_diagnose['appearance']='center'
    df_diagnose['type']='note'
    df_diagnose['label::en']='<p>' + df_diagnose['label::en'] + '</p>'
    df_diagnose['name']=df_diagnose['name'].replace({'d_':'label_'},regex=True)

    df_diagnose.index=df_diagnose.index+'label'
    
    intro = pd.read_excel(summaryfile).iloc[:6]
    
    endgroup = pd.read_excel(summaryfile).iloc[-2:]
    
    danger_signs = df_choices.loc[df_choices['list_name'].str.contains('select_signs') & ~df_choices['name'].str.contains('none')].copy()
    danger_signs['relevance']='selected(${' + danger_signs['list_name'] + '},\'' + danger_signs['name'] + '\')'
    danger_signs['type']='note'
    danger_signs['name']='label_' + danger_signs['name']
    danger_signs.index = danger_signs.index+'danger'
    
    df_summary = pd.concat([intro, df_diagnose, pd.read_excel(summaryfile).iloc[6:8], danger_signs, endgroup])
    
    df_summary.drop(columns=['list_name'], inplace = True)
    
    df_summary.fillna('', inplace=True)
    
    # make group relevance for danger sign group
    ds_relevance = ' or '.join(danger_signs['relevance'])
    df_summary.loc[df_summary['name']=='g_danger_signs', 'relevance'] = ds_relevance
    
    
    return df_summary


# In[257]:


df_diagnose = pd.read_csv(p.diagnosis_order)
diagnosis_id_hierarchy = list(df_diagnose['id'])


# In[258]:


df_summary = make_summary(df, df_choices, diagnosis_id_hierarchy, p.summaryfile)

# store df_summary
import pickle

with open(p.folder+'df_summary.pickle', 'wb') as handle:
    pickle.dump(df_summary, handle, protocol=pickle.HIGHEST_PROTOCOL)


#%% Make the xlsx file! 
 
#create a Pandas Excel writer using XlsxWriter as the engine
writer = pd.ExcelWriter(p.folder+p.form_id+'_dx.xlsx', engine='xlsxwriter')


df.to_excel(writer, sheet_name='survey',index=False)
df_choices.to_excel(writer, sheet_name='choices',index=False)
df_settings.to_excel(writer, sheet_name='settings',index=False)

writer.close()
