function [v,x]=read_txt(path)
% Stand-in for LIMPIC's read_txt.m: the original opens a file dialog (uigetfile).
% This one takes the next file from the global queue LIMPIC_FILES and reads it
% the same way (load, drop the first 50 points).
global LIMPIC_FILES LIMPIC_NEXT
if nargin < 1
    path = LIMPIC_FILES{LIMPIC_NEXT};
    LIMPIC_NEXT = LIMPIC_NEXT + 1;
end
data=load_spectrum(path);
x=data(51:end,1)';
v=data(51:end,2)';
