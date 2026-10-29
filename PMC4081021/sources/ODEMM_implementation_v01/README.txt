{\rtf1\ansi\ansicpg1252\cocoartf1265\cocoasubrtf190
{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
\paperw11905\paperh16837\margl1440\margr1440\vieww10800\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural

\f0\fs24 \cf0 %%%%%%%%%%%%%%%%%%%%%%%%%%%%\
%%                                                                             %%\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 %%    Tool for ODE constrained mixture modelling    %%\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 %%                                                                             %%\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 %%%%%%%%%%%%%%%%%%%%%%%%%%%%\
\
1) Description:\
\
This is a collection of MATLAB algorithm for ODE constrained\
mixture modelling and provides an implementation of the examples\
presented in the manuscript: \
\
[1] J. Hasenauer, C. Andres, Tim Hucho and F. Theis.\
     ODE constrained mixture modelling: A method for\
     unraveling subpopulation structures and dynamics\
     submitted to PLoS Computational Biology\
\
Note: The software is not intended as a complete toolbox, but should\
only provide a first simple, easily extendable implementation of the\
methods.\
\
\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 %%%%%%%%%%%%%%%%%%%%%%%%%%%%\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 \
2) Installation:\
\
To employ the functionality of the tools include the place were it is\
located into your MATLAB path. Make sure that you have the MATLAB\
statistical toolbox and MATLAB optimisation toolbox are available.\
Furthermore the SUNDIALS package CVodes and SUNDIALSTB\
have to be installed. These toolboxes are used for an efficient simulation.\
\
\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 %%%%%%%%%%%%%%%%%%%%%%%%%%%%\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 \
3) Content and functionality:\
\
For an illustration of the functionality we refer to the example\
     ./conversion_reaction/scenario_1___low_variability\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0      ./conversion_reaction/scenario_2___high_variability\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0      ./NGF_induced_Erk_phosphorylation/pathway_model_A\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0      ./NGF_induced_Erk_phosphorylation/pathway_model_B\
     ./NGF_induced_Erk_phosphorylation/pathway_model_C\
\
These example also contain the results presented in the paper and \
routines which generate the respective plots:\
     plots_for_paper.m\
     plots_for_paper__model_comparison.m\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 \
\
Furthermore, the measurement data for the NGF signalling\
pathway are provided in \
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0      ./NGF_induced_Erk_phosphorylation/pathway_model_A/project/data\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 For a consistent way to load these data we refer to the m-file\
fitting__2logn_median_TrkA0.m in the subfolder\
    ./NGF_induced_Erk_phosphorylation/pathway_model_A\
\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 %%%%%%%%%%%%%%%%%%%%%%%%%%%%\
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 \
4) Contacts:\
\
This tool has been developed by Jan Hasenauer. If you need support or\
if you have any recommendations how the tools can be improved, please\
do not hesitate to contact me:\
\
Jan Hasenauer\
Institute of Computational Biology\
Helmholtz Center Munich\
Email: jan.hasenauer@helmholtz-muenchen.de\
\
}