% computeProfiles calculates the profiles of a user-supplied function,
%   starting from the maximum a posteriori estimate.
%
% USAGE:
% ======
% [...] = computeProfiles(parameters,logPosterior)
% [...] = computeProfiles(parameters,logPosterior,options)
% [parameters,fh] = computeProfiles(...)
%
% INPUTS:
% =======
% parameters ... parameter struct       
% logPosterior ... log-posterior of model as function of the parameters.
%       This log-posterior function must allow for a second input. This
%       input is an option, which determines whether the value and the
%       gradient of the positive (.sign = 'negative') or the negative 
%       (.sign = 'positive') log-posterior is provided. Furthermore, an 
%       index set may be provided which determines the index of the 
%       parameters with respect to which the gradient is evaluated
%       (.grad_ind).
% options ... options of algorithm
%     .fmincon ... options for local optimization
%     .intervals ... number of intervals in which profile is 
%         decomposed (default = 30).
%     .plot ... plot the results during the computation (default = 'true').
%     .fh ... figure handle. If no figure handle is provided, a new figure
%           is created.
%     .parameter_index ... index of the parameters for which the profile
%           is calculated (default = 1:parameters.number).
%     .P.min ... lower bound for profiling parameters, having same
%           dimension as the parameter vector (default = parameters.min).
%     .P.max ... lower bound for profiling parameters, having same
%           dimension as the parameter vector (default = parameters.max).
%     .R_min ... minimal ratio down to which the profile is calculated 
%           (default = 0.03).
%     .dR_max ... maximul relative decrease of ratio allowed
%           for two adjacent points in the profile (default = 0.15).
%
% Outputs:
% ========
% parameters ... updated parameter object containing:
%     .P(i) ... profile for i-th parameter
%         .par ... MAP along profile
%         .logPost ... maximum log-posterior along profile
%         .R ... ratio
% fh .. figure handle
%
% 2012/05/16 Jan Hasenauer

% function [parameters,fh] = computeProfiles(parameters,logPosterior,options)
function [parameters,fh] = computeProfiles(varargin)

%% CHECK AND ASSIGN INPUTS
if nargin >= 2
    parameters = varargin{1};
    logPosterior = varargin{2};
else
    error('optimizeMixtureModel requires at least three inputs.')
end

% Check and assign options
%options.fmincon = optimset('algorithm','trust-region-reflective',...
options.fmincon = optimset('algorithm','interior-point',...
                           'display','off',...
                           'GradObj','on',...
                           'MaxIter',2000,...
                           'MaxFunEvals',300*parameters.number);
options.intervals = 30;
options.plot = 'true';
options.plot_options.interval = 'dynamic';
options.plot_options.mark_constraint = 'false';
options.plot_options.hold_on = 'false';
options.fh = [];
options.parameter_index = 1:parameters.number;
options.P.min = parameters.min;
options.P.max = parameters.max;
options.R_min = 0.03;
options.dR_max = 0.12;
options.update_mode = 'multi-dimensional'; %'one-dimensional';
options.P_next_step.min = 1e-6;
options.P_next_step.max = 1e2;
options.reoptimize = 'false'; %'true';
options.profile = 'true'; %'false'; 
if nargin == 3
    options = setdefault(varargin{3},options);
end

%% OPEN FIGURE
if strcmp(options.plot,'true')
    if isempty(options.fh)
        fh = figure;
    else
        fh = figure(options.fh);
    end
else
    fh = [];
    disp(' ');
    disp(['Profile likelihood computation:']);
    disp(['===============================']);
end

%% COMPUTE PROFILE
if strcmp(options.profile,'true')
% Loop: Parameters
for i = options.parameter_index
    % Initialize profile
    parameters.P(i).par     = parameters.MS.MAP.par;
    parameters.P(i).logPost = parameters.MS.MAP.logPost;
    parameters.P(i).R       = 1;
end

% Loop: Parameters
for i = options.parameter_index
    disp('');
    % Index set
    I1 = [1:i-1]';
    I2 = [i+1:parameters.number]';
    I  = [I1;I2];
    % Likelihood function option
    options.logPost_options.grad_ind = I(:);
    options.logPost_options.sign = 'negative';
            
    %% COMPUTE OPTIMUM FOR IN-/DECREASING THETA
    for s = [-1,1]
        % Sarting point
        theta  = parameters.MS.MAP.par;
        logPost = parameters.MS.MAP.logPost;
        % Lower and upper bounds for profiles
        theta_min = [parameters.min(I1);options.P.min(i);parameters.min(I2)];
        theta_max = [parameters.max(I1);options.P.max(i);parameters.max(I2)];
        % Initialize direction
        dtheta = zeros(parameters.number,1);
        dtheta(i) = s*(parameters.max(i) - parameters.min(i))/options.intervals;
        % Loop: Points of profile with theta_i > theta_i_ml
        while (options.P.min(i) < theta(i)) && (theta(i) < options.P.max(i)) && ...
              (logPost >= (log(options.R_min) + parameters.MS.MAP.logPost))
            % Propose theta_i
            logPost_target = log(1-options.dR_max) + logPost;
            options.P_next_step.start = abs(dtheta(i));
            [theta_new,logPost_exp] = getNextStepProfile(theta,theta_min,theta_max,dtheta/abs(dtheta(i)),logPost_target,...
                                                         @(theta) -logPosterior(theta,options.logPost_options),...
                                                         parameters.constraints,options.P_next_step);
            theta_i = theta_new(i);
            
            % Linear constraints
            if ~isempty(parameters.constraints.A)
                A = parameters.constraints.A(:,I);
                b = parameters.constraints.b - 10^-10 - parameters.constraints.A(:,i)*theta_i;
            else
                A = [];
                b = [];
            end
            if ~isempty(parameters.constraints.Aeq)
                Aeq = parameters.constraints.Aeq(:,I) - parameters.constraints.Aeq(:,i)*theta_i;
                beq = parameters.constraints.beq;
            else
                Aeq = [];
                beq = [];
            end
            
            if logPost_exp > -inf
                % Optimize
                [theta_new,J_opt] = ...
                    fmincon(@(theta_I) logPosterior([theta_I(I1);theta_new(i);theta_I(I2-1)],options.logPost_options),...     % negative log-likelihood function
                                        theta_new(I),...
                                        A  ,b  ,... % linear inequality constraints
                                        Aeq,beq,... % linear equality constraints     [],[],[],[],...   % initial parameter
                                        parameters.min(I),...   % lower bound
                                        parameters.max(I),...   % upper bound
                                        [],options.fmincon);    % options

                % Restore full vector and determine update direction
                logPost = -J_opt;
                dtheta = [theta_new(I1);theta_i;theta_new(I2-1)] - theta;
                theta = theta + dtheta;
                if strcmp(options.update_mode,'one-dimensional')
                    dtheta = dtheta.*([1:parameters.number]'==i);
                end
            else
                logPost = -inf;
                theta = theta_new;
                theta(i) = theta(i) + s*1e-16;
            end
            
            % Store results
            switch s
                case 1
                    parameters.P(i).par     = [parameters.P(i).par,theta];
                    parameters.P(i).logPost = [parameters.P(i).logPost,logPost];
                    parameters.P(i).R       = [parameters.P(i).R,exp(logPost - parameters.MS.MAP.logPost)];
                case -1
                    parameters.P(i).par     = [theta,parameters.P(i).par];
                    parameters.P(i).logPost = [logPost,parameters.P(i).logPost]; 
                    parameters.P(i).R       = [exp(logPost - parameters.MS.MAP.logPost),parameters.P(i).R];
            end
            
            % Update plot
            if strcmp(options.plot,'true')
                fh = plotP(parameters,fh,options.parameter_index,options.plot_options);
            end
            
            % Output command line
            disp([num2str(i,'%d') '-th P: point ' num2str(length(parameters.P(i).R)-1,'%d') ', R = ' ...
                  num2str(exp(logPost - parameters.MS.MAP.logPost),'%.3e') ' (optimized) / '...
                  num2str(exp(logPost_exp - parameters.MS.MAP.logPost),'%.3e') ' (predicted)']);
        end
    end    
end
end

%% REOPTIMIZE PROFILE FROM THE BOARDER
if strcmp(options.reoptimize,'true')
disp('');
disp('Re-optimization of profile');
% Loop: Parameters
for i = options.parameter_index
    disp('');
    % Index set
    I1 = [1:i-1]';
    I2 = [i+1:parameters.number]';
    I  = [I1;I2];
    % Likelihood function option
    options.logPost_options.grad_ind = I(:);
    options.logPost_options.sign = 'negative';

    %% COMPUTE OPTIMUM FOR IN-/DECREASING THETA
    for s = [-1,1]
        % Find set
        if s == -1
            ind = find(parameters.P(i).par(i,:) < parameters.MS.MAP.par(i));
            ind = ind(2:end);
        else
            ind = find(parameters.P(i).par(i,:) > parameters.MS.MAP.par(i));
            ind = ind(end-1:-1:1);
        end
 
        % Loop: Index points
        for k = ind
            % Starting point
            theta_new = parameters.P(i).par(:,k+s);
            theta_new(i) = parameters.P(i).par(i,k);
            theta_i = theta_new(i);
            
            % Modification of options struct
            options_fmincon = options.fmincon;
            if isfield(options.fmincon,'TypicalX')
                if ~isempty(options.fmincon.TypicalX)
                    options_fmincon.TypicalX = options_fmincon.TypicalX(I);
                end
            end
            if isfield(options.fmincon,'FinDiffRelStep')
                if ~isempty(options.fmincon.FinDiffRelStep)
                    options_fmincon.FinDiffRelStep = options_fmincon.FinDiffRelStep(I);
                end
            end
            
            % Linear constraints
            if ~isempty(parameters.constraints.A)
                A = parameters.constraints.A(:,I);
                b = parameters.constraints.b - 10^-10 - parameters.constraints.A(:,i)*theta_i;
            else
                A = [];
                b = [];
            end
            if ~isempty(parameters.constraints.Aeq)
                Aeq = parameters.constraints.Aeq(:,I) - parameters.constraints.Aeq(:,i)*theta_i;
                beq = parameters.constraints.beq;
            else
                Aeq = [];
                beq = [];
            end
            
            % Optimize
            [theta_new,J_opt] = ...
                fmincon(@(theta_I) logPosterior([theta_I(I1);theta_new(i);theta_I(I2-1)],options.logPost_options),...     % negative log-likelihood function
                                    theta_new(I),...        % initial parameter
                                    A  ,b  ,...             % linear inequality constraints
                                    Aeq,beq,...             % linear equality constraints
                                    parameters.min(I),...   % lower bound
                                    parameters.max(I),...   % upper bound
                                    [],options_fmincon);    % options
            logPost = -J_opt;
            
            % Assignment
            if -J_opt > parameters.P(i).logPost(k);
                parameters.P(i).par(I,k) = theta_new;
                parameters.P(i).logPost(k) = logPost;
                parameters.P(i).R(k) = exp(logPost - parameters.MS.MAP.logPost);
            end
            
            % Update plot
            if strcmp(options.plot,'true')
                fh = plotP(parameters,fh,options.parameter_index,options.plot_options);
            end
            
            % Output command line
            disp([num2str(i,'%d') '-th P: point ' num2str(k,'%d') ...
                ' -> ' num2str(ind(end)-s,'%d')]);
        end
    end
    disp('');
end
end
%% 