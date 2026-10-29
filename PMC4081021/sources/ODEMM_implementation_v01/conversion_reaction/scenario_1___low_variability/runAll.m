clear all;
close all;
clc;

%% Parameter estimation
% Mixture model analysis
fitting__statistical_analysis

% ODE model: no subpopulations
fitting__1norm
fitting__1logn_mean
fitting__1logn_median

% ODE-constraint mixture model: different levels of k1a
fitting__2norm_k1a
fitting__2logn_mean_k1a
fitting__2logn_median_k1a

% ODE-constraint mixture model: different levels of k1b
fitting__2norm_k1b
fitting__2logn_mean_k1b
fitting__2logn_median_k1b

% ODE-constraint mixture model: different levels of k2
fitting__2norm_k2
fitting__2logn_mean_k2
fitting__2logn_median_k2

