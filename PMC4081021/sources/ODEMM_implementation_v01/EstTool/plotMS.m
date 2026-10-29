% plotMS plots the result of the multi-start optimization stored in parameters.
%
% USAGE:
% ======
% fh = plotMS(parameters)
% fh = plotMS(parameters,fh)
% fh = plotMS(parameters,fh,options)
%
% INPUTS:
% =======
% parameters ... parameter struct containing information about parameters
%   and profile likelihood.
% fh ... handle of figure in which profile likelihood is plotted. If no
%   figure handle is provided, a new figure is opened.
% options ... options of plotting
%   .title ... switches plot title of (default = 'off').
%
% Outputs:
% ========
% fh .. figure handle
%
% 2012/05/31 Jan Hasenauer

% function fh = plotMS(parameters,fh,options)
function fh = plotMS(varargin)

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
options.title = 'off';
options.bounds = 'on';
if nargin == 3
    options = setdefault(varargin{3},options);
end

%% ASSIGN COLORS
i = length(parameters.MS.MAP_list.logPost);
Col = colormap(gray(i+ceil(i/3)));

%% PLOT OBJECTIVES
subplot(2,2,1);
plot(1:i,parameters.MS.MAP_list.logPost,'-','color',0.9*[1,1,1],'linewidth',2); hold on;
for j = i:-1:1
    plot(j,parameters.MS.MAP_list.logPost(j),'o','color',Col(j,:),'linewidth',2); hold on;
end
hold off;
xlim([1-0.2,i+0.2]);
xlabel('start');
ylabel('log-likelihood');
if strcmp(options.title,'on')
    title('all estimates');
end

%% PLOT TOP TEN OBJECTIVES
subplot(2,2,3);
plot(1:min(i,10),parameters.MS.MAP_list.logPost(1:min(i,10)),'-','color',0.9*[1,1,1],'linewidth',2); hold on;
for j = min(i,10):-1:1
    plot(j,parameters.MS.MAP_list.logPost(j),'o','color',Col(j,:),'linewidth',2); hold on;
end
hold off;
xlim([1-0.2,min(i,10)+0.2]);
ylim([min(parameters.MS.MAP_list.logPost(1)-1,parameters.MS.MAP_list.logPost(min(i,10))),parameters.MS.MAP_list.logPost(1)+1]);
xlabel('start');
ylabel('log-likelihood');
if strcmp(options.title,'on')
    title('top 10 estimates');
end

%% PLOT PARAMETERS
subplot(2,2,[2,4]);
for j = i:-1:1
    plot(parameters.MS.MAP_list.par(:,j)',1:parameters.number,'-o','color',Col(j,:),'linewidth',2); hold on;
end
plot(parameters.MS.MAP_list.par(:,1)',1:parameters.number,'r-o','linewidth',2); hold on;
if strcmp(options.bounds,'on')
    plot(parameters.min',1:parameters.number,'b--','linewidth',2); hold on;
    plot(parameters.max',1:parameters.number,'b--','linewidth',2); hold on;
end
hold off;
ylim([1-0.2,parameters.number+0.2]);
ylabel(' ');
xlabel('parameters values');
set(gca,'ytick',1:parameters.number,'yticklabel',parameters.name)

if strcmp(options.title,'on')
    title('estimated parameters');
end
drawnow;
