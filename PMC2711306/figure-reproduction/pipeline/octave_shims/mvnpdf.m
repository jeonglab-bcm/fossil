function p = mvnpdf(x, mu, s)
% Shim for the Statistics Toolbox mvnpdf in the scalar case the authors use: x, mu scalars and s
% the variance.
  p = exp(-0.5 * (x - mu).^2 ./ s) ./ sqrt(2 * pi * s);
end
