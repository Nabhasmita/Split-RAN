# Split-RAN

Problem Statement: Given the data rate, delay requirements of RAN slices and underlying network charecteristics, the codes select functional split, baseband function placement and traffic routing of RAN slices so that the degree of centralization is maximized and cost of active nodes is minimized.

create_data.py: This file is used to create input data which contain slice datarate, origin and delay requirements.

To run the other .py codes GUROBI with Python interface needs to be used.
  Install Gurobi and gather a Liscene
  
The optimization results collected for different strategies using the following codes.
opt.py: To get the solution of the optimization model of Split-RAN
fms.py: To get the solution of when only the highest split is used
nt.py: To get the solution of when no traffic splitting is used
optnc.py: To get the solution of the optimization model without consolidation of nodes
fmsnt.py: To get the solution of when only the highest split is used with no traffic splitting

#



