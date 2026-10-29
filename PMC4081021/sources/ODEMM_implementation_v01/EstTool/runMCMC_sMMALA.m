% runMCMC_sMMALA samples the user provided log-posterior with parameter
%   bounds and starting values as provided in parameters
%
% USAGE:
% ======
% parameters = runMCMC_sMMALA(parameters,logPosterior)
% parameters = runMCMC_sMMALA(parameters,logPosterior,options)
%
% INPUTS:
% =======
% parameters ... parameter struct containing at least:
%     .number ... number of parameter
%     .guess ... initial guess of parameter
%     .min ... lower bound for parameter values       
%     .max ... upper bound for parameter values       
% logPosterior ... function handle providing for a given parameter theta
%     1) the log-posterior (first output),
%     2) the gradient of the log-posterior (second output), and
%     3) the local Fisher information matrix of the log-posterior (third 
%         output). Instead of the Fisher information matrix also a
%         positive semi-definite approximation of the Hessian can be
%         supplied.
% options ... options of sampling
% 
%
% INPUTS:


% function parameters = runMCMC_sMMALA(parameters,logPosterior,options)
function parameters = runMCMC_sMMALA(varargin)

%% CHECK AND ASSIGN INPUTS
if nargin >= 2
    parameters = varargin{1};
    logPosterior = varargin{2};
else
    error('runMCMC_sMMALA requires at least two input arguments.');
end

% Set and assign defauls
options.sample_size = 1000;
options.burnin = 100;
options.thinning = 1;
options.Sigma_scaling = 1;
options.mu_step_scaling = 1;
if nargin == 3
    options = setdefault(varargin{3},options);
end

%% GENERAL INITIALIZATION
lb = parameters.min;
ub = parameters.max;
parameters.chain      = nan(length(lb),length(1:options.thinning:options.sample_size));
parameters.chain_logP = nan(1         ,length(1:options.thinning:options.sample_size));
j = 1;
acc = 0;

%% INITIALIZATION OF SAMPLING
% Starting point
try
    theta = parameters.ml;
catch
    theta = parameters.guess;
end
% Sampling
[logP,grad,F] = logPosterior(theta);
if (logP == nan) || (logP == -inf)
    error('log-posterior undefined at initial point.');
end
[mu,Sigma] = sMMALA(theta,grad,F,lb,ub,options);

%% CHECK FOR REGULARITY
s = diag(Sigma);
if max(s < 1e-5)
    warning(['The Fisher information matrix is close to singular.' ...
             'The sMMALA is in this case not appropriate.']);
end

%% INITIALIZE WAITBAR
h = waitbar(0,['MCMC sampling completed to 0 % (acc = 0 %)']);

%% GENERATE MARKOV CHAIN
i  = 1;
i_ = 0;
while i <= (options.sample_size + options.burnin)

    if mod(i,100) == 0
        % Report current estimate in the waitbar's message field
        waitbar(i/(options.sample_size + options.burnin),h,...
            ['MCMC sampling completed to ' num2str(100*i/(options.sample_size + options.burnin),'%.2f')...
             ' % (acc = ' num2str(100*acc/i,'%.2f') ' % )']);
    end
    
% Propose new parameter vector
theta_i = mvnrnd(mu,Sigma)';

% Check bounds
if (sum(theta_i < lb) + sum(theta_i>ub) == 0)
    try
        % Increase counter
        i = i + 1;
        % Compute log-likelihood and sensitivity
        [logP_i,grad_i,F_i] = logPosterior(theta_i);
        % Update mu and Sigma of proposal
        [mu_i,Sigma_i] = sMMALA(theta_i,grad_i,F_i,lb,ub,options);
        mu_i = max(min(mu_i,ub),lb);
        Sigma_i = options.Sigma_scaling * Sigma_i;
        % Transition probabilities
        log_p_forward  = logmvnpdf(theta_i,mu  ,Sigma  );
        log_p_backward = logmvnpdf(theta  ,mu_i,Sigma_i);
        % Acceptance probability
        pacc = exp(logP_i - logP + log_p_backward - log_p_forward);
    catch
        warning('Evaluation of objective function failed.');
        pacc = 0;
    end
else
    pacc = 0;
end

% Accept or reject
if rand <= pacc
    theta   = theta_i;
    logP    = logP_i;
    mu      = mu_i;
    Sigma   = Sigma_i;
    acc     = acc + 1;
end

% Store
if (mod(i,options.thinning) == 0) && (i > options.burnin) && (i ~= i_)
    parameters.chain(:,j)      = theta;
    parameters.chain_logP(:,j) = logP;
    j = j + 1;
    i_ = i;
end

end

%% CLOSE WAITBAR
close(h);


end

%% FUNCTION TO COMPUTE MEAN AND COVARIANCE OF PROPOSAL
function [mu,Sigma] = sMMALA(theta,grad,F,lb,ub,options)

% E = eig(F);
% if (max(real(E)) / min(real(E))) > 1e3
%     F = F + diag(10^2*(ub - lb).^-2);
% end

Sigma = options.Sigma_scaling*inv(F);

dmu = F\(grad);
dmu = options.mu_step_scaling * (dmu / norm(dmu,2)^2);
mu    = theta + dmu;

mu = max(min(mu,ub),lb);
% mu    = theta + inv(Sigma)*grad;

end