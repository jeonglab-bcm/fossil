% getNextStepProfile is a support function for the profile calculation
%   and is called by computeProfile. It determines the length of the 
%   update step given update direction, parameter constraints,
%   log-posterior and target log posterior.
%
% USAGE:
% ======
% function [theta_new,logPost] = getNextStepProfile(theta,theta_min,theta_max,dtheta,logPost_target,logPosterior)
%
% INPUTS:
% =======
% theta ... starting parameter   
% theta_min ... lower bound for parameters   
% theta_max ... upper bound for parameters   
% dtheta ... upper direction
% logPost_target ... target value for log-posterior
% logPosterior ... log-posterior of model as function of the parameters.
%
% Outputs:
% ========
% theta_new ... parameter proposal
% logPost ... log-posterior at proposed parameter
%
% 2012/07/12 Jan Hasenauer

function [theta_new,logPost_new] = getNextStepProfile(theta,theta_min,theta_max,dtheta,logPost_target,logPosterior,constraints,options)

%% INITALIZATION
c     = min(max(options.start,options.min),options.max);
c_min = options.min; 
c_max = options.max;

theta_new = max(min(theta + c_min*dtheta,theta_max),theta_min);
logPost_c_min = logPosterior(theta_new);

% Constraints
if ~isempty(constraints.A)
    A = constraints.A;
    b = constraints.b;
else
    A = zeros(1,length(theta));
    b = 1;
end

if logPost_c_min >= logPost_target
    %% BISECTION
    while c_max/c_min > 1.5
        % Proposal
        theta_new = max(min(theta + c*dtheta,theta_max),theta_min);
        % Evaluate objective
        if max(A*theta_new > b) || max(theta_new > theta_max) || max(theta_new < theta_min)
            logPost = -inf;
        else
            logPost = logPosterior(theta_new);
        end
        % Update bounds
        if logPost <= logPost_target
            c_max = c;
        else 
            c_min = c;
            logPost_c_min = logPost;
        end
        % Update scaling
        c = sqrt(c_min*c_max);
    end
end    
% Determine theta
theta_new = theta + c_min*dtheta;
logPost_new = logPost_c_min;
