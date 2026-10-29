function numstr = num2str_sign(num,options)

numstr = num2str(num,options);
if num > 0
    numstr = ['+' numstr];
end