% computeMCMCsample_DRAM performs adaptive MCMC sampling of the posterior
%   distribution using the DRAM toolbox. The main porpuse of this routine
%   is to provide a nice interface.  
%
% USAGE:
% ======
% [...] = computeMCMCsample_DRAM(parameters,logPosterior)
% [...] = computeMCMCsample_DRAM(parameters,logPosterior,options)
% [parameters] = computeMCMCsample_DRAM(...)
% [parameters,fh_logPost_trace] = computeMCMCsample_DRAM(...)
% [parameters,fh_logPost_trace,fh_par_trace] = computeMCMCsample_DRAM(...)
% [parameters,fh_logPost_trace,fh_par_trace,fh_par_dis] = computeMCMCsample_DRAM(...)
%
% INPUTS:
% =======
% parameters ... parameter struct containing at least:
%   .number ... number of parameter
%   .ml .. maximum likelihood estimate
%   .min ... lower bound for parameter values       
%   .max ... upper bound for parameter values       
% logPosterior ... log-posterior of model as function of the parameters.
% options ... options of algorithm
%   .nsimu_warmup ... length of MCMC warm-up run (default = 1e4).
%   .nsimu_run ... length of MCMC run(default = 5e4).
%   .algorithm ... MCMC sampling scheme (default = 'dram')
%   .qcov ... initial covariance matrix for MCMC sampling
%       (default = 0.001*eye(parameters.number)).
%   .adaptint ... number of function evaluations between adaptation of
%       the MCMC transition kernel (default = 20*parameters.number).
%   .plot ... visualization of the results after the computation (default = 'true').
%   .plot_options ... plot options:
%       .interval ... method uses to determine plot bounds (default = 'dynamic').
%       .hold_on ... conserve of current plot content (default = 'false').
%   .fh_logPost_trace ... figure handle for log-posterior trace plot.
%   .fh_par_trace ... figure handle for parameter trace plots.
%   .fh_par_dis ... figure handle for the parameter distribution trace plot.
%
% Outputs:
% ========
% parameters ... updated parameter object containing:
%   .MCMC ... informations about MCMC-sampling.
%       .sample ... MCMC sample:
%           .logPost ... log-posterior function along chain
%           .par  ... parameters along chain
%       .MAP ... MCMC-based MAP estimate:
%           .logPost ... log-posterior function of MAP
%           .par  ... MAP
% fh_logPost_trace .. figure handle for log-posterior trace
% fh_par_trace .. figure handle for parameter traces
% fh_par_dis .. figure handle for parameter distribution
%
% 2012/07/11 Jan Hasenauer

% function [parameters,fh_logPost_trace,fh_par_trace,fh_par_dis] = computeMCMCsample_DRAM(parameters,logLikelihood,options)
function [parameters,fh_logPost_trace,fh_par_trace,fh_par_dis] = computeMCMCsample_DRAM(varargin)


%% CHECK AND ASSIGN INPUTS
if nargin >= 2
    parameters = varargin{1};
    logPosterior = varargin{2};
else
    error('optimizeMixtureModel requires at least three inputs.')
end

% Set options
options.plot = 'true';
options.plot_options.interval = 'dynamic';
options.plot_options.hold_on = 'false';
options.fh_logPost_trace = [];
options.fh_par_trace = [];
options.fh_par_dis = [];
options.nsimu_warmup = 1e4;
options.nsimu_run    = 5e4;
options.algorithm    = 'dram';
options.qcov         = 0.001*eye(parameters.number);
options.adaptint     = 20*parameters.number;
if nargin == 3
    options = setdefault(varargin{3},options);
end

%% OPEN FIGURE
if strcmp(options.plot,'true')
    % logL trace
    if isempty(options.fh_logPost_trace)
        fh_logPost_trace = figure;
    else
        fh_logPost_trace = figure(options.fh_logPost_trace);
    end
    % parameter traces
    if isempty(options.fh_par_trace)
        fh_par_trace = figure;
    else
        fh_par_trace = figure(options.fh_par_trace);
    end
    % parameter distribution
    if isempty(options.fh_par_dis)
        fh_par_dis = figure;
    else
        fh_par_dis = figure(options.fh_par_dis);
    end
end

%% INITIALIZATION
for i = 1:parameters.number
    params{i} = {parameters.name{i},parameters.MS.MAP.par(i),parameters.min(i),parameters.max(i)};
end

%% SAMPLING MODEL
model.ssfun = @(theta,dummi) -2*logPosterior(theta);
model.sigma2 = 1;
model.N = 1;

%% OPTIONS MCMC SAMPLING
% Options
options_dram.method      = options.algorithm; % adaptation method (mh,am,dr,dram)
options_dram.qcov        = options.qcov;      % proposal covariance
options_dram.adaptint    = options.adaptint;  % adaptation interval
options_dram.printint    = 0; % how often to show info on acceptance ratios
options_dram.verbosity   = 0;  % how much to show output in Matlab window
options_dram.waitbar     = 1;  % show garphical waitbar
options_dram.updatesigma = 0;  % update error variance
options_dram.stats       = 0;  % save extra statistics in results

%% RUN MCMC SAMPLING
% Warm-up
options_dram.nsimu = options.nsimu_warmup; % # simulations
[results] = mcmcrun(model,[],params,options_dram);
% Sampling
options_dram.nsimu = options.nsimu_run; % # simulations
[results,Theta,~,Obj] = mcmcrun(model,[],params,options_dram,results);
% Reassignment
parameters.MCMC.sample.logPost = -0.5*Obj;
parameters.MCMC.sample.par = Theta';
[parameters.MCMC.MAP.logPost,ind_map] = max(-0.5*Obj);
parameters.MCMC.MAP.par = Theta(ind_map,:)';

%% PLOT RESULTS OF MCMC RUN
if strcmp(options.plot,'true')
    % Course of individual parameters
    figure(fh_logPost_trace);
    mcmcplot(parameters.MCMC.sample.par',[],results,'chainpanel');
    
    % Course of log-likelihood
    figure(fh_par_trace);
    semilogy(1:length(parameters.MCMC.sample.logPost),parameters.MCMC.sample.logPost,'b.');
    xlabel('sample member');
    ylabel('log-likelihood');

    % Parameter histogram
    plotMCMC(parameters,fh_par_dis); hold on;

    % Chain statistics
    chainstats(parameters.MCMC.sample.par',results);
end
