# Split-RAN

Given the data rate, delay requirements of RAN slices and underlying network characteristics, the codes select functional split, baseband function placement and traffic routing of RAN slices so that the degree of centralization is maximized and cost of active nodes is minimized.

create_data.py: This file is used to create input data which contain slice datarate, origin and delay requirements.

To run the other .py codes GUROBI with Python interface needs to be used.
  Install Gurobi and obtain a License
  
The optimization results collected for different strategies using the following codes.
- opt.py: Generates solution of Split-RAN problem
- fms.py: Generates solution when only the highest split is used for slices with traffic splitting
- nt.py: Generates solution of Split-RAN problem without traffic splitting
- optnc.py: Generates solution of Split-RAN problem without server consolidation
- fmsnt.py: Generates solution when only the highest split is used for slices with no traffic splitting


