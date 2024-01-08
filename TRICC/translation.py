# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 14:47:42 2022
To extract and inject English strings from the excel and to update the translation file
@author: kluera
"""

import pandas as pd
from cleanhtml import html2plain
import re

def make_transtable(df_survey, df_choices):
    # Extracting strings from survey tab:
    dfl1 = df_survey.filter(like = '::') # extract text columns (for translation)
    # combine with 'type' and 'name' column
    dfl1 = pd.concat([df_survey[['type', 'name']], dfl1], axis = 1) 
    # drop 'calculate', 'end group', 'hidden', 'string', 'db:person' and empty rows ''
    dfl1 = dfl1[~dfl1['type'].isin(['calculate', 'end group', 'hidden', 'string', 'db:person', ''])]
    
    # Extracting strings from choices tab:
    dfl2 = df_choices.filter(like = '::') # extract text columns (for translation)
    # combine with 'list_name' and 'name' column
    dfl2 = pd.concat([df_choices[['list_name', 'name']], dfl2], axis = 1) 
    # drop empty rows ''
    dfl2 = dfl2[dfl2['list_name']!='']
    
    # combine survey and choices to one df
    dfl = pd.concat([dfl1, dfl2])
    dfl.fillna('', inplace = True)
    
    # sort columns so that label::en and label::fr are together, but put 'type', 'list_name', 'name' in front
    cols = sorted(dfl.filter(like = '::').columns)
    cols[:0] = ['type', 'list_name', 'name']
    dfl = dfl[cols]
    
    # sort rows alphabetically    
    dfl.sort_values(by=['type', 'list_name', 'name'], ascending=True, inplace = True)
    
    # drop image columns, they are not translated
    img_cols = dfl.filter(like = 'image').columns
    dfl.drop(columns = img_cols, inplace = True)
    
    return dfl


# update translation table by the xls table
# update criteria: 
# when the en column in the translation table does not exist, it gets created
# when the en column in the translation table exists, but is differnt, it gets updated
# input are the two translation tables, dfl from xls form and dft from the translation file
def update_trans(dfl, dft):
    
    encols = dfl.filter(like = '::en').columns # get the names of 'English' columns    
    encols = encols[~encols.str.contains('image')] # DROP IMAGE COLUMNS
    headcols = dfl.filter(regex = '^(?!.*(::)).*$').columns # get the non-text columns 
    frcols = dft.filter(regex = '::fr$').columns # get the names of the 'French' columns from the translation file
    
    # make list of columns the final output should have
    cols = encols.append(frcols).sort_values()
    cols = headcols.append(cols)
    
    # merge xls table and translation table on 'type', 'list_name', 'name'; that combo is unique to each row
    # the 'en' columns from the translation table will have a '_t' suffix
    dft_updated = dfl.merge(dft, on=['type', 'list_name', 'name'], how = 'left', suffixes= ('', '_t')) 
    dft_updated.fillna('', inplace = True)
    
    # update the EN text columns of the translation table by those from the xls form
    for col in encols:
        # rows where EN exists, but en_t column is empty (new strings)
        newrows = dft_updated.loc[(dft_updated[col]!='') & (dft_updated[col + '_t']=='')].index+2
        if len(list(newrows))>0:
            print('The following rows contain new English ', col, 'fields: ', list(newrows))
        
        # rows where en_t exists but does not match with en (updated English strings) (without html formatting)
        dft_updated[[col + '_clean', col + '_t_clean']] = dft_updated[[col, col + '_t']].applymap(html2plain)
        updated_rows = dft_updated.loc[(dft_updated[col + '_clean']!=dft_updated[col + '_t_clean']) & (dft_updated[col + '_t_clean']!='')].index+2
        if len(list(updated_rows))>0:
            print('The following rows contain updated English ', col, 'fields: ', list(updated_rows))
                 
    dft_updated = dft_updated[cols]
    # dft_updated.rename(columns=lambda x: re.sub('_t$','',x), inplace = True)
    
    return dft_updated


# update translations in the xls-form by the translation file
def import_trans(df, dft):
    '''Function to write the translated fields from the translation file into the dataframe. It works for the survey and for the choices tab'''
    # need a full copy of dft, to avoid that it gets manipulated when updating successive xls-form sheets(survey + choices)
    dft1 = dft.copy()
    # add missing columns to df
    
    #check which cols actually exist in the file that gets the updates inserted
    textcols = df.filter(like = '::').columns # get the names of textcolumns from the translation file
    textcols = [re.search('.+(?=::)', s).group(0) for s in textcols] # strip of ::language code for the column names
    textcols = list(set(textcols)) # remove duplicates
    textcols = [s for s in textcols if s != 'image'] # drop the image column, it needs no translation, it contains the image filename
    
    # see which of those textcols have translated columns in dft1
    textcols_dft = dft1.columns[dft1.columns.str.contains('|'.join(textcols))]
    
    # from those drop the original ENGLISH ones, to avoid dft1 updating the English strings
    textcols_dft = [s for s in textcols_dft if '::en' not in s]
    
    # add new translation columns into df
    df = pd.concat([df,pd.DataFrame(columns=textcols_dft)], axis=1)
    
    # get NON_text columns from dft1
    nontext_cols_dft = list(filter(lambda x: '::' not in x, dft1.columns))
    
    # extract from dft1 the index columns AND the translated columns
    dft1 = dft1[nontext_cols_dft + textcols_dft]
    
    # nan values are not correctly updated, so reset them to an empty string ''
    df.fillna('', inplace=True)
    dft1.fillna('', inplace=True)
    # df_original_english = df['label::en'] # keep the original English, so that the translation file does not overwrite it. 
    
    if 'list_name' not in df.columns:
        df.set_index(['type', 'name'], inplace = True) # set ['type', 'name'] as multiindex for updating
        dft1.drop_duplicates(subset=(['type', 'name']), inplace=True) # drop duplicates in the ['type', 'name'] combo (exist for choices tab elements, that have an empty 'name')
        dft1.set_index(['type', 'name'], inplace = True) # set the same index as in df in order to be able to update
        df.update(dft1)
    else:         
        df.set_index(['name', 'list_name'], inplace = True) # set ['type', 'name'] as multiindex for updating
        dft1.drop_duplicates(subset=(['name', 'list_name']), inplace=True) # drop duplicates in the ['name', 'list-name'] combo (exist for survey tab elements, that have an empty 'list-name')
        dft1.set_index(['name', 'list_name'], inplace = True) # set the same index as in df in order to be able to update
        df.update(dft1)    
    
    df.reset_index(inplace=True) # setting index back to the way it was
    #df = df[cols] # reduce to those columns (if not, then the survey tab would also have columns from the choices tab and vice versa)
    
    df['image::fr'] = df['image::en'] # make a French column with the same images as in En
    #df['label::en'] = df_original_english # bring back English from the original file
    
    return df


