function [X,XS] = simConversionReaction(T,theta,u)

% Initialization
data.theta = theta;
if length(u) > 1
    error('u has the wrong dimension!');
else
    data.u = u;
end

% Initialization of CVode
options = CVodeSetOptions('Reltol',1e-7,...
                          'AbsTol',1e-7,...
                          'MaxStep',1e10,...
                          'JacobianFn',@jacfn,...
                          'Userdata',data);
x0 = theta(1)/(theta(1)+theta(2));
CVodeInit(@rhsfn,'BDF','Newton',0,x0,options);

% Initialization of CVodes
NS = 3; % number of parameters
FSAoptions = CVodeSensSetOptions('method','Simultaneous',...
                                 'ErrControl',true,...
                                 'ParamScales',1:NS);
xS0 = [ theta(2)/(theta(1)+theta(2))^2,...
       -theta(1)/(theta(1)+theta(2))^2,...
                          0];
CVodeSensInit(NS,@rhsSfn,xS0,FSAoptions);

% Simulation using CVode
if T(1) == 0
    [~,~,X,XS] = CVode(T(2:end),'Normal');
    X = [x0(:)';X'];
    XS(:,:,2:length(T)) = XS;
    XS(:,:,1) = xS0;
else
    [~,~,X,XS] = CVode(T,'Normal');
    X = X(:,:)';
    XS = XS(:,:,:);
end

% Free memory
CVodeFree;

return
%%

function [f,flag,new_data] = rhsfn(t,x,data)
% ODE right-hand side function

theta = data.theta;
u = data.u;

f = (theta(1)+theta(3)*u) - (theta(1)+theta(3)*u+theta(2))*x;

flag = 0;
new_data = [];

return

function [fS,flag,new_data] = rhsSfn(t,x,f,xS,data)
% Sensitivity right-hand side function

theta = data.theta;
u = data.u;

J = jacfn(t,x,f,data);

fS = J*xS + [1-x,-x,u*(1-x)];
    
flag = 0;
new_data = [];

return

function [J,flag,new_data] = jacfn(t,x,f,data)
% ODE right-hand side Jacobian

theta = data.theta;
u = data.u;

J = -(theta(1)+theta(3)*u+theta(2));

flag = 0;
new_data = [];

