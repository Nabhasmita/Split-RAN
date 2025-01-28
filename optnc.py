###
# optnc.py: This python file has the slice datarate, delay, origin and available network capacity as input.
# It selects functional split, baseband function placement and traffic routing of RAN slices so that
# the centalization degree is maximized
###
#Import the required libraries
from gurobipy import *
import time
import logging
import json
import math
import time
import numpy as np
import argparse
import os

isTest = False
parser = argparse.ArgumentParser()
parser.add_argument('-path','--path', help='path of the data directiory', required=False, default="data")
parser.add_argument('-out','--out', help='output directory', required=False, default="optnc_22")
parser.add_argument('-time','--time', help='output directory', required=False, type=int, default=2)
parser.add_argument('-max','--max', help='maximum instances', required=False, type=int, default=10)

args = vars(parser.parse_args())
#num_slice = args['slice']
data_path = args['path']
model_dir = args['out']
time_limit_mins = args['time']
max_length = args['max']
if(isTest):
    max_length = 1
tot_load = [100,200,300,400,500]


print(f"Data path: {data_path}")
print(f"Model path: {model_dir}")
print(f"isTest: {isTest}")
print(f"Max Length: {max_length}")
#print(f"num_slices: {num_slices}")

if(os.path.isdir(model_dir)):
    print("Model Directory exists.")
    #exit(0)
else:
    os.mkdir(model_dir)
    print(f"Model directory {model_dir} created.")
    
out_file = os.path.join(model_dir, f"out_{max_length}.json")
log_file = os.path.join(model_dir, f"log_{max_length}.txt")
if(not isTest):
    out_file2 = os.path.join(model_dir, f"out_{max_length}.csv")
    result_file2 = open(out_file2, "w")

logging.basicConfig(filename=log_file, filemode='a', 
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)
logging.Formatter.converter = time.gmtime
logger = logging.getLogger(__name__)

logger.info(f"Data path: {data_path}")
logger.info(f"Model path: {model_dir}")
logger.info(f"isTest: {isTest}")
logger.info(f"Max Length: {max_length}")
#logger.info(f"num_slices: {num_slices}")
logger.info(f"gurobi time limit: {time_limit_mins} mins")
logger.info("-"*40)
logger.info("-"*40)

#=====================================================useful functions===========================

def linkpath(links):
    link_path=[[0 for i in range(links)] for j in range(links)]
    for i in range(0,links):
        for j in range(0,links):
            if i==j:
                link_path[i][j]=1
    return link_path    

def cal_dem(tr, fs):
    f1=0.76*tr*2
    f2=0.17*tr*2
    f3=0.4*tr*2
    f4=0.2*tr*2
    if fs==0:
        cu=0
        du=f1+f2+f3+f4
        mh=0
    elif fs==1:
        cu=f1
        du=f2+f3+f4
        mh=tr
    elif fs==2:
        cu=f1+f2
        du=f3+f4
        mh=tr        
    elif fs==3:
        cu=f1+f2+f3
        du=f4
        mh=tr+2
    return cu,du,mh

result_dict = {}
for tl in tot_load:
    if(not isTest):
        logger.info(f"Load is: {tl}")
        logger.info("-"*40)
    file_name = os.path.join(data_path, f"data_{tl}.json")
    data = []
    with open(file_name, 'r') as f:
        data = json.load(f)
    if(isTest):
        print(data[0])
    
    lst_central= []
    lst_cost = []
    lst_reg_energy = []
    lst_edge_energy = []
    lst_mid_bandwidth = []
    lst_turn_on = []
    lst_reg_turn_on = []
    lst_edge_turn_on = []
    lst_tot_accept= []
    
    dt_idx=0
    for dt in data[0:max_length]:
        dt_idx+=1
        try:
            m = Model("optimization_model")     # Optimization Model
            m.setParam('OutputFlag', 0)
            m.setParam('TimeLimit', time_limit_mins*60)

             #=====================================================Network Topology======================
            CU=24  # Number of CUs in the network
            DU=40  #Number of DUs in the network
            fs=4  # Number of functional split
            users=50  # Number of users
            M=10000   # Big M

            num_rs=CU
            num_es=DU
            num_split=fs
            num_slice=30
            
            #Number of paths and links
            path1=50
            links=36
            #links capacity

           # Link X path matrix
         #   link_path=[[0 for i in range(path1)] for j in range(path1)]
            #link_path=linkpath(links)
            link_path=[
                [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            ]

                #which links are of which delay category
            p1=[]
            p2=[0,1,9,12,17,20,25,26,34,37,42,45]
            p3=[2,10,13,18,21,27,35,38,43,46]

            #Connectivity of RU X edge
            cond=[
                 [1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1],
                 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1],
                 
            ]

            #Path and edge connection
            path_connect=[
            [1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
                
            ]

            
            #Dynamic Parameters
            #========================================================================================

            # Capacity of CUs and DU and Links
            cap_c=[1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200]
            cap_d=[1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200,1200]
            
            ##################################

            link_cap=[500,500,150,150,500,500,150,500,500,150,150,500,500,150,500,500,150,150,500,500,150,150,500,500,150,500,500,150,150,500,500,150,500,500,150,150]

            ###################################            
             #Dynamic Parameters
            dem=dt['dem']
            cell=dt['cell']
            edge=dt['edge']
            delay=dt['delay']
            
            #=======================================================================================
            ct=[0.1,0.2,0.3,0.4]
            path_delay=[6,6,10,2,2,2,2,2,2,6,10,2,6,10,2,2,2,6,10,2,6,10,2,2,2,6,6,10,2,2,2,2,2,2,6,10,2,6,10,2,2,2,6,10,2,6,10,2,2,2]
            split_delay=[30,30,6,2]
           

            Q=[[0 for i in range(0,path1)]for j in range(0,num_slice)]
            for s in range(0,num_slice):
                for p in range(0,path1):
                    if path_delay[p]<=delay[s]:
                        Q[s][p]=1


            # Matrix generation for CU, DU and Midhaul demand of each slices according to the functionl split
            slice_cu=[[0 for f in range(0,num_split)]for s in range(0, num_slice)]
            slice_du=[[0 for f in range(0,num_split)]for s in range(0, num_slice)]
            t=[[0 for i in range(0, num_split)]for j in range(0,num_slice)]


            for s in range(0,num_slice):
                for f in range(0,num_split):
                    cu,du,mh=cal_dem(dem[s],f)
                    slice_cu[s][f]=cu
                    slice_du[s][f]=du
                    t[s][f]=mh


            # Decision variables==========================================================================
            #A slice is accepted or not
            g=[]
            for s in range(0, num_slice):
                g.append(m.addVar(vtype=GRB.BINARY, name="g[%d]" % (s)))

            #SlicexSplit variable
            k=[]
            for s in range(0,num_slice):
                k.append([])
                for f in range(0,num_split):
                    k[s].append(m.addVar(vtype=GRB.BINARY, name="k[%d,%d]" % (s,f))) 

            # #DRAN Split
            # for s in range(0,num_slice):
            #     m.addConstr(sum(k[s][f]for f in range(0,1))==g[s]) 


            #CU and server connection           
            x=[]
            for s in range(0,num_slice):
                x.append([])
                for v in range(0,num_rs):
                    x[s].append(m.addVar(vtype=GRB.BINARY, name="x[%d,%d]" % (s,v))) 

            #DU and server connection
            y=[]
            for s in range(0,num_slice):
                y.append([])
                for v in range(0, num_es):
                    y[s].append(m.addVar(vtype=GRB.BINARY, name="y[%d,%d]" % (s,v))) 

            #1-D matrix for used server 
            z = []
            for v in range(0,num_rs):
                z.append(m.addVar(vtype=GRB.BINARY, name="z[%d]" % v))

            w = []
            for v in range(0,num_es):
                w.append(m.addVar(vtype=GRB.BINARY, name="z[%d]" % v))


            #Each slice can select or not select a path with some traffic
            kappa=[]
            for s in range (0, num_slice):
                kappa.append([])
                for p in range (0,path1):
                    kappa[s].append(m.addVar(vtype=GRB.CONTINUOUS, name="kappa[%d,%d]" % (s, p)))

            # #Each slice can select or not select a path
            # psi=[]
            # for s in range (0, S):
            #     psi.append([])
            #     for p in range (0,path1):
            #         psi[s].append(m.addVar(vtype=GRB.BINARY, name="psi[%d,%d]" % (s, p)))


            #********************************************************************==============================
            #Constraints of the model
            #********************************************************************==============================

            #Each function can select only one split if it is admitted.
            for s in range(0,num_slice):
                m.addConstr(sum(k[s][f]for f in range(0,num_split))==g[s]) 

            #Each slice can be connected to one processing node in the regional cloud except split 0.
            for s in range(0,num_slice):
                m.addConstr(sum(x[s][v] for v in range (0,num_rs))== (1- k[s][0])*g[s])  

            #Each slice can be connected to one processing node in the edge cloud.
            for s in range(0,num_slice):
                m.addConstr(sum(y[s][v]*cond[cell[s]][v] for v in range (0,num_es)) == g[s])
            for s in range(0,num_slice):
                m.addConstr(sum(y[s][v] for v in range (0,num_es)) == g[s])

            # Capacity constraint of a node in regional and edge cloud
            for v in range (0,num_rs):
                c1 = LinExpr();
                c1 = 0;
                for s in range (0,num_slice):
                    for f in range(0, num_split):
                        c1=c1+x[s][v]*k[s][f]*slice_cu[s][f]  
                m.addConstr(c1 <= cap_c[v])

            for v in range (0,num_es):
                c1 = LinExpr();
                c1 = 0;
                for s in range (0,num_slice):
                    for f in range(0, num_split):
                        c1=c1+y[s][v]*k[s][f]*slice_du[s][f]  
                m.addConstr(c1 <= cap_d[v])

            # server-used constraint
            for s in range(0,num_slice):
                for v in range(0, num_rs):
                    m.addConstr(z[v]>=x[s][v])

            for s in range(0,num_slice):
                for v in range(0, num_es):
                    m.addConstr(w[v]>=y[s][v])

            # Total Traffic constraints
            for s in range (0, num_slice):
                dus1 = LinExpr();
                dus1=0;
                for f in range (0,fs):
                    dus1 = dus1+ k[s][f]*t[s][f]
                dus2=LinExpr();
                dus2=0;
                for p in range (0,path1):
                    dus2=dus2+ kappa[s][p]
                m.addConstr(dus1 == dus2)

            #Only through the connected path traffic can flow
            for p in range(0, path1):
                for s in range (0, num_slice):
                    m.addConstr(M*path_connect[edge[s]][p]>=kappa[s][p])

            #slice delay constraint
            for s in range (0, num_slice):
                for p in range(0, path1):
                    m.addConstr(M*Q[s][p]>=kappa[s][p])

            #Path delay for functional split
            # for s in range(0,num_slice):
            #     for f in range(0,num_split):
            #         for p in range(0,path1):
            #             psi[s][p]*k[s][f]*path_delay[p]<=split_delay[f]

            # for s in range(0,num_slice):
            #     for p in range(0,path1):
            #         psi[s][p]*M>=kappa[s][p]


            for s in range (0,num_slice):
                tt= LinExpr();
                tt=0;
                for p in range (0,len(p2)):
                    tt=tt+kappa[s][p2[p]]
                m.addConstr(tt<= M * (1-k[s][3]))

            for s in range (0,num_slice):
                tt= LinExpr();
                tt=0;
                for p in range (0,len(p3)):
                    tt=tt+kappa[s][p3[p]]
                m.addConstr(tt<= M * (1-(k[s][2]+k[s][3])))

            #Link traffic constraint:
            for l in range (0, links):
                tt= LinExpr();
                tt=0;
                for p in range (0, path1):
                    for s in range (0, num_slice):
                        tt=tt+ link_path[l][p]*kappa[s][p] 
                m.addConstr(tt<=link_cap[l])


            #Objective value and constrints calculation       
            cost= LinExpr();
            cost= 0;

            obj1= LinExpr();
            obj1= 0;
            obj2= LinExpr();
            obj2= 0;
            obj3= LinExpr();
            obj3= 0;

            for s in range(0, num_slice):
                for f in range (0,num_split):
                    obj1=obj1+k[s][f]*dem[s]*ct[f]            


            for m1 in range(0,num_rs):
                obj2=obj2+z[m1]

            for n in range(0,num_es):
                obj3=obj3+w[n]


            cost= obj1/2040

            m.modelSense = GRB.MAXIMIZE
            m.setObjective(cost,GRB.MAXIMIZE)


            start=time.time()
            m.optimize()
            end=time.time()


            # Print solution
            if(isTest):
                print('\nTOTAL COSTS: %g' % m.objVal)
                print('SOLUTION:')
            else:
                logger.info('\nTOTAL COSTS: %g' % m.objVal)
                logger.info('SOLUTION:')

            curr_split=[[-1 for f in range(0,num_split)]for s in range(0, num_slice)]
            split_select=[-1 for s in range(0, num_slice)]
            for s in range(0, num_slice):
                    for f in range(0, num_split):
                        curr_split[s][f]=k[s][f].x
                        if k[s][f].x>0.9:
                            split_select[s]=f

            curr_CU=[-1 for s in range(0, num_slice)]
            for s in range(0, num_slice):
                for v in range (0,num_rs):
                    if x[s][v].x==1:
                        curr_CU[s]=v

            curr_DU=[-1 for s in range(0, num_slice)]
            for s in range(0, num_slice):
                for v in range (0,num_es):
                    if y[s][v].x==1:
                        curr_DU[s]=v

            accepted=[-1 for s in range(0, num_slice)]
            for s in range(0, num_slice):
                accepted[s]=g[s].x
                
            tot_accept=0
            for s in range(0, num_slice):
                if accepted[s]==1:
                    tot_accept+=1

            cost11= 0;
            central=0;

            obj11= 0;
            obj22= 0;
            obj33= 0;

            for s in range(0, num_slice):
                for f in range (0,num_split):
                    obj11=obj11+k[s][f].x*dem[s]*ct[f]            


            for m1 in range(0,num_rs):
                obj22=obj22+z[m1].x

            for n in range(0,num_es):
                obj33=obj33+w[n].x


            cost11= obj11 /2040 
            central= obj11 /2040

            if(isTest):
                print("Central")
                print(central)
                print("Cost11")
                print(cost11)
                print("Obj11")
                print(obj11)
                print("Obj22")
                print(obj22)
                print("Obj33")
                print(obj33)

                print("Accepted Slices")
                print(accepted)
                
                print("Total accepetd slices")
                print(tot_accept)

                print("Curr CU Placement is")
                print(curr_CU)

                print("Curr DU Placement is")
                print(curr_DU)

                print("Curr split is")
                print(curr_split)

                print ('\n**************Regional server on status**************')
                for v in range (0,num_rs):
                    print(z[v].x)

                print ('\n**************Edge server on status**************')        
                for v in range (0,num_es):
                    print(w[v].x)   

                print ('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')   
                for s in range (0, num_slice):
                    for p in range (0,path1):
                        print ('Slice {} and path {}'.format(s,p))
                        if kappa[s][p].x!=0:
                            print (kappa[s][p].x)
                print("time")
                print (end-start)
                for l in range (0, links):
                    tt=0
                    for p in range (0, path1):
                        for s in range (0, num_slice):
                            tt=tt+ link_path[l][p]*kappa[s][p].x
                    print("remaining link capacity {}".format(link_cap[l]-tt))
                    
            else:
                logger.info(f"Central: {central}")
                logger.info(f"Cost11: {cost11}")
                logger.info(f"Obj11: {obj11}")
                logger.info(f"Obj22: {obj22}")
                logger.info(f"Obj33: {obj33}")
                logger.info(f"Accepted Slices: {accepted}")
                logger.info(f"Total Accepted Slices: {tot_accept}")
                logger.info(f"Curr CU Placement is: {curr_CU}")
                logger.info(f"Curr DU Placement is: {curr_DU}")
                logger.info(f"Curr split is: {curr_split}")

                lst_num_rs = []
                for v in range (0,num_rs):
                    lst_num_rs.append(z[v].x)
                logger.info(f"Regional server on status: {lst_num_rs}")
                
                lst_num_es = []
                for v in range (0,num_es):
                    lst_num_es.append(w[v].x)
                logger.info(f"Edge server on status: {lst_num_es}")
                
                logger.info(f"time: {end-start}")

            cu_energy11=0
            du_energy11=0
            mid_bandwidth11=0


            for s in range(0, num_slice):
                if split_select[s]!=-1:
                    cu_energy11=cu_energy11+slice_cu[s][split_select[s]]
                    du_energy11=du_energy11+slice_du[s][split_select[s]]
                    mid_bandwidth11=mid_bandwidth11+t[s][split_select[s]]
                else:
                    if(isTest):
                        print("Not accepted")
                    else:
                        logger.info("Not accepted")
            
            if(isTest):
                print("cu du and mh amount used are")
                print(cu_energy11)
                print(du_energy11)
                print(mid_bandwidth11)
            else:
                logger.info("cu du and mh amount used are")
                logger.info(cu_energy11)
                logger.info(du_energy11)
                logger.info(mid_bandwidth11)
                logger.info(f"done {dt_idx}")
                logger.info("-"*40)    
                
            lst_central.append(central)
            lst_cost.append(cost11)
            lst_reg_energy.append(cu_energy11)
            lst_edge_energy.append(du_energy11)
            lst_mid_bandwidth.append(mid_bandwidth11)
            lst_turn_on.append(obj22+obj33)
            lst_reg_turn_on.append(obj22)
            lst_edge_turn_on.append(obj33)
            lst_tot_accept.append(tot_accept)
        except Exception as e:
            print(e)
            print(f"Error: tot load = {tl}, data_index = {dt_idx}") 
            if(not isTest):
                logger.info(f"Error: totload = {tl}, data_index = {dt_idx}") 
                logger.info("-"*40)

    if(not isTest):
        logger.info(f"Central :: Mean = {np.mean(lst_central)}, Std Dev = {np.std(lst_central)}")
        logger.info(f"Cost :: Mean = {np.mean(lst_cost)}, Std Dev = {np.std(lst_cost)}")
        logger.info(f"Regional Energy :: Mean = {np.mean(lst_reg_energy)}, Std Dev = {np.std(lst_reg_energy)}")
        logger.info(f"Edge Energy :: Mean = {np.mean(lst_edge_energy)}, Std Dev = {np.std(lst_edge_energy)}")
        logger.info(f"Midhaul Bandwidth :: Mean = {np.mean(lst_mid_bandwidth)}, Std Dev = {np.std(lst_mid_bandwidth)}")      
        logger.info(f"Reg Turn On :: Mean = {np.mean(lst_reg_turn_on)}, Std Dev = {np.std(lst_reg_turn_on)}")      
        logger.info(f"Edge Turn On :: Mean = {np.mean(lst_edge_turn_on)}, Std Dev = {np.std(lst_edge_turn_on)}")    
        logger.info(f"Total accepted :: Mean = {np.mean(lst_tot_accept)}, Std Dev = {np.std(lst_tot_accept)}")    
        logger.info("-"*40)
        logger.info("-"*40)
        
        result_dict[tl] = {}
        result_dict[tl]['mean_central'] = round(np.mean(lst_central),4)
        result_dict[tl]['mean_tot_accept'] = round(np.mean(lst_tot_accept),4)
        result_dict[tl]['mean_cost'] = round(np.mean(lst_cost),4)
        result_dict[tl]['mean_reg_energy'] = round(np.mean(lst_reg_energy),4)
        result_dict[tl]['mean_edge_energy'] = round(np.mean(lst_edge_energy),4)
        result_dict[tl]['mean_midhaul_band'] = round(np.mean(lst_mid_bandwidth),4)
        
        result_dict[tl]['std_central'] = round(np.std(lst_central),4)                                                  
        result_dict[tl]['std_tot_accept'] = round(np.mean(lst_tot_accept),4)    
        result_dict[tl]['std_cost'] = round(np.std(lst_cost),4)
        result_dict[tl]['std_reg_energy'] = round(np.std(lst_reg_energy),4)
        result_dict[tl]['std_edge_energy'] = round(np.std(lst_edge_energy),4)
        result_dict[tl]['std_midhaul_band'] = round(np.std(lst_mid_bandwidth),4)
        
        result_dict[tl]['mean_turn_on'] = round(np.mean(lst_turn_on),4)
        result_dict[tl]['mean_reg_turn_on'] = round(np.mean(lst_reg_turn_on),4)
        result_dict[tl]['mean_edge_turn_on'] = round(np.mean(lst_edge_turn_on),4)
        result_dict[tl]['std_turn_on'] = round(np.std(lst_turn_on),4)
        result_dict[tl]['std_reg_turn_on'] = round(np.std(lst_reg_turn_on),4)
        result_dict[tl]['std_edge_turn_on'] = round(np.std(lst_edge_turn_on),4)
        
        str_log = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(tl, "opt_200", 
                                          
round(np.mean(lst_central),4), round(np.std(lst_central),4),                                                                                   round(np.mean(lst_cost),4), round(np.std(lst_cost),4),
                                          round(np.mean(lst_reg_energy),4), round(np.std(lst_reg_energy),4),
                                          round(np.mean(lst_edge_energy),4), round(np.std(lst_edge_energy),4),
                                          round(np.mean(lst_mid_bandwidth),4), round(np.std(lst_mid_bandwidth),4),
                                          round(np.mean(lst_turn_on),4), round(np.std(lst_turn_on),4),
                                          round(np.mean(lst_reg_turn_on),4), round(np.std(lst_reg_turn_on),4),                                                                         round(np.mean(lst_edge_turn_on),4), round(np.std(lst_edge_turn_on),4))
        result_file2.write(str_log)

if(not isTest):
    result_file = open(out_file, "w")
    result_file.write(json.dumps(result_dict, indent=4, sort_keys=True))
    result_file.close()
    result_file2.close()
               
print("done")
