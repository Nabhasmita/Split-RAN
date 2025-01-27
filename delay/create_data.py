import numpy as np
import random
import json
import os
random.seed(0)
np.random.seed(0) 

urllc_percent=[0.1,0.2,0.3,0.4,0.5]
num_slice = 30
data_len = 50
max_cell = 9
data_path = "data"

if(os.path.isdir(data_path)):
    print("Data path exists.")
    exit(0)
else:
    os.mkdir(data_path)
    print(f"Data path created.")
    
tl=350

for u in urllc_percent:
    data = []
    embb_ratio=0.75-u
    mmtc_ratio=0.25
    urllc_ratio=u
    for dt in range (0, data_len):
        lst = []
        for i in range(0,10):
            d=random.randint(tl-10,tl+10)
            v1=d*embb_ratio
            v2=d*mmtc_ratio
            v3=d*urllc_ratio
            lst.append(v1)
            lst.append(v2)
            lst.append(v3)
        print("Here is")
        print(lst)

        cell=[0,0,0,3,3,3,6,6,6,9,9,9,12,12,12,15,15,15,18,18,18,21,21,21,24,24,24,27,27,27]
        edge=[0,0,0,1,1,1,2,2,2,3,3,3,4,4,4,5,5,5,6,6,6,7,7,7,8,8,8,9,9,9]
        stype=[0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2]
        delay=[10,10,1,10,10,1,10,10,1,10,10,1,10,10,1,10,10,1,10,10,1,10,10,1,10,10,1,10,10,1]

        dct = {}
        dct["dem"] = lst
        dct["stype"] = stype
        dct["delay" ] = delay
        dct["cell"] = cell
        dct["edge"] = edge
        data.append(dct)

        file_name = os.path.join(data_path, f"data_{u}.json")
        with open(file_name, 'w') as f:
            json.dump(data, f)

print("Data Created")