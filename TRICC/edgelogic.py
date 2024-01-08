#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  4 09:05:27 2022

@author: rafael
"""
import re
import networkx as nx
from sympy import S
from sympy import Symbol
from sympy.parsing.sympy_parser import parse_expr
from sympy import Eq, Not
import cleanhtml as ch
# adds the attribute 'True' to the edges where the source is of type specified in columnlist
# this is for objects that do not have any decision, typically there is only one edge leaving them
# whith 'True' as expression, when building the relevance, the relevance of the predecessor is unified with 
# 'True' so this leads to taking over the previous relevance. 
# typically applied to notes
def edge_assign_true(dag, logic, columnlist):
    e = [edge for edge in dag.edges if dag.nodes[edge[0]]['type'] in columnlist]
    logic.update(dict.fromkeys(e, S.true))
    return logic

def edge_assign_sourcename(dag, logic, logicmap, negated_logicmap, columnlist):
    e = [edge for edge in dag.edges if dag.nodes[edge[0]]['type'] in columnlist]
    source_node_names = [dag.nodes[i[0]]['name'] for i in e] # names of source nodes of the edges
    odk_expressions =  ['${' + str(n) + '}=1' for n in source_node_names]
    logicsymbols = [Symbol(dag.nodes[i[0]]['name']) for i in e]
    
    #logicmap.update(dict(zip(logicsymbols, source_node_names)))
    logicmap_symbols = [str(i) for i in logicsymbols]
    logicmap.update(dict(zip(logicmap_symbols, odk_expressions)))
    # odk-expressions for ~expression
    negated_logicmap.update({'~' + n[0] : n[1][:-2] + '=0' for n in list(logicmap.items())})
    logic.update(dict(zip(e, logicsymbols)))
    
    return logic, logicmap, negated_logicmap

def edge_select_options(dag, logic, logicmap, negated_logicmap, columnlist):
    e = [edge for edge in dag.edges if dag.nodes[edge[0]]['type'] in columnlist]
    select_option_tuples = [(dag.nodes[list(dag.predecessors(e[0]))[0]]['name'],dag.nodes[e[0]]['name']) for e in e] # names of source nodes of the edges 
    odk_expressions = ['selected(${' + str(t[0]) + '},\'' + str(t[1]) + '\')' for t in select_option_tuples]
    logicsymbols = [Symbol(dag.nodes[list(dag.predecessors(e[0]))[0]]['name'] + '_' + dag.nodes[e[0]]['name']) for e in e]
    
    # logicmap.update(dict(zip(logicsymbols, select_option_tuples)))
    logicmap.update(dict(zip(logicsymbols, odk_expressions)))
    negated_logicsymbols = ['~' + str(n) for n in logicsymbols]
    negated_odk_expressions = ['not(selected(${' + str(t[0]) + '},\'' + str(t[1]) + '\'))' for t in select_option_tuples]
    negated_logicmap.update(dict(zip(negated_logicsymbols, negated_odk_expressions)))
    logic.update(dict(zip(e, logicsymbols)))
    
    return logic, logicmap, negated_logicmap

def edge_add_name_to_logic(dag, logic, logicmap, negated_logicmap, columnlist):
    e = [edge for edge in dag.edges if dag.nodes[edge[0]]['type'] in columnlist]
    source_nodes_names = [dag.nodes[i[0]]['name'] for i in e] # names of source nodes of the edges 
    edges_values = [dag.edges[i]['logic'] for i in e] # current 'logic' attribute of the edge
    expression_symbols = [Symbol(i+'_'+j) for (i,j) in zip(source_nodes_names,edges_values)]
    odk_expressions = ['${' + str(t[0]) + '} = \'' + str(t[1]) + '\'' for t in zip(source_nodes_names, edges_values)]
    logic.update(dict(zip(e, expression_symbols)))
    
    logicmap.update(dict(zip(expression_symbols, odk_expressions))) # update with odk expressions
    negated_expression_symbols = ['~' + str(n) for n in expression_symbols] # logicmap for negated odk_expressions
    negated_odk_expressions = [n.replace('\'No\'', '\'YES\'') for n in odk_expressions]
    negated_odk_expressions = [n.replace('\'Yes\'', '\'No\'') for n in negated_odk_expressions]
    negated_odk_expressions = [n.replace('\'YES\'', '\'Yes\'') for n in negated_odk_expressions]
    negated_logicmap.update(dict(zip(negated_expression_symbols, negated_odk_expressions)))
    # logicmap.update(dict(zip(expression_symbols, zip(source_nodes_names, edges_values))))
    
    return logic, logicmap, negated_logicmap



# makes objects which are necessary for giving a logic to rhombus edges
def make_rhombus_tags(dag, refer_types):
    # names of rhombus
    rhombus_names = [dag.nodes[node]['name'] for node in dag.nodes if dag.nodes[node]['type'] in ['rhombus']]
    # ids of rhombus
    rhombus_ids = [node for node in dag.nodes if dag.nodes[node]['type'] in ['rhombus']]   
    # map between rhombusnames and the types they refer to
    rhombusname_to_objectid = {name:[key for key in dag.nodes if dag.nodes[key]['name'] in [name] and \
                                     dag.nodes[key]['type'] in refer_types] for (name, key) \
                               in zip(rhombus_names, rhombus_ids)}
    # dict that links rhombus-name with type of the object it refers to
    rhombusname_to_objecttype = {name:[dag.nodes[key]['type'] for key in dag.nodes if dag.nodes[key]['name'] in [name] \
                                       and dag.nodes[key]['type'] in refer_types][0] for (name, key) in zip(rhombus_names, rhombus_ids)}
    rhombusname_to_objecttype
    return rhombus_names, rhombus_ids, rhombusname_to_objectid, rhombusname_to_objecttype


# get out_egdes for rhombus that refer to objects of types in 'columnlist' and that have the logic 'value'
def get_rhombus_edges(dag, columnlist, refer_types, value):
    rhombus_names, rhombus_ids, rhombusname_to_objectid, rhombusname_to_objecttype = make_rhombus_tags(dag, refer_types)
    edges = [edge for edge in dag.edges if dag.nodes[edge[0]]['type'] in ['rhombus'] and \
             rhombusname_to_objecttype[dag.nodes[edge[0]]['name']] in columnlist and dag.edges[edge]['logic'] == value]
    return edges


# assigns logic to out_edges of rhombus that refer to objects of type in columnlist (this is the right approach for 'calculate' and 'diagnosis')
# columnlist: types that the rhombus refer to 
def edge_get_logic_for_rhombus_calculate(dag, logic, columnlist, refer_types):
    for i in ['Yes', 'No']:
        ec = get_rhombus_edges(dag, columnlist, refer_types, i) # out_edges of rhombus referring to columnlist types, with value 'i' ('Yes' or 'No')
        obj_type = [dag.nodes[node]['name'] for node in [e[0] for e in ec]]
        if i =='No':
            obj_type = ['~'+i for i in obj_type]
        logic.update(dict(zip(ec, obj_type)))
    return logic

# assigns logic to out_edges of rhombus that refer to objects of type in columnlist (this is the right approach for 'calculate' and 'diagnosis')
# columnlist: types that the rhombus refer to
# refer_types: types that rhombus refer to in general
def edge_get_logic_for_rhombus_select(dag, logic, columnlist, refer_types):
    for i in ['Yes', 'No']:
        es = get_rhombus_edges(dag, columnlist, refer_types, i) # out_edges of rhombus referring to columnlist types, with value 'i' ('Yes' or 'No')
        obj_type = [dag.nodes[node]['name'] for node in [e[0] for e in es]]
        if i =='No':
            obj_type = ['~'+i for i in obj_type]
        logic.update(dict(zip(es, obj_type)))
    return logic

# assigns logic to out_edges of rhombus that refer to objects of type in columnlist (this is the right approach for 'calculate' and 'diagnosis')
# columnlist: types that the rhombus refer to
# refer_types: types that rhombus refer to in general
def edge_get_logic_for_rhombus_digit(dag, logic, columnlist, refer_types):
    for i in ['Yes', 'No']:
        ed = get_rhombus_edges(dag, columnlist, refer_types, i) # out_edges of rhombus referring to columnlist types, with value 'i' ('Yes' or 'No')
        # obj_type: (name of object, content of rhombus with only mathematical expression kept (regex substitute))
        obj_type = [(dag.nodes[node]['name'], re.sub(r'^[^<=>]+','', dag.nodes[node]['content']))  for node in [e[0] for e in ed]]
        if i =='No':
            obj_type = [(obj_type[0], '~'+obj_type[1]) for obj_type in obj_type]
        logic.update(dict(zip(ed, obj_type)))
    return logic
                   

# for contracting select_xxx with their select_options (works only if the child has only 1 parent)
def contract_node_descendant(dag, columnlist):
    n = [node for node in dag.nodes if dag.nodes[node]['type'] in columnlist]
    for node in n:
        for child in nx.descendants_at_distance(dag, node, 1):
            nx.contracted_nodes(dag, node, child, self_loops=False, copy = False) 
    return dag

def get_rhombus_refers(dag):
    '''gets the names of the nodes that all the rhombus in the DAG refer to
    @param dag: the graph
    @result rhombus_refer_names is a dictionary where the keys are the IDs of the rhombus nodes and the values
    are the names that those rhombus refer to'''
    # gets rid of the legacy prefix 'stored_' if still existant, in not, not
    rhombus_refer_names = {i:re.sub(r'^stored_', r'', dag.nodes[i]['name']) for i in dag.nodes if dag.nodes[i]['type']=='rhombus'}
    return rhombus_refer_names

def get_rhombus_content(dag):
    '''gets the content (what is written into the rhombus) without brackets (if existant)
    @param dag: the graph
    @result rhombus_content is a dictionary where the keys are the IDs of the rhombus nodes and the values
    are the content of those rhombus'''
    # {rhombusID : names of the nodes that rhombus refer to}
    # remove also eventual html from the content
    # strip of the brackets [ ] around the content and got only what is inside (for select_options)
    rhombus_content = {i:strip_off_brackets(ch.html2plain(dag.nodes[i]['content'])) for i in dag.nodes if dag.nodes[i]['type']=='rhombus'}
    return rhombus_content

def get_rhombus_equation(dag):
    '''gets the content (what is written into the rhombus) without brackets (if existant)
    @param dag: the graph
    @result rhombus_content is a dictionary where the keys are the IDs of the rhombus nodes and the values
    are the content of those rhombus'''
    # {rhombusID : names of the nodes that rhombus refer to}
    # remove also eventual html from the content
    # strip of the brackets [ ] around the content and got only what is inside (for select_options)
    rhombus_content = {i:re.sub(r'^[^<=>]+','',ch.html2plain(dag.nodes[i]['content'])) for i in dag.nodes if dag.nodes[i]['type']=='rhombus'}
    return rhombus_content

def get_rhombus_types(dag, refer_types):
    '''gets the types of the nodes that all the rhombus in the DAG refer to
    @param dag: the graph
    @param rhombus_refer_names: dictionary in which the keys are the nodes of the rhombus nodes and the values 
    are the names of the nodes that the rhombus refer to
    @result: rhombus_types is a dictionary where the keys are the IDs of the rhombus nodes and the values are
    the types of the nodes that they refer to.'''
    rhombus_refer_names = get_rhombus_refers(dag)
    rhombusIDs = rhombus_refer_names.keys() 
    # {rhombusID : type of node it refers to}
    rhombus_types = {i : [dag.nodes[n]['type'] for n in dag.nodes if dag.nodes[n]['name']==rhombus_refer_names[i] and dag.nodes[n]['type'] in refer_types][0] for i in rhombusIDs}
    
    return rhombus_types

def strip_off_brackets(s):
    try:
        s = re.search('\[(.*?)\]', s).group(1)
    except: 
        s = s
    return s
    
def get_rhombus_refering_to(dag, refer_types, refers_to):
    '''Gets the ids of all the rhombus that refer to nodes which have a type that is in the list 'refers_to'
    @param1 dag The graph
    @param2 refers_to List of types that the rhombus are supposed to refer to
    @result rhid is a list of IDs of the rhombus that refer to nodes of types in refers_to'''
    
    rhombus_refer_names = get_rhombus_refers(dag)
    rhombusIDs = rhombus_refer_names.keys() 
    
    rhombus_types = get_rhombus_types(dag, refer_types)
    rhid = [n for n in rhombusIDs if rhombus_types[n] in refers_to]
    return rhid

def get_rhombus_out_edges(dag, refer_types, refers_to, value):
    '''gets all out edges of all rhombus that refer to types in 'refers_to' and that have the value 'value' 
    @param1: dag the Graph
    @param2: refer_types: list of types that a rhombus can refer to 
    @param3: refers_to: types that the rhombus refer to have the out_edges this function gets
    @param4: value is the value of the edges. Rhombus out_edges only have Yes or No. this allows to filter them by the value'''
    rhid = get_rhombus_refering_to(dag, refer_types, refers_to)
    e = [e for e in dag.edges(data=True) if e[0] in rhid and e[2]['logic']==value]
    return e

def assign_refername_to_edges(dag, refer_types, refers_to, value):
    '''This function assigns as logic to rhombus_out_edges with 'value' 
    the name of the node that the rhombus refer to if the value is Yes
    If the value is 'No' it gets the negated name: ~name
    This is the logic when refers_to is a 'calculate' or a 'diagnosis'
    @param1 dag The graph
    @param2 refer_types a list of types that a rhombus could refer to
    @param3 refers_to types that the rhombus with those out_edges refer to
    @param4 value Yes or No are the possible values for an rhombus out_edge'''
    # get a {rhombusID: names of the nodes the rhombus refer to}
    rhombus_refer_names = get_rhombus_refers(dag)
    rhombus_logicsymbols = {i:Symbol(j) for (i,j) in zip(rhombus_refer_names.keys(), rhombus_refer_names.values())}
    # updating logicmap is not necessary, because the rhombus uses expressions that already exist on edges it refers to
    #logicmap.update(dict(zip(rhombus_logicsymbols.values(), rhombus_refer_names.values())))
    
    # get the out edges of the rhombus that refers_to with the 'value
    e = get_rhombus_out_edges(dag, refer_types, refers_to, value)
    e_logic = {}
    if value =='Yes':
        e_logic.update({(e[0],e[1]):rhombus_logicsymbols[e[0]] for e in e}) # logic for those edges
    elif value =='No':
        e_logic.update({(e[0],e[1]):Not(rhombus_logicsymbols[e[0]]) for e in e}) # logic for those edges
        
    nx.set_edge_attributes(dag, e_logic, name = 'logic') # assign logic to edges
    
    return dag

def assign_refername_and_content_to_edges(dag, refer_types, refers_to, value):
    '''This function assigns as logic to rhombus_out_edges with 'value' 
    the name of the node that the rhombus refer to if the value is Yes
    If the value is 'No' it gets the negated name: ~name
    This is the logic when refers_to is a select_one or select_multiple
    @param1 dag The graph
    @param2 refer_types a list of types that a rhombus could refer to
    @param3 refers_to types that the rhombus with those out_edges refer to
    @param4 value Yes or No are the possible values for an rhombus out_edge'''
    # get a {rhombusID: names of the nodes the rhombus refer to}
    rhombus_refer_names = get_rhombus_refers(dag)
    # get a {rhombusID: rhombusContent}
    rhombus_content = get_rhombus_content(dag)
    # from the content of the rhombus, get the name of the corresponding select_option
    
    rhombus_types = get_rhombus_types(dag, refer_types)
    
    # map between rhombus content and the name of the select_option it refers to (for rhombus refering to select_one and select_multiple)
    rhombus_content_to_refername = {dag.nodes[n]['content']:dag.nodes[n]['name'] for n in dag.nodes if dag.nodes[n]['content'] in rhombus_content.values() and dag.nodes[n]['type'] in ['select_option']}
    
    # map between rhombusID and the name of the select_option it is refering to 
    rhombus_select_optionname = {c:rhombus_content_to_refername[rhombus_content[c]] for c in rhombus_content if rhombus_types[c] in refers_to}
    
    # refername_content = dict(zip(rhombus_refer_names.keys(),   [i+';'+j for (i,j) in zip(rhombus_refer_names.values(), rhombus_content.values())]))
    
    # rhombus_refername_option_name = dict(zip(rhombus_select_optionname.keys(),[(rhombus_refer_names[n], rhombus_select_optionname[n]) for n in rhombus_select_optionname.keys()] ))
    
    rhombus_logicsymbols = dict(zip(rhombus_select_optionname.keys(), [Symbol(rhombus_refer_names[n]+ '_' + rhombus_select_optionname[n]) for n in rhombus_select_optionname.keys()]))  # symbols for logical expressions
    # logicmap.update(dict(zip(rhombus_logicsymbols.values(), rhombus_refername_option_name.values())))
    
    # get the out edges of the rhombus that refers_to with the 'value'   
    e = get_rhombus_out_edges(dag, refer_types, refers_to, value)
    e_logic = {}
    if value =='Yes':
        e_logic.update({(e[0],e[1]):rhombus_logicsymbols[e[0]] for e in e}) # logic for those edges
    elif value =='No':
        e_logic.update({(e[0],e[1]):Not(rhombus_logicsymbols[e[0]]) for e in e}) # logic for those edges
        
    nx.set_edge_attributes(dag, e_logic, name = 'logic') # assign logic to edges
    
    return dag

def assign_refername_and_edgevalue_to_edges(dag, refer_types, refers_to, value):
    '''This function assigns as logic to rhombus_out_edges with 'value' 
    the name of the node that the rhombus refer to and the current logic of the edge. 
    If the current edge logic is YES, it would be 'name;Yes' if no 'name;No'
    This is the logic when refers_to is a select_one yesno
    @param1 dag The graph
    @param2 refer_types a list of types that a rhombus could refer to
    @param3 refers_to types that the rhombus with those out_edges refer to
    @param4 value Yes or No are the possible values for an rhombus out_edge'''
    # get a {rhombusID: names of the nodes the rhombus refer to}
    rhombus_refer_names = get_rhombus_refers(dag)
    # get the out edges of the rhombus that refers_to with the 'value
    e = get_rhombus_out_edges(dag, refer_types, refers_to, value)
    
    rhombus_logicsymbols = {e[0]:Symbol(rhombus_refer_names[e[0]]+'_'+value) for e in e}
    
    e_logic = {}
    e_logic.update({(e[0],e[1]):rhombus_logicsymbols[e[0]] for e in e}) # logic for those edges
        
    nx.set_edge_attributes(dag, e_logic, name = 'logic') # assign logic to edges
    
    return dag

def assign_refername_and_content_equation(dag, logicmap, negated_logicmap, refer_types, refers_to, value):
    '''This function assigns as logic to rhombus_out_edges with 'value' 
    the name of the node that the rhombus refer to if the value is Yes
    If the value is 'No' it gets the negated name: ~name
    This is the logic when refers_to is a select_one or select_multiple
    @param1 dag The graph
    @param2 refer_types a list of types that a rhombus could refer to
    @param3 refers_to types that the rhombus with those out_edges refer to
    @param4 value Yes or No are the possible values for an rhombus out_edge'''
    # get a {rhombusID: names of the nodes the rhombus refer to}
    rhombus_types = get_rhombus_types(dag, refer_types) #{rhombusID:refers_to_type}
    rhombus_refer_nodes = [k for k in rhombus_types.keys() if rhombus_types[k] in refers_to]  # list of rhombus nodes that refer to 'refers_to'
    
    rhombus_refer_names = get_rhombus_refers(dag)
    # {rhombusID : name of the node it refers to} - keep those that refer to 'refers_to' only
    rhombus_refer_names = {i:rhombus_refer_names[i] for i in rhombus_refer_nodes} 
    # get a {rhombusID: rhombusContent}
    rhombus_content = get_rhombus_equation(dag)
    rhombus_content = {i:rhombus_content[i] for i in rhombus_refer_nodes} # only keep those rhombus that refer to 'refers_to'
    
    #{rhombusID:(refer_name, content-equation), for instance ('p_age', '<12')}
    rhombus_name_content = dict(zip(rhombus_refer_names.keys(), list(zip(rhombus_refer_names.values(), rhombus_content.values()))))
    
    # only those that are unequal, for instance p_age>12 or p_age<12, but NOT p_age=12)
    rhombus_name_unequal = {i:rhombus_name_content[i] for i in rhombus_name_content.keys() if ('<' in rhombus_name_content[i][1]) or ('>' in rhombus_name_content[i][1])}
    # only those that are equal
    rhombus_name_equal = {i:rhombus_name_content[i] for i in rhombus_name_content.keys() if ('<'  not in rhombus_name_content[i][1]) and ('>' not in rhombus_name_content[i][1])}
    
    # {rhombusID : equation like 'p_age > 6'} and parse equation to symbolic sympy expression
    # for expressions with '<' and '>':
    refername_content = dict(zip(rhombus_name_unequal.keys(), [parse_expr(i+j) for (i,j) in rhombus_name_unequal.values()]))
    # for expressions that compare, for example: p_age = 24, parse to Eq(p_age,24)
    refername_content.update(dict(zip(rhombus_name_equal.keys(), [Eq(Symbol(i),float(j[1:])) for (i,j) in rhombus_name_equal.values()])))
    
    # add decimal and integer variables to logicmap
    newnames = set([i[0] for i in rhombus_name_content.values()])
    
    #logicmap.update({Symbol(i):i for i in newnames})
    # odk-style for decimal/integer variables
    logicmap.update({Symbol(i):'${' + str(i) + '}' for i in newnames})
    
    # need to add EQUAL TO expressions to logicmap
    logicmap.update({Eq(Symbol(i),float(j[1:])):'${' + i + '} ' + j for (i,j) in rhombus_name_equal.values()})
    # need to add UNEQUAL TO expressions to negated_logicmap
    negated_logicmap.update({Not(Eq(Symbol(i),float(j[1:]))):'${' + i + '} !=' + j[1:] for (i,j) in rhombus_name_equal.values()})
    
    # get the out edges of the rhombus that refers_to with the 'value'   
    e = get_rhombus_out_edges(dag, refer_types, refers_to, value)
    e_logic = {}
    if value =='Yes':
        e_logic.update({(e[0],e[1]):refername_content[e[0]] for e in e if e[0] in refername_content.keys()}) # logic for those edges
    elif value =='No':
        e_logic.update({(e[0],e[1]):Not(refername_content[e[0]]) for e in e if e[0] in refername_content.keys()}) # logic for those edges
        
    nx.set_edge_attributes(dag, e_logic, name = 'logic') # assign logic to edges
    
    return dag, logicmap, negated_logicmap


def parse_sympy_logic(s, negated_logicmap, logicmap):
    '''To convert sympy logical expressions into odk conform expressions. 
    :param s: is the relevance expression encoded as a sympy logical expression
    :param negated_logicmap: is the dictionary for negated expression like NOT(Fever)
    :param logicmap: is the dictionary for the non-negated expressions like ${d_fever}=1'''
    s = str(s) # convert sympy expression into string

    for key, value in negated_logicmap.items():
        s = s.replace(str(key), value)

    for key, value in logicmap.items():
            # first replace the (rare) EQUAL TO expressions like 'Eq(p_age, 24.0)'
            s = re.sub(r'Eq\((.+?),(.+?)\)', r'${\g<1>} =\g<2>', s)
            # replace str(key) by value, only if str(key) is not preceeded by characters 
            # from a-z / A-Z / 0-9, a underscore '_' or a curly open bracket { or 'Eq('
            s = re.sub('(?<![a-zA-Z0-9_{])' + str(key) + '(?![a-zA-Z0-9_}])', value, s)
            # s = re.sub('(?<![a-zA-Z0-9_{])' + str(key) + '(?![a-zA-Z0-9_}])', value, s)
        
    s = s.replace('|', 'or')
    s = s.replace('&', 'and')
    
    return s