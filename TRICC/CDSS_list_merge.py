#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 13:52:09 2023

@author: rafael

Tools to merge sorted lists into one, while still respecting the sorting of every one of those lists. For this to work, 
there must not be any contradiction of sorting in the lists. For instance there must not be a list where `a` comes before `b` and 
another one where `b` comes before `a`. [..., a, b, ...] and another with [..., b, ..., a, ...]
This is actually a representation of a cycle inside the CDSS flow. Therefore, prior to buiding the global sorting, one must contract all 
duplicate nodes, check the graph for cycles and resolve them. 
This function is mostly used for sorting treatment nodes in Almanach Somalia, Libya or MSFeCARE. 
It requires first a 'list of lists' to be build. Each list in this `list of lists` contains all nodes for a specific diagnosis, sorted the 
CDSS way. 
The lists themselves are sorted among each other, degressive diagnosis hierarchy order. 
"""
from itertools import product

def merge_list(diagnosis_sort, global_sort):
    '''Function to merge the list `diagnosis_sort` into the list `global_sort`. Returns the new global_sort list. The function iterates
    over the matrix product of `diagnosis_sort` and `global _sort` and checks if the nodes in diagnosis_sort appear in the global_sort, 
    while respecting the sorting of both. If it finds a fit, all the nodes from diagnosis_sort, that came prior to this node and that
    did not exist in the global_sort, get inserted into global_sort, right before the found node. It continues until the end of the
    global_sort list. When reached the end, and there are still nodes left in the diagnosis_sort, they get appended to the end of 
    `global_sort.'''
    global_sort_new = [] # this will be the new global sort
    # continue as long as there are elements in the `diagnosis_sort`, that are not written into `global_sort`
    while len(diagnosis_sort)>0:
        # iterate over all possible pairs of nodes from `diagnosis_sort` and `global_sort`
        for n in product(range(len(diagnosis_sort)), range(len(global_sort))):
            # check if the node from the diagnosis_sort is in global_sort
            if diagnosis_sort[n[0]] == global_sort[n[1]]:
                # stitch together the parts, the `global_sort_new` ends at the node we have just found
                global_sort_new = global_sort_new + global_sort[:n[1]] + diagnosis_sort[:n[0]] + [global_sort[n[1]]]
                # cut out from global_sort what has already been checked and pasted into global_sort_new
                global_sort = global_sort[n[1]+1:]
                # cut out from diagnosis_sort what has already been checked 
                diagnosis_sort = diagnosis_sort[n[0]+1:]
                
                # if all nodes from diagnosis_sort were in global_sort, then we append the remaining nodes from global_sort to the 
                # global_sort_new
                if diagnosis_sort[n[0]+1:]==[]:
                    global_sort_new = global_sort_new + global_sort
                
                break
        # if we have not broken out of the loop; that means that in the end, there remained nodes in the diagnosis_sort, 
        # that do not yet exist in global_sort; these get attached to the end of global_sort
        else: 
            global_sort_new = global_sort_new + diagnosis_sort
            diagnosis_sort = [] # set to zero to finish the while-loop
    
    return global_sort_new

