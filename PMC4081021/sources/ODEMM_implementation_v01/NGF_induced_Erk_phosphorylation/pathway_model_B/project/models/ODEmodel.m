% Model variant 2

function [X,XS] = ODEmodel(T,theta,u)

% Initialization
data.theta = theta;
if length(u) > 1
    error('u has the wrong dimension!');
else
    data.u = u;
end

% Refinement of time vector
if length(T) <= 100
    if T(1) == 0
        Tsim = linspace(T(1),T(2),10); 
        ind = [1,10];
        k0 = 2;
    else
        Tsim = linspace(0,T(1),10); 
        ind = 10;
        k0 = 2;
    end
    for k = k0:length(T)-1
        Tsim_k = linspace(T(k),T(k+1),10);
        Tsim = [Tsim,Tsim_k(2:end)];
        ind = [ind,length(Tsim)];
    end
end


% Initialization of CVode
options = CVodeSetOptions('Reltol',1e-10,...
                          'AbsTol',1e-10,...
                          'MaxStep',1e10,...%                          'JacobianFn',@jacfn,...
                          'Userdata',data);
x0 = ...
[0;
(theta(3)*theta(9))/(theta(3) + theta(4));
(theta(3)*theta(9)*theta(10))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4))));
(theta(3)*theta(9)*theta(10)*theta(11))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4)))*(theta(6) + (theta(3)*theta(9)*theta(10))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4))))));
(theta(3)*theta(9)*theta(10)*theta(11)*theta(12))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4)))*(theta(7) + (theta(3)*theta(9)*theta(10)*theta(11))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4)))*(theta(6) + (theta(3)*theta(9)*theta(10))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4)))))))*(theta(6) + (theta(3)*theta(9)*theta(10))/((theta(3) + theta(4))*(theta(5) + (theta(3)*theta(9))/(theta(3) + theta(4))))))];

CVodeInit(@rhsfn,'BDF','Newton',0,x0,options);

% Initialization of CVodes
NS = 12; % number of parameters
FSAoptions = CVodeSensSetOptions('method','Simultaneous',...
                                 'ErrControl',true,...
                                 'ParamScales',1:NS);
xS0 = ...
[0,0,0,0,0,0,0,0,0,0,0,0;
0,0,(theta(4)*theta(9))/(theta(3) + theta(4))^2,-(theta(3)*theta(9))/(theta(3) + theta(4))^2,0,0,0,0,theta(3)/(theta(3) + theta(4)),0,0,0;
0,0,(theta(4)*theta(5)*theta(9)*theta(10))/(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9))^2,-(theta(3)*theta(5)*theta(9)*theta(10))/(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9))^2,-(theta(3)*theta(9)*theta(10)*(theta(3) + theta(4)))/(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9))^2,0,0,0,(theta(3)*theta(5)*theta(10)*(theta(3) + theta(4)))/(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9))^2,(theta(3)*theta(9))/(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9)),0,0;
0,0,(theta(4)*theta(5)*theta(6)*theta(9)*theta(10)*theta(11))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10))^2,-(theta(3)*theta(5)*theta(6)*theta(9)*theta(10)*theta(11))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10))^2,-(theta(3)*theta(6)*theta(9)*theta(10)*theta(11)*(theta(3) + theta(4)))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10))^2,-(theta(3)*theta(9)*theta(10)*theta(11)*(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9)))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10))^2,0,0,(theta(3)*theta(5)*theta(6)*theta(10)*theta(11)*(theta(3) + theta(4)))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10))^2,(theta(3)*theta(6)*theta(9)*theta(11)*(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9)))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10))^2,(theta(3)*theta(9)*theta(10))/(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10)),0;
0,0,(theta(4)*theta(5)*theta(6)*theta(7)*theta(9)*theta(10)*theta(11)*theta(12))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,-(theta(3)*theta(5)*theta(6)*theta(7)*theta(9)*theta(10)*theta(11)*theta(12))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,-(theta(3)*theta(6)*theta(7)*theta(9)*theta(10)*theta(11)*theta(12)*(theta(3) + theta(4)))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,-(theta(3)*theta(7)*theta(9)*theta(10)*theta(11)*theta(12)*(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9)))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,-(theta(3)*theta(9)*theta(10)*theta(11)*theta(12)*(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10)))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,0,(theta(3)*theta(5)*theta(6)*theta(7)*theta(10)*theta(11)*theta(12)*(theta(3) + theta(4)))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,(theta(3)*theta(6)*theta(7)*theta(9)*theta(11)*theta(12)*(theta(3)*theta(5) + theta(4)*theta(5) + theta(3)*theta(9)))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,(theta(3)*theta(7)*theta(9)*theta(10)*theta(12)*(theta(3)*theta(5)*theta(6) + theta(4)*theta(5)*theta(6) + theta(3)*theta(6)*theta(9) + theta(3)*theta(9)*theta(10)))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))^2,(theta(3)*theta(9)*theta(10)*theta(11))/(theta(3)*theta(5)*theta(6)*theta(7) + theta(4)*theta(5)*theta(6)*theta(7) + theta(3)*theta(6)*theta(7)*theta(9) + theta(3)*theta(7)*theta(9)*theta(10) + theta(3)*theta(9)*theta(10)*theta(11))];

CVodeSensInit(NS,@rhsSfn,xS0,FSAoptions);

% Simulation using CVode
[~,~,X,XS] = CVode(Tsim(2:end),'Normal');
X = [x0(:)';X'];
XS(:,:,2:length(Tsim)) = XS;
XS(:,:,1) = xS0;

X = X(ind,:);
XS = XS(:,:,ind);

% Free memory
CVodeFree;

return
%%

function [f,flag,new_data] = rhsfn(t,x,data)
% ODE right-hand side function

theta = data.theta;
u = data.u;

f = ...
[u*theta(1)*(theta(8) - x(1)) - theta(2)*x(1);
(theta(3) + x(1))*(theta(9) - x(2)) - theta(4)*x(2);
x(2)*(theta(10) - x(3)) - theta(5)*x(3);
x(3)*(theta(11) - x(4)) - theta(6)*x(4);
x(4)*(theta(12) - x(5)) - theta(7)*x(5)];


flag = 0;
new_data = [];

return

function [fS,flag,new_data] = rhsSfn(t,x,f,xS,data)
% Sensitivity right-hand side function

theta = data.theta;
u = data.u;

J = jacfn(t,x,f,data);

fS = J*xS + ...
            [u*(theta(8) - x(1)),-x(1),0,0,0,0,0,u*theta(1),0,0,0,0;
            0,0,theta(9) - x(2),-x(2),0,0,0,0,theta(3) + x(1),0,0,0;
            0,0,0,0,-x(3),0,0,0,0,x(2),0,0;
            0,0,0,0,0,-x(4),0,0,0,0,x(3),0;
            0,0,0,0,0,0,-x(5),0,0,0,0,x(4)];

flag = 0;
new_data = [];

return

function [J,flag,new_data] = jacfn(t,x,f,data)
% ODE right-hand side Jacobian

theta = data.theta;
u = data.u;
  
J = ...
[- theta(2) - u*theta(1),0,0,0,0;
theta(9) - x(2),- theta(3) - theta(4) - x(1),0,0,0;
0,theta(10) - x(3),- theta(5) - x(2),0,0;
0,0,theta(11) - x(4),- theta(6) - x(3),0;
0,0,0,theta(12) - x(5),- theta(7) - x(4)];

flag = 0;
new_data = [];

