#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 10:02:12 2023

@author: rafael
"""
import os
path = os.getcwd()

### General
form_id = 'ped'
form_title = 'Ped'
htmlcontent = True # whether the diagram  contains html in the content of objects
platform = 'cht'
testing = False
context_params_from_facility=True
mhsplit = False  # whether several nodes are combined into 1 (multiheadline split)
interrupt_flow = True
activity = 'treatment'

### Input Streamlit webapp folder
folder = path + "/"
resource_folder = 'resources/'
inputfile_dx = folder+'uploaded_files/dx.drawio'  # inputfile for jupyter notebook diagnostic
inputfile = folder+'uploaded_files/tt.drawio' # inputfile for tricc-graph tt
diagnosis_order = folder+'uploaded_files/diagnosis_order.csv'
input_trans = folder+'uploaded_files/ped_fr.xlsx'

### Resources
cafile = resource_folder+'ca.xlsx'
summaryfile = resource_folder+'summary.xlsx'

### Output
output_folder = folder+'output_for_zip/' # folder where output files will be stored
output_xls = folder+'tt.xlsx'
output = output_folder+form_id+'.xlsx'
media_folder = output_folder+'media/images/'
updated_trans = output_folder+'ped_fr_newest.xlsx'
zipfile = folder+'output/output'

### Input TRICC Repo folder
repo_folder = os.path.join(path,'TRICC/')
drugsfile = repo_folder+'medications_zscores.xlsx'
headerfile = repo_folder+'formheader_cht.xlsx'
headerfile_pause = repo_folder+'formheader_cht_pause.xlsx'
breakpoints = repo_folder+'breakpoints.csv'
