% optimizeMixtureModel calculates the maximum a posterior estimate of the
%   parameters of a user-supplied posterior function. Therefore, a 
%   multi-start local optimization is used. The starting points are 
%   computed via a using defined function.
%
% USAGE:
% ======
% [...] = optimizeMultiStart(parameters,logLikelihood)
% [...] = optimizeMultiStart(parameters,logLikelihood,options)
% [parameters,fh] = optimizeMultiStart(...)
%
% INPUTS:
% =======
% parameters ... parameter struct containing at least:
%   .number ... number of parameter
%   .guess ... initial guess of parameter
%   .min ... lower bound for parameter values       
%   .max ... upper bound for parameter values       
%   .name = {'name1',...} ... names of the parameters       
%   .init_fun ... function to draw starting points for local
%   	optimization. The function has to have the input structure
%           .init_fun(theta_0,theta_min,theta_max)
% logPosterior ... log-posterior of model as function of the parameters.
%   This log-posterior function must allow for a second input. This
%   input is an option, which determines whether the value and the
%   gradient of the positive (.sign = 'negative') or the negative 
%   (.sign = 'positive') log-likelihood is provided. Furthermore, an 
%   index set may be provided which determines the index of the 
%   parameters with respect to which the gradient is evaluated
%   (.grad_ind).
% options ... options of algorithm
%   .mode
%   .fmincon ... options for local optimization
%   .n_starts ... number of starts of the local optimization (default = 20)
%   .plot ... plot the results during the computation (default = 'true').
%
% Outputs:
% ========
% parameters ... updated parameter object containing:
%   .MS ... information about multi-start optimization
%       .MAP ... information about different a posteriori estimates:
%           .par ... MAP
%           .logPost ... log-posterior at MAP
%       .MAP_list ... list of different optimization results:
%           .par ... MAP
%           .logPost ... log-posterior at MAP
%               (columns are different estimation runs.
%           .nonzero ... ratio of successive runs defined as runs
%               which optimization converged.
%
% 2012/05/31 Jan Hasenauer
% 2012/07/09 Jan Hasenauer
% 2012/07/11 Jan Hasenauer

% function [parameters,fh] = optimizeMultiStart(parameters,logLikelihood,options)
function [parameters,fh] = optimizeMultiStart(varargin)

%% CHECK AND ASSIGN INPUTS
if nargin >= 2
    parameters = varargin{1};
    logPosterior = varargin{2};
else
    error('optimizeMixtureModel requires at least two inputs.')
end
% Check parameters:
if ~isfield(parameters,'min') || ~isfield(parameters,'max')
    error('Algorithm requires lower and upper bounds');
else
    parameters.min = parameters.min(:);
    parameters.max = parameters.max(:);
end
if length(parameters.min) ~= length(parameters.max)
	error('Dimension of parameters.min and parameters.max does not agree.');
else
    if max(parameters.min >= parameters.max)
        error('There exists at least one i with parameters.min(i) >= parameters.max(i).');
    end
end
if ~isfield(parameters,'number')
    parameters.number = length(parameters.min);
else
    if parameters.number ~= length(parameters.min)
        error('Dimension mismatch: parameters.number ~= length(parameters.min).');
    end
end
if isfield(parameters,'guess')
    parameters.guess = parameters.guess(:);
    if length(parameters.guess) ~= length(parameters.max)
        error('Dimension of parameters.guess does not agree with dimesion of parameters.min and .max.');
    end
end
constr.A = [];
constr.b = [];
constr.Aeq = [];
constr.beq = [];
if isfield(parameters,'constraints')
    parameters.constraints = setdefault(parameters.constraints,constr);
else
    parameters.constraints = constr;
end

% Check and assign options
options.fmincon = optimset('algorithm','interior-point',...
                           'display','off',...
                           'GradObj','on');
options.fmincon_con = optimset('algorithm','active-set',...
                           'display','off',...
                           'GradObj','off');
options.n_starts = 20;
options.proposal = 'latin hypercube';
options.plot = 'true';
options.mode = 'normal'; % 'silent';
options.logPost_options.sign = 'negative';
options.logPost_options.grad_ind = [1:parameters.number]';
options.fh = [];
if nargin == 3
    options = setdefault(varargin{3},options);
end
if ~isfield(parameters,'init_fun') || ~isfield(parameters,'guess')
    options.proposal = 'latin hypercube';
end

%% INITIALIZATION OF LISTS
parameters.MS.MAP.par = [];
parameters.MS.MAP.logPost = [];
parameters.MS.MAP_list.par = [];
parameters.MS.MAP_list.logPost = [];
parameters.MS.MAP_list.gradient = [];
parameters.MS.MAP_list.hessian = [];

%% OPEN FIGURE
if strcmp(options.plot,'true')
    if isempty(options.fh)
        fh = figure;
    else
        fh = figure(options.fh);
    end
else
    fh = [];
    switch options.mode
        case 'normal'
            disp(' ');
            disp(['Optimization:']);
            disp(['=============']);
        case 'silent'
            % no output
        otherwise
            error('This option is not available.');
    end
end

%% INITIALIZATION
if options.n_starts >= 1
    if strcmp(options.proposal,'latin hypercube')
        % Sampling from latin hypercube
        Theta_init = bsxfun(@plus,parameters.min,bsxfun(@times,parameters.max - parameters.min,lhsdesign(options.n_starts,parameters.number,'smooth','off')'));
        if isfield(parameters,'guess')
            Theta_init = [parameters.guess,Theta_init];
        end
    else
        % Sampling from user-supplied function
        Theta_init = parameters.init_fun(parameters.guess,parameters.min,parameters.max,options.n_starts);
        Theta_init = [parameters.guess,Theta_init];
    end
else
    Theta_init = parameters.guess;
end
% Set default value
parameters.MS.MAP.logPost = -logPosterior(Theta_init(:,1),options.logPost_options);

%% OPTIMIZATION USING LOCAL OPTIMIZATION FROM MULTIPLE STARTING POINTS
% Loop: Optimization starts
for i = 1:size(Theta_init,2)
%     % Evaluate inequality constraint at starting point
%     if ~isempty(parameters.constraints.A)
%         con = min(parameters.constraints.A*Theta_init(:,i) <= parameters.constraints.b);
%     else
%         con = 1;
%     end
    % Calculation of feasible initial condition
    if ~isempty(parameters.constraints.A)
        if max(parameters.constraints.A  *Theta_init(:,i)  > parameters.constraints.b  )
            ind_in = find(sum(parameters.constraints.A   ~= 0,1));
            ind_eq = find(sum(parameters.constraints.Aeq ~= 0,1));
            ind = union(ind_in,ind_eq);
            
            if ~isempty(parameters.constraints.A)
                A = parameters.constraints.A(:,ind);
                b = parameters.constraints.b - 10^-10;
            else
                A = [];
                b = [];
            end
            if ~isempty(parameters.constraints.Aeq)
                Aeq = parameters.constraints.Aeq(:,ind);
                beq = parameters.constraints.beq;
            else
                Aeq = [];
                beq = [];
            end
            
            Theta_init(ind,i) = fmincon(@(theta) 0,...  % dummi
                                   Theta_init(ind,i),...    % initial parameter
                                   A  ,b  ,... % linear inequality constraints
                                   Aeq,beq,... % linear equality constraints
                                   parameters.min(ind),...     % lower bound
                                   parameters.max(ind),...     % upper bound
                                   [],options.fmincon_con);
        end
    end
    % Optimizations
    try
        if (logPosterior(Theta_init(:,i),options.logPost_options) < inf)
            % Call fmincon to maximize log-likelihood
            [theta,J_opt,~,~,~,gradient,hessian] = ...
                fmincon(@(theta) logPosterior(theta,options.logPost_options),...  % negative log-likelihood function
                                    Theta_init(:,i),...    % initial parameter
                                    parameters.constraints.A  ,parameters.constraints.b  ,... % linear inequality constraints
                                    parameters.constraints.Aeq,parameters.constraints.beq,... % linear equality constraints
                                    parameters.min,...     % lower bound
                                    parameters.max,...     % upper bound
                                    [],options.fmincon);   % options
            % Store estimates
            parameters.MS.MAP_list.logPost(end+1) = -J_opt;
            parameters.MS.MAP_list.par(:,end+1) = theta;
            parameters.MS.MAP_list.gradient(:,end+1) = gradient;
            if strcmp(options.fmincon.Hessian,'user-supplied')
                [~,~,hessian] = logPosterior(theta,options.logPost_options);
            end
            parameters.MS.MAP_list.hessian(:,:,end+1) = full(hessian);
            
            % Sort estimates
            [parameters.MS.MAP_list.logPost,ind] = sort(parameters.MS.MAP_list.logPost,2,'descend');
            parameters.MS.MAP.logPost  = parameters.MS.MAP_list.logPost(1);
            parameters.MS.MAP_list.par = parameters.MS.MAP_list.par(:,ind);
            parameters.MS.MAP_list.gradient = parameters.MS.MAP_list.gradient(:,ind);
            parameters.MS.MAP_list.hessian  = parameters.MS.MAP_list.hessian(:,:,ind);
            parameters.MS.MAP.par = parameters.MS.MAP_list.par(:,1);
            parameters.MS.MAP.gradient = parameters.MS.MAP_list.gradient(:,1);
            parameters.MS.MAP.hessian = parameters.MS.MAP_list.hessian(:,:,1);
            
            % Update plot
            if strcmp(options.plot,'true')
                fh = plotMS(parameters,fh);
            else
                switch options.mode
                    case 'normal'
                        disp(['  ' num2str(i,'%d') '/' num2str(options.n_starts,'%d')]);
                end
            end
        else
            disp('Posterior probability is zero at initial point.');
        end
        
    catch error_msg
        disp(['Optimization failed because: ' error_msg.message]);
    end
end

%% ASSIGN STATISTICS AND FINISH
parameters.MS.MAP_list.nonzero = size(parameters.MS.MAP_list.par,2)/size(Theta_init,2);

% Output
switch options.mode
    case 'normal'
        disp('-> Multi-start optimization FINISHED.');
end


