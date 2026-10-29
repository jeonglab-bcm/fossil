function ExpCondition = load_NGF_dose_response
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

%% load data: sheet - Dose response stimulus for NGF

D = csvread('project/data/Dose response NGF.csv',1,0);
% stimulus and type of data
str_stim = 'NGF';
str_type = 'dose_response';


% number of stimuli
n_c = 6;
% number of experiments
n_e = 5;
% considered experiments
I_exp = 1:n_e;

% label data
ExpCondition(1).name = 'no stimulus';
ExpCondition(1).label = '0';
ExpCondition(1).labelname = 'NGF [pM]';

ExpCondition(2).name = '1 pM NGF';
ExpCondition(2).label = '10^0';
ExpCondition(2).labelname = 'NGF [pM]';

ExpCondition(3).name = '10 pM NGF';
ExpCondition(3).label = '10^1';
ExpCondition(3).labelname = 'NGF [pM]';

ExpCondition(4).name = '100 pM NGF';
ExpCondition(4).label = '10^2';
ExpCondition(4).labelname = 'NGF [pM]';

ExpCondition(5).name = '1 nM NGF';
ExpCondition(5).label = '10^3';
ExpCondition(5).labelname = 'NGF [pM]';

ExpCondition(6).name = '10 nM NGF';
ExpCondition(6).label = '10^4';
ExpCondition(6).labelname = 'NGF [pM]';

% restore data
for c = 1:n_c
    % index set of all measurements for stimulus s
    ind_c = find(D(:,c)>0);
    % initialization
    j = 1;
    % loop over experiments
    for e = I_exp
        % Additional information
        ExpCondition(c).experiment(j).name = sprintf('experiment %d',e);
        ExpCondition(c).experiment(j).measurands = {'Erk-P','size'};
        % index set of experiment e
        ind_e = find(D(:,end)==e);
        % index set of experiment e with stimulus s
        ind_ec = intersect(ind_e,ind_c);
        % fluorescence and size data
        ExpCondition(c).experiment(j).data = D(ind_ec,c+[0,n_c]);
        % update
        j = j+1;
    end
end

