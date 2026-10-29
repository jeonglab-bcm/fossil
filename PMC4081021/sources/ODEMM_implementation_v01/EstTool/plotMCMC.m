% plotMCMC plots the MCMC sample stored in a parameter object.
%
% USAGE:
% ======
% fh = plotMCMC(parameters)
% fh = plotMCMC(parameters,fh)
% fh = plotMCMC(parameters,fh,options)
%
% INPUTS:
% =======
% parameters ... parameter object containing information about parameters
% 	and MCMC sample.
% fh ... handle of figure in which profile likelihood is plotted. If no
%   figure handle is provided, a new figure is opened.
% options ... options of plotting
%   .bins ... number of bins (default = 30).
%   .hold_on ... conserve of current plot content (default = 'false').
%   .interval ... method uses to determine plot bounds (default = 'dynamic').
%       'dynamic' ... bounds are most extreme values of sample.
%       'static' ... bounds are lower and upper bounds provided in 
%           parameter object.
%       'none' ... bounds are chosen automatically by MATLAB.
%
% Outputs:
% ========
% fh .. figure handle
%
% 2012/07/11 Jan Hasenauer

% function fh = plotMCMC(parameters,fh,options)
function fh = plotMCMC(varargin)

%% CHECK AND ASSIGN INPUTS
% Assign parameters
if nargin >= 1
    parameters = varargin{1};
else
    error('plotPL requires a parameter object as input.');
end

% Open figure
if nargin >= 2
    if ~isempty(varargin{2})
        fh = figure(varargin{2});
    else
        fh = figure;
    end
else
    fh = figure;
end

% Options
options.bins = 50;
options.hold_on = 'false';
options.interval = 'dynamic';
if nargin == 3
    options = setdefault(varargin{3},options);
end

%% PLOT PROFILE LIKELIHOODS
% Compute number of subfigure
s = round(sqrt(parameters.number)*[1,1]);
if prod(s) < parameters.number
    s(2) = s(2) + 1;
end

% Loop: Parameter
for i = 1:parameters.number

    % Open subplot
    subplot(s(1),s(2),i); hold off;
    if strcmp(options.hold_on,'true');
        hold on;
    else
        hold off;
    end

    % Histograms
    [N,X] = hist(parameters.MCMC.sample.par(i,:),options.bins);
    bar(X,N/max(N),1,'facecolor',0.7*[1,1,1]);
    
    % Limits
    switch options.interval
        case 'static'
            xlim([parameters.min(i),parameters.max(i)]);
        case 'dynamic'
            xlim([min(parameters.MCMC.sample.par(i,:)),max(parameters.MCMC.sample.par(i,:))]);
        case 'none'
            %
        otherwise
            error('This option is not available.');
    end
    ylim([0,1.1]);
    % Labels
    xlabel(parameters.name(i));
    if mod(i,s(2)) == 1
        ylabel('lik. ration, R');
    else
        set(gca,'Ytick',[]);
    end

end

drawnow;
