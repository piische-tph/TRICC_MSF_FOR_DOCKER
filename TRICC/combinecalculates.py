# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 13:54:51 2022

@author: kluera
"""

def calcombo (df, df_raw):
    # get sub-df that contains calculate-diagnose duplicates only
    m = (df['type']=='calculate') & (df['label::en'] != '') & ~df['name'].str.contains('ds_',na=False)
    dfa = df.loc[m]
    dfa = dfa.loc[dfa['label::en'].duplicated(keep = False)]
    calcnames = dfa['label::en'].unique()

    for calcname in calcnames:
        expressions = set(df.loc[m & (df['label::en']==calcname), 'calculation']) # to get rid of repetitive logic expressions
        newcalc = ' or '.join(expressions)
        newcalc = 'number(' + newcalc + ')'
        df.loc[m & (df['label::en']==calcname), 'calculation'] = newcalc
        # print('For', calcname, 'the new calculation expression is:\n', newcalc)

        newname_id = df.loc[m & (df['label::en']==calcname)].index[0]
        newname = df_raw[df_raw['id']==newname_id]['name'].iloc[0]
        drops = df.loc[m & (df['label::en']==calcname)].index[1:]
        for s in df.loc[m & (df['label::en']==calcname)]['name']:
            # print('^'+s+'&', newname)
            df.replace(s, newname, regex=True, inplace = True)
        # print('The name of the combined calculate field is:', newname)
        df.drop(drops, inplace = True)
    return df