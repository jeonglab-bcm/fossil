% function fh = plotODEMix(D,M,xi,options)
function fh = plotODEMix(varargin)

%% Assign inputs
D = varargin{1};
if nargin >= 3
    M = varargin{2};
    xi = varargin{3};
else
    M = [];
    xi = [];
end

% Set defaults
options.type = 'kde';
options.model.col = 'r';
options.model.lw  = 2;
options.model.points = 100;
options.model.plot = 'continuous'; % 'hist'
options.data.plot = 'filled'; %'empty'
options.data.col  = 'b';
options.data.fill_col = 0.7*[1,1,1];
options.data.lw   = 2;
options.data.bins = 100;
options.x_scale = 'lin';
for e = 1:length(D)
    options.boundaries(e).y_min = [];
    options.boundaries(e).y_max = [];
    options.ylabel{e} = 'frequency';
    options.z_max{e} = [];
end
if nargin == 4
    options = setdefault(varargin{4},options);
end

%% Introduction
if ~isempty(M)
    for s = 1:M.N_subpop
        theta{s} = M.theta{s}(xi);
        dthetadxi{s} = M.dthetadxi{s}(xi);
        w{s} = M.w{s}(xi);
        dwdxi{s} = M.dwdxi{s}(xi);
    end
end

%% Visualization
% Loop: Experimental conditions
for e = 1:length(D)
    % Open figure
    fh(e) = figure('name',D(e).name);
    % Plot
    switch D(e).type
        % Time response
        case 'kinetic'
            % Subplot structure
            sx = round(sqrt(length(D(e).t)));
            sy = ceil(length(D(e).t)/sx);
            % Simulation
            if ~isempty(M)
                for s = 1:M.N_subpop
                    [X,dXdtheta] = M.model(D(e).t,theta{s},D(e).u);
                    mu{s} = M.mu{s,e}(D(e).t,X,xi,D(e).u);
                    sigma{s} = M.sigma{s,e,1}(D(e).t,X,xi,D(e).u);
                end
            end
            % Boundaries
            if isempty(options.boundaries(e).y_min) || isempty(options.boundaries(e).y_max)
                y_min{e} =  inf;
                y_max{e} = -inf;
                for k = 1:length(D(e).t)
                    y = D(e).y(k,:)';
                    y = y(~isnan(y));
                    y_min{e} = min(y_min{e},min(y));
                    y_max{e} = max(y_max{e},max(y));
                end
            else
                y_min{e} = options.boundaries(e).y_min;
                y_max{e} = options.boundaries(e).y_max;
            end
            switch options.x_scale
                case 'lin'
                    y_hist = linspace(y_min{e},y_max{e},options.data.bins+1)';
                    d_y_hist = y_hist(2)-y_hist(1);
                    y_grid = linspace(y_min{e},y_max{e},options.model.points+1)';
                    d_y_grid = y_grid(2)-y_grid(1);
                case 'log'
                    z_hist = linspace(log10(y_min{e}),log10(y_max{e}),options.data.bins+1)';
                    d_y_hist = (z_hist(2)-z_hist(1));
                    y_hist = 10.^z_hist;
                    z_grid = linspace(log10(y_min{e}),log10(y_max{e}),options.model.points+1)';
                    d_y_grid = (z_grid(2)-z_grid(1));
                    y_grid = 10.^z_grid;
            end
            % Evaluation of probability density
            for k = 1:length(D(e).t)
                subplot(sy,sx,k);
                % Data
                y = D(e).y(k,:)';
                y = y(~isnan(y));
                h = hist(y,y_hist);
                h = (h(1:end-1)'/sum(h(1:end-1)));
                % Density calculation
                if ~isempty(M)
                    p = zeros(size(y_grid));
                    cp = zeros(size(y_grid));
                    for s = 1:M.N_subpop
                        p = p + w{s}*pdf(M.distribution{s},y_grid,mu{s}(k),sigma{s}(k));
                        cp = cp + w{s}*cdf(M.distribution{s},y_grid,mu{s}(k),sigma{s}(k));
                    end
                end
                % Plot
                switch options.data.plot
                    case 'filled'
                        fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],options.data.fill_col); hold on;
                    case 'empty'
                        plot(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],...
                            '-','color',options.data.col,'linewidth',options.data.lw); hold on;
                end
                if ~isempty(M)
                    switch options.model.plot
                        case 'continuous'
                            switch options.x_scale
                                case 'lin'
                                    plot(y_grid,p*d_y_hist,'-','color',options.model.col,'linewidth',options.model.lw);
                                case 'log'
                                    plot(y_grid,p.*y_grid*d_y_hist*log(10),'-','color',options.model.col,'linewidth',options.model.lw);
                            end
                        case 'hist'
                            h_sim = diff(cp)*d_y_hist/d_y_grid;
                            plot(y_grid(round(0.5:0.5:length(y_hist))),[0;h_sim(round(0.5:0.5:length(h_sim)));0],...
                                 '-','color',options.model.col,'linewidth',options.model.lw); hold on;
                    end
                end
                % Label
                xlabel(D(e).measurand);
                ylabel(options.ylabel{e});
                xlim([y_min{e},y_max{e}]);
                if ~isempty(options.z_max{e})
                    ylim([0,options.z_max{e}]);
                end
                title(['time = ' num2str(D(e).t(k))]);
                set(gca,'xscale',options.x_scale);
                % Data
                if (e == 1) && (k == 1)
                    if isempty(M)
                        legend('data')
                    else
                        legend('data','model')
                    end
                end
            end
        % Dose response
        case 'dose response'
            % Subplot structure
            sx = round(sqrt(length(D(e).u)));
            sy = ceil(length(D(e).u)/sx);
            % Boundaries
            if isempty(options.boundaries(e).y_min) || isempty(options.boundaries(e).y_max)
                y_min{e} =  inf;
                y_max{e} = -inf;
                for d = 1:length(D(e).u)
                    y = D(e).y(k,:)';
                    y = y(~isnan(y));
                    h = hist(y,y_hist);
                    h = (h(1:end-1)'/sum(h(1:end-1)));
                end
            else
                y_min{e} = options.boundaries(e).y_min;
                y_max{e} = options.boundaries(e).y_max;
            end
            y_grid = linspace(y_min{e},y_max{e},options.model.points)';
            switch options.x_scale
                case 'lin'
                    y_hist = linspace(y_min{e},y_max{e},options.data.bins+1)';
                    d_y_hist = y_hist(2)-y_hist(1);
                    y_grid = linspace(y_min{e},y_max{e},options.model.points+1)';
                    d_y_grid = y_grid(2)-y_grid(1);
                case 'log'
                    z_hist = linspace(log10(y_min{e}),log10(y_max{e}),options.data.bins+1)';
                    d_y_hist = (z_hist(2)-z_hist(1));
                    y_hist = 10.^z_hist;
                    z_grid = linspace(log10(y_min{e}),log10(y_max{e}),options.model.points+1)';
                    d_y_grid = (z_grid(2)-z_grid(1));
                    y_grid = 10.^z_grid;
            end
            % Loop: Doses
            for d = 1:length(D(e).u)
                subplot(sy,sx,d);
                % Data
                y = D(e).y(d,:)';
                y = y(~isnan(y));
                h = hist(y,y_hist);
                h = (h(1:end-1)'/sum(h(1:end-1)));
                % Density calculation
                if ~isempty(M)
                    p = zeros(size(y_grid));
                    cp = zeros(size(y_grid));
                    for s = 1:M.N_subpop
                        % Simulation
                        [X,dXdtheta] = M.model(D(e).t,theta{s},D(e).u(d));
                        mu{s} = M.mu{s,e}(D(e).t,X,xi,D(e).u(d));
                        sigma{s} = M.sigma{s,e}(D(e).t,X,xi,D(e).u(d));
                        % Evaluation of probability density
                        p = p + w{s}*pdf(M.distribution{s},y_grid,mu{s},sigma{s});
                        cp = cp + w{s}*cdf(M.distribution{s},y_grid,mu{s},sigma{s});
                    end
                end
                % Plot
                switch options.data.plot
                    case 'filled'
                        fill(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],options.data.fill_col); hold on;
                    case 'empty'
                        plot(y_hist(round(0.5:0.5:length(y_hist))),[0;h(round(0.5:0.5:length(h)));0],...
                            '-','color',options.data.col,'linewidth',options.data.lw); hold on;
                end
                if ~isempty(M)
                    switch options.model.plot
                        case 'continuous'
                            switch options.x_scale
                                case 'lin'
                                    plot(y_grid,p*d_y_hist,'-','color',options.model.col,'linewidth',options.model.lw);
                                case 'log'
                                    plot(y_grid,p.*y_grid*d_y_hist*log(10),'-','color',options.model.col,'linewidth',options.model.lw);
                            end
                        case 'hist'
                            h_sim = diff(cp)*d_y_hist/d_y_grid;
                            plot(y_grid(round(0.5:0.5:length(y_hist))),[0;h_sim(round(0.5:0.5:length(h_sim)));0],...
                                 '-','color',options.model.col,'linewidth',options.model.lw); hold on;
                    end
                end
                % Label
                xlabel(D(e).measurand);
                ylabel(options.ylabel{e});
                xlim([y_min{e},y_max{e}]);
                if ~isempty(options.z_max{e})
                    ylim([0,options.z_max{e}]);
                end
                title(['dose = ' num2str(D(e).u(d))]);
                set(gca,'xscale',options.x_scale);
                % Data
                if (e == 1) && (d == 1)
                    if isempty(M)
                        legend('data')
                    else
                        legend('data','model')
                    end
                end
           end
    end
end