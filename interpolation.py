#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  2 10:14:10 2022

@author: w5i
"""
import numpy as np

a = [226026,
216994,
210643,
207168,
202690
    ]

def compute(a):

    def interpolation(d, x):
        output = d[0][1] + (x - d[0][0]) * ((d[1][1] - d[0][1])/(d[1][0] - d[0][0]))
     
        return output
    result = {key: 0 for key in np.linspace(2021, 2050,30)}
    
    year = [2021,2025,2030,2035,2050]
    for i,y in enumerate(year):
        result[y] = a[i]
    
    for i in range(4):
        for j in range(year[i], year[i+1]):
            result[j+1] = round(interpolation([[year[i],a[i]], [year[i+1],a[i+1]]],j+1),3)
    aa = list(result.values())
    return aa

print(compute(a))