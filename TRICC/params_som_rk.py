#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 10:02:12 2023

@author: rafael
"""

### General
form_id = 'almlib'
form_title = 'Almanach Libya'
htmlcontent = False # whether the diagram  contains html in the content of objects
platform = 'cht'
testing = False
context_params_from_facility=False
mhsplit = True  # whether several nodes are combined into 1 (multiheadline split)
interrupt_flow = False
activity = 'treatment'

### Input Streamlit webapp folder
folder = '/home/rafael/Documents/git/Almanach-Libya/form/'
resource_folder = '/home/rafael/Documents/git/TRICC-Webapp/resources/'
inputfile_dx = folder+'dx.drawio'  # inputfile for jupyter notebook diagnostic
inputfile = folder+'tt.drawio' # inputfile for tricc-graph tt
diagnosis_order = folder+'diagnosis_order.csv'
input_trans = folder + 'translation.xlsx'
htmlfolder = folder + 'htm_files/' # folder where the html files are stored (that will replace the text in notes)

### Resources
cafile = resource_folder+'ca.xlsx'
summaryfile = resource_folder+'summary.xlsx'

### Output
output_folder = folder+'output_for_zip/' # folder where output files will be stored
output_xls = folder+'tt.xlsx'
output = output_folder+form_id+'.xlsx'
media_folder = output_folder+'media/images/'
updated_trans = folder + 'to_be_translated.xlsx'
zipfile = folder+'output/output'

### Input TRICC Repo folder
repo_folder = '/home/rafael/Documents/git/TRICC-Webapp/TRICC/'
drugsfile = repo_folder+'medications_zscores.xlsx'
headerfile = repo_folder+'formheader_cht.xlsx'
headerfile_pause = repo_folder+'formheader_cht_pause.xlsx'
breakpoints = repo_folder+'breakpoints.csv'