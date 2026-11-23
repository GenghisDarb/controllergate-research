%   SpotOn_main.m
%   Copyright (C) 2017 Anders Sejr Hansen & Maxime Woringer
clear; clc; clearvars -global; close all; 

%%%%%%%%%%%%%%%%%%%%%%%% GNU LICENSE OVERVIEW %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This program is free software: you can redistribute it and/or modify it
% under the terms of the GNU General Public License as published by the
% Free Software Foundation, either version 3 of the License, or any later
% version.   
% This program is distributed in the hope that it will be useful, but
% WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
% Public License for more details.
% 
% If you modify this Program, or any covered work, by linking or combining it
% with Matlab or any Matlab toolbox, the licensors of this Program grant you 
% additional permission to convey the resulting work.
%
% You should have received a copy of the GNU General Public License along
% with this program. If not, please see <http://www.gnu.org/licenses/>.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%% DEFINE PARAMETERS FOR MODEL-FITTING %%%%%%%%%%%%%%%%%%%%

%%%%% Choose DataSet
DataSet = 1;    % Use DataSet=1 for an example of how to process data for multiple cells from a single replicate
                % Use DataSet=2 for an example of how to process data for multiple cells from multiple replicates
data_struct = struct([]);

%%%%% Acquisition Parameters: 
TimeGap = 7.477; % delay between frames in milliseconds
dZ = 0.700; % The axial observation slice in micrometers; Rougly 0.7 um for the example data (HiLo)
GapsAllowed = 1; % The number of allowed gaps in the tracking

%%%%% Data Processing Parameters:
TimePoints = 8; % How many delays to consider: N timepoints yield N-1 delays
BinWidth = 0.010; % Bin Width for computing histogram in micrometers (only for PDF; Spot-On uses 1 nm bins for CDF)
UseAllTraj = 0; % If UseAllTraj=1, all data from all trajectories will be used; If UseAllTraj=0, only the first X displacements will be used
JumpsToConsider = 4; % If UseAllTraj=0, the first JumpsToConsiders displacements for each dT where possible will be used. 
MaxJumpPlotPDF = 1.05; % the cut-off for displaying the displacement histograms plots
MaxJumpPlotCDF = 3.05; % the cut-off for displaying the displacement CDF plots
MaxJump = 5.05; % the overall maximal displacements to consider in micrometers
SavePlot = 1; % if SavePlot=1, key output plots will be saved to the folder "SavedPlots"; Otherwise set SavePlot = 0;
DoPlots = 1; % if DoPlots=1, Spot-On will output plots, but not if it's zero. Avoiding plots speeds up Spot-On for batch analysis

%%%%% Model Fitting Parameters:
ModelFit = 2; %Use 1 for PDF-fitting; Use 2 for CDF-fitting
DoSingleCellFit = 1; %Set to 1 if you want to analyse all single cells individually (slow). 
NumberOfStates = 2; % If NumberOfStates=2, a 2-state model will be used; If NumberOfStates=3, a 3-state model will be used 
FitIterations = 2; % Input the desired number of fitting iterations (random initial parameter guess for each)
FitLocError = 0; % If FitLocError=1, the localization error will fitted from the data
FitLocErrorRange = [0.010 0.075]; % min/max for model-fitted localization error in micrometers.
LocError = 0.035; % If FitLocError=0, LocError in units of micrometers will be used. 
UseWeights = 0; % If UseWeights=0, all TimePoints are given equal weights. If UseWeights=1, TimePoints are weighted according to how much data there is. E.g. 1dT will be weighted more than 5dT.
D_Free_2State = [0.5 25]; % min/max Diffusion constant for Free state in 2-state model (units um^2/s)
D_Bound_2State = [0.0001 0.08]; % min/max Diffusion constant for Bound state in 2-state model (units um^2/s)
D_Free1_3State = [0.5 25]; % min/max Diffusion constant #1 for Free state in 3-state model (units um^2/s)
D_Free2_3State = [0.5 25]; % min/max Diffusion constant #2 for Free state in 3-state model (units um^2/s)
D_Bound_3State = [0.0001 0.08]; % min/max Diffusion constant for Bound state in 3-state model (units um^2/s)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%% DEFINE DATA SET PARAMETERS %%%%%%%%%%%%%%%%%%%%%%%%
if DataSet == 1 % Example DataSet 1: a single replicate of Halo-hCTCF at 134 Hz
    data_struct(1).path = [pwd, filesep, 'Data', filesep, 'CTCF_134Hz_rep1', filesep];
    data_struct(1).workspaces = {'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell01', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell02', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell03', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell04', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell05'};
    data_struct(1).Include = [1,2,3,4,5];
    SampleName = 'U2OS C32 Halo-hCTCF; PA-JF646; ~134 Hz; rep1';
   
elseif DataSet == 2 % Example DataSet 2: two replicates of Halo-hCTCF at 134 Hz
    % 1st CTCF replicate:
    data_struct(1).path = [pwd, filesep, 'Data', filesep, 'CTCF_134Hz_rep1', filesep];
    data_struct(1).workspaces = {'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell01', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell02', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell03', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell04', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep1_cell05'};
    data_struct(1).Include = [1,2,3,4,5];   
    % 3rd CTCF replicate:
    data_struct(2).path = [pwd, filesep, 'Data', filesep, 'CTCF_134Hz_rep3', filesep];
    data_struct(2).workspaces = {'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep3_cell01', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep3_cell02', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep3_cell03', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep3_cell04', 'U2OS_C32_Halo-CTCF_PA-JF646_1ms-633nm_134Hz_rep3_cell05'};
    data_struct(2).Include = [1,2,3,4,5];
    % name of merged dataset
    SampleName = 'U2OS C32 Halo-hCTCF; PA-JF646; ~134 Hz; two replicates';   
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%% SpotOn core mechanics %%%%%%%%%%%%%%%%%%%%%%%%%%%
Params = struct(); % Use Params to feed all the relevant data/parameters into the relevant functions
Params.TimeGap = TimeGap; Params.dZ = dZ; Params.GapsAllowed = GapsAllowed; Params.TimePoints = TimePoints; Params.BinWidth = BinWidth; Params.UseAllTraj = UseAllTraj; Params.DoPlots = DoPlots; Params.UseWeights = UseWeights;
Params.JumpsToConsider = JumpsToConsider; Params.MaxJumpPlotPDF = MaxJumpPlotPDF; Params.MaxJumpPlotCDF = MaxJumpPlotCDF; Params.MaxJump = MaxJump; Params.SavePlot = SavePlot; Params.ModelFit = ModelFit;
Params.DoSingleCellFit = DoSingleCellFit; Params.FitIterations = FitIterations; Params.FitLocError = FitLocError; Params.FitLocErrorRange = FitLocErrorRange; Params.LocError = LocError; Params.NumberOfStates = NumberOfStates;
Params.D_Free_2State = D_Free_2State; Params.D_Bound_2State = D_Bound_2State; Params.D_Free1_3State = D_Free1_3State; Params.D_Free2_3State = D_Free2_3State; Params.D_Bound_3State = D_Bound_3State;
Params.curr_dir = pwd; Params.SampleName = SampleName; Params.data_struct = data_struct;
% add the relevant paths
addpath(genpath([pwd, filesep, 'SpotOn_package', filesep])); 
display('Added local paths for Spot-on core mechanics');
[Output_struct] = SpotOn_core(Params);













