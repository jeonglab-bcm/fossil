function data=load_spectrum(path)
% load(path), skipping lines that do not hold two numbers (line 32768 of
% SOL_5_TXT/SOL_calib_08e.txt is damaged in the publisher's archive).
lines=strsplit(fileread(path),"\n");
data=zeros(numel(lines),2); n=0;
for i=1:numel(lines)
  t=sscanf(lines{i},'%f');
  if numel(t)==2, n=n+1; data(n,:)=t'; end
end
data=data(1:n,:);
