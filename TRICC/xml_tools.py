#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 10:28:47 2023

@author: rafael
"""

from lxml import etree
from copy import deepcopy


# path = '/home/rafael/Documents/git/almsom/diagrams/tt.xml'
def parse_xform(path):
    root = etree.parse(path).getroot()
    return root


def replace_attribute(root, tag, attrib, oldvalue, newvalue):
    '''in all elements with the tag 'tag', that have the attribute 'attrib' with a value 'oldvalue', it gets replaced 
    with 'newvalue'
    Output is the updated tree 'root'
    '''
    for element in root.iter(tag):
        if element.attrib[attrib]==oldvalue:
            element.attrib[attrib]=newvalue
    return root


def make_notes_commcare_conform(root):
    '''Commcare regards simple note fields as text input fields. Fixed by this function. 
    1. Find all note element names. These are elements with the tag name 'bind' that have the attribute 'readonly' 
    and it is equal to 'true()'. Their name is written into the attribute 'nodeset'
    2. Find all the elements that have the tag 'input' and an attribute called 'ref' that has as value 
    the name of the note 'note_names' 
    3. Rename the tag from 'input' to 'trigger'
    4. The elements with the tag name 'text' and the attribute 'id' that has as value the 'note_names:label', 
    have a child element with the tag 'value'. Get the text of this element and create an exact sibling but with the 
    attribute: form="markdown". This will insure that markdown is rendered. 
    '''
    n = root.findall(".//{*}bind[@readonly]") # part (1)
    note_names = [n.attrib['nodeset'] for n in n if n.attrib['readonly']=='true()']
    
    inputs = root.findall(".//{*}input[@ref]") # part (2)
    note_inputs = [n for n in inputs if n.attrib['ref'] in note_names]

    [convert_to_trigger(n) for n in note_inputs] # part (3)
    
    note_names_label = [n+':label' for n in note_names] # add ':label' as suffix to note_names
    textvalues = root.findall(".//{*}text[@id]") # part (4)
    # get the children of the textvalues where id attribute has as value a name of a note with the tag 'value' 
    textvalue_children = [el.find("{*}value") for el in textvalues if el.attrib['id'] in note_names_label and el.attrib['id'] != '/data/label_lang-code:label'] 
   
    for i in textvalue_children:
        if i.text!='': 
            j = deepcopy(i)  # if no decopy, then i and j are the same node and the line below would write in i
            j.attrib['form']="markdown"
            i.addnext(j)
    
    return root


def convert_to_trigger(n):
    '''Converts tags of elements to 'trigger'. This is necessary for note elements in commcare, so they are 
    properly recognised. It also adds the appearance attribute 'minimal'.
    If not added, then note fields come with a greyed out 'OK, continue' message. 
    '''
    n.tag = 'trigger'
    n.attrib['appearance']="minimal" 

def remove_element(root, tag):
    '''Removes the element with the tag 'tag' from the tree '''
    m = root.find(tag) # meta block
    p = m.getparent() # parent of metablock
    p.remove(m) # delete metablock
    return root

def remove_meta_instance(root):
    '''Delete the bind note that Commcare does not like'''
    instance_bind = root.findall(".//{*}bind[@nodeset]") 
    for i in instance_bind:
        if i.attrib['nodeset']=='/data/meta/instanceID':
            p = i.getparent()
            p.remove(i)
    return root



def xform2commcare(path, output_file):
    root = parse_xform(path)
    root = replace_attribute(root, '{*}bind', 'type', 'decimal', 'double') # change from decimal to double
    root = make_notes_commcare_conform(root) # make real note fields (on import Commcare considers them as note fields)
    root = remove_element(root, ".//{*}meta") # get rid of the meta block
    root = remove_meta_instance(root) # remove the bind element that is associated with the meta block to avoid this error:
    # Bind Node [/data/meta/instanceID] found but has no associated Data node. This bind node will be discarded!
    
    #s = etree.tostring(root) # write tree to string
    et = etree.ElementTree(root) # convert to an element tree
    et.write(output_file, pretty_print=True)
    return "Converted into commcare compliant xform"