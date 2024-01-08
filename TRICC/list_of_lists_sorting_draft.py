#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 13:52:09 2023

@author: rafael
"""
from itertools import product

# When this is applied, the graph must already by without cycles. 
# This assures that the sorting of nodes in the lists is not contradictory 
# For instance, there is never a list with [..., a, b, ...] and another with [..., b, ..., a, ...]

# example lists
l0 = ['a','b', 'c','x','y','z']
l1 = ['d','b', 'g','c', 'z', 'w','e']
l2 = ['g', 'b', 'h']

# build a list of lists. This is where we would start, as we already have a list of lists
l_of_ls= [l0, l1, l2]

topo_order = l0 # start with the most important diagnosis
topo_order_new=[]  # this will be the sorting of all the nodes from all the diagnosis

# select the second list and merge it with topo_order (later make a for loop)
l=l1


# continue as long as there are still elements in the diagnosis list, that are not written into topo_order
while len(l)>0:
    # iterate over all possible pairs of nodes from l and topo_order
    for n in product(range(len(l)), range(len(topo_order))):
        print(l[n[0]], topo_order[n[1]])
        # check if the node from the diagnosis is in topo_order
        if l[n[0]] == topo_order[n[1]]:
            topo_order_new = topo_order_new + topo_order[:n[1]] + l[:n[0]] + [topo_order[n[1]]]
            topo_order = topo_order[n[1]+1:]
            
            if l[n[0]+1:]==[]:
                topo_order_new = topo_order_new + topo_order
                
            l=l[n[0]+1:]
            print(topo_order_new)
            break
    # if we have not broken out of the loop; that means that in the end, there were nodes in the diagnosis list, 
    # that do not yet exist in topo_order; these get attached to the end of topo_order
    else: 
        topo_order_new = topo_order_new + l
        print('Appending remaining nodes to the end of the topo_order')
        print(topo_order_new)
        print(l)
        l = []
    
            
            
        
    