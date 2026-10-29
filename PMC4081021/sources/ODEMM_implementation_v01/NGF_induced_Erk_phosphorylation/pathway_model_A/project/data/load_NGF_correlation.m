function ExpCondition = load_NGF_correlation
% This file creats the data structure used for the following analysis.
% The stucture is as follows:
%
% MeasurementData(i)
%   .name = 'string specifying the experimental consitions'
%   .label = 'label used in plots for ticks'
%   .labelname = 'label used in plots as label'
%   .experiment(j)
%      .name = 'string specifying the experiment'
%      .measurands = {'name of measurand 1','name of measurand 2',
%                            ...,'name of measurand m'}
%      .data = n_D x m matrix
%         (One row represents one observed cell with the
%          data in the order of the measurands. The different
%          rows provide measurement data for different cells.)
%
% The whole routine strongle depends on the way the data
% are provided. The struct 'MeasurementData' on the other hand
% should have exactly wthis form to allow the usag of other
% routines in the following.

%% load data: sheet - Dose response stimulus for GDNF

D = csvread('project/data/pErk_Erk_correlation_reduced.csv',1,0);
%D = csvread('pErk_Erk_correlation_reduced.csv',1,0);
% stimulus and type of data
str_stim = 'NGF';
str_type = 'kinetic';


% number of time points
n_c = 2;
% number of experiments
n_e = 3;
% considered experiments
I_exp = 1:n_e;

% label data
ExpCondition(1).name = 'no stimulus';
ExpCondition(1).label = '0';
ExpCondition(1).labelname = 'time [min] after stimulus with 1 nM NGF';

ExpCondition(2).name = '30 min after NGF stimulation with 1 nM';
ExpCondition(2).label = '30 min after NGF stimulation with 1 nM';
ExpCondition(2).labelname = '30 min after NGF stimulation with 1 nM';

% restore data
for c = 1:n_c
    % index set of all measurements for stimulus s
    ind_c = find(D(:,2*c)>0);
    % initialization
    j = 1;
    % loop over experiments
    for e = I_exp
        % Additional information
        ExpCondition(c).experiment(j).name = sprintf('experiment %d',e);
        ExpCondition(c).experiment(j).measurands = {'Erk','Erk-P','size'};
        % index set of experiment e
        ind_e = find(D(:,end)==e);
        % index set of experiment e with stimulus s
        ind_ec = intersect(ind_e,ind_c);
        % fluorescence and size data
        ExpCondition(c).experiment(j).data = D(ind_ec,3*(c-1)+[1:3]);
        % update
        j = j+1;
    end
end


