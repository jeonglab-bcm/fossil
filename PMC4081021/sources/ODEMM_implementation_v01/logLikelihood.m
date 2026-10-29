% function logL = logLikelihood(xi,D,M,options)
function varargout = logLikelihood(varargin)

%% Structure of D
% D(j).type = 'kinetic' or 'dose response'
%
% 'kinetic'
% D(j).t = n_t x 1 vector (e.g., [0;5;...])
% D(j).u = 1 x 1 scalar
% D(j).y = n_t x N matrix
%
% 'dose response'
% D(j).t = 1 x 1 scalar
% D(j).u = n_u x 1 vector (e.g., [0;10-3;...])
% D(j).y = n_u x N matrix
    
%% Set default
xi = varargin{1};
M = varargin{2};
D = varargin{3};

options.sign = 'positive';
options.grad_ind = 1:length(xi);
if nargin == 4
    options = setdefault(varargin{4},options);
end

try
%% Stucture of theta
for s = 1:M.N_subpop
    theta{s} = M.theta{s}(xi);
    dthetadxi{s} = M.dthetadxi{s}(xi);
    w{s} = M.w{s}(xi);
    dwdxi{s} = M.dwdxi{s}(xi);
end

%% Simulation and evaluation of likelihood function
% Initialization
logL = 0;
dlogLdxi = zeros(length(xi),1);
% Loop: Experimental conditions
for e = 1:length(D)
    switch D(e).type
        case 'kinetic'
            for s = 1:M.N_subpop
                % States
                [X,dXdtheta] = M.model(D(e).t,theta{s},D(e).u);
                mu{s} = M.mu{s,e}(D(e).t,X,xi,D(e).u);
                sigma{s} = M.sigma{s,e}(D(e).t,X,xi,D(e).u);

                % Sensitivities
                dXdxi{s} = zeros(size(X,2),length(xi),length(D(e).t));
                for k = 1:length(D(e).t)
                    dXdxi{s}(:,:,k) = dXdtheta(:,:,k)*dthetadxi{s};
                end
                dmudxi{s} = M.dmudxi{s,e}(D(e).t,X,dXdxi{s},xi,D(e).u);
                dsigmadxi{s} = M.dsigmadxi{s,e}(D(e).t,X,dXdxi{s},xi,D(e).u);
                
            end
            % Evaluation of probability density
            for k = 1:length(D(e).t)
                % Data
                y = D(e).y(k,:)';
                y = y(~isnan(y));
                % Loop: Subpopulations
                p = zeros(length(y),1);
                dpdxi = zeros(length(y),length(xi));
                for s = 1:M.N_subpop
                    p = p + w{s}*pdf(M.distribution{s},y,mu{s}(k),sigma{s}(k));
                    switch M.distribution{s}
                        case 'logn'
                            dpdxi = dpdxi + pdf('logn',y,mu{s}(k),sigma{s}(k))*dwdxi{s} ...
                                          + w{s}/sigma{s}(k)*bsxfun(@times,pdf('logn',y,mu{s}(k),sigma{s}(k)),((log(y)-mu{s}(k))/sigma{s}(k)*dmudxi{s}(k,:)+(((log(y)-mu{s}(k))/sigma{s}(k)).^2-1)*dsigmadxi{s}(k,:)));
                        case 'norm'
                            dpdxi = dpdxi + pdf('norm',y,mu{s}(k),sigma{s}(k))*dwdxi{s} ...
                                          + w{s}/sigma{s}(k)*bsxfun(@times,pdf('norm',y,mu{s}(k),sigma{s}(k)),((y-mu{s}(k))/sigma{s}(k)*dmudxi{s}(k,:)+(((y-mu{s}(k))/sigma{s}(k)).^2-1)*dsigmadxi{s}(k,:)));
                    end
                end
                % Evaluation log-likelihood
                logL = logL + sum(log(p));
                dlogLdxi = dlogLdxi + sum(bsxfun(@times,1./p,dpdxi))';
            end
        case 'dose response'
            % Loop: Doses
            for d = 1:length(D(e).u)
                % Data
                y = D(e).y(d,:)';
                y = y(~isnan(y));
                % Loop: Subpopulations
                p = zeros(length(y),1);
                dpdxi = zeros(length(y),length(xi));
                for s = 1:M.N_subpop
                    [X,dXdtheta] = M.model(D(e).t,theta{s},D(e).u(d));
                    mu{s} = M.mu{s,e}(D(e).t,X,xi,D(e).u(d));
                    sigma{s} = M.sigma{s,e}(D(e).t,X,xi,D(e).u(d));
                    
                    % Sensitivities
                    dXdxi{s} = zeros(size(X,2),length(xi),length(D(e).t));
                    for k = 1:length(D(e).t)
                        dXdxi{s}(:,:,k) = dXdtheta(:,:,k)*dthetadxi{s};
                    end
                    dmudxi{s} = M.dmudxi{s,e}(D(e).t,X,dXdxi{s},xi,D(e).u(d));
                    dsigmadxi{s} = M.dsigmadxi{s,e}(D(e).t,X,dXdxi{s},xi,D(e).u(d));
                    
                    % Evaluation of probability density
                    p = p + w{s}*pdf(M.distribution{s},y,mu{s}(k),sigma{s}(k));
                    switch M.distribution{s}
                        case 'logn'
                            dpdxi = dpdxi + pdf('logn',y,mu{s}(k),sigma{s}(k))*dwdxi{s} ...
                                          + w{s}/sigma{s}(k)*bsxfun(@times,pdf('logn',y,mu{s}(k),sigma{s}(k)),((log(y)-mu{s}(k))/sigma{s}(k)*dmudxi{s}(k,:)+(((log(y)-mu{s}(k))/sigma{s}(k)).^2-1)*dsigmadxi{s}(k,:)));
                        case 'norm'
                            dpdxi = dpdxi + pdf('norm',y,mu{s}(k),sigma{s}(k))*dwdxi{s} ...
                                          + w{s}/sigma{s}(k)*bsxfun(@times,pdf('norm',y,mu{s}(k),sigma{s}(k)),((y-mu{s}(k))/sigma{s}(k)*dmudxi{s}(k,:)+(((y-mu{s}(k))/sigma{s}(k)).^2-1)*dsigmadxi{s}(k,:)));
                    end
                end
                % Evaluation log-likelihood
                logL = logL + sum(log(p));
                dlogLdxi = dlogLdxi + sum(bsxfun(@times,1./p,dpdxi))';
            end
    end
end

catch
    logL = -inf;
    dlogLdxi = zeros(length(xi),1);
end

% if logL == -inf
%     fh = plotODEMix(D,M,xi);
% end

%% Output assignment
if nargout == 1
    switch  options.sign
        case 'positive'
            varargout{1} =  logL;
        case 'negative'
            varargout{1} = -logL;
    end
else
    switch  options.sign
        case 'positive'
            varargout{1} =  logL;
            varargout{2} =  dlogLdxi(options.grad_ind);
        case 'negative'
            varargout{1} = -logL;
            varargout{2} = -dlogLdxi(options.grad_ind);
    end
end

