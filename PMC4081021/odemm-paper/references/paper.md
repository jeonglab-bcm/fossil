# ODE Constrained Mixture Modelling: A Method for Unraveling Subpopulation Structures and Dynamics

Jan Hasenauer<sup>1,2</sup>\*, Christine Hasenauer<sup>3</sup>, Tim Hucho<sup>3,4</sup>, Fabian J. Theis<sup>1,2</sup>

1 Institute of Computational Biology, Helmholtz Center Munich, Munich, Germany, 2 Division of Mathematical Modeling of Biological Systems, Department of Mathematics, University of Technology Munich, Munich, Germany, 3 Max Planck Institute for Molecular Genetics, Berlin, Germany, 4 Division of Experimental Anesthesiology and Pain Research, Department of Anesthesiology and Intensive Care Medicine, University Hospital Cologne, Cologne, Germany

## Abstract

Functional cell-to-cell variability is ubiquitous in multicellular organisms as well as bacterial populations. Even genetically identical cells of the same cell type can respond differently to identical stimuli. Methods have been developed to analyse heterogeneous populations, e.g., mixture models and stochastic population models. The available methods are, however, either incapable of simultaneously analysing different experimental conditions or are computationally demanding and difficult to apply. Furthermore, they do not account for biological information available in the literature. To overcome disadvantages of existing methods, we combine mixture models and ordinary differential equation (ODE) models. The ODE models provide a mechanistic description of the underlying processes while mixture models provide an easy way to capture variability. In a simulation study, we show that the class of ODE constrained mixture models can unravel the subpopulation structure and determine the sources of cell-to-cell variability. In addition, the method provides reliable estimates for kinetic rates and subpopulation characteristics. We use ODE constrained mixture modelling to study NGF-induced Erk1/2 phosphorylation in primary sensory neurones, a process relevant in inflammatory and neuropathic pain. We propose a mechanistic pathway model for this process and reconstructed static and dynamical subpopulation characteristics across experimental conditions. We validate the model predictions experimentally, which verifies the capabilities of ODE constrained mixture models. These results illustrate that ODE constrained mixture models can reveal novel mechanistic insights and possess a high sensitivity.

## Author Summary

In this manuscript, we introduce ODE constrained mixture models for the analysis of population snapshot data of kinetics and dose responses. Population snapshot data can for instance be derived from flow cytometry or single-cell microscopy and provide information about the population structure and the dynamics of subpopulations. Currently available methods enable, however, only the extraction of this information if the subpopulations are very different. By combining pathway-specific ODE and mixture models, a more sensitive method is obtained, which can simultaneously analyse a variety of experimental conditions. ODE constrained mixture models facilitate the reconstruction of subpopulation sizes and dynamics, even in situations where the subpopulations are hardly distinguishable. This is shown for a simulation example as well as for the process of NGF-induced Erk1/2 phosphorylation in primary sensory neurones. We find that the proposed method allows for a simple but pervasive analysis of heterogeneous cell systems and more profound, mechanistic insights.

**Citation:** Hasenauer J, Hasenauer C, Hucho T, Theis FJ (2014) ODE Constrained Mixture Modelling: A Method for Unraveling Subpopulation Structures and Dynamics. PLoS Comput Biol 10(7): e1003686. doi:10.1371/journal.pcbi.1003686

**Editor:** Jorg Stelling, ETH Zurich, Switzerland

**Received** December 18, 2013; **Accepted** May 9, 2014; **Published** July 3, 2014

**Copyright:** © 2014 Hasenauer et al. This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.

**Funding:** The authors would like to acknowledge financial support from the German Federal Ministry of Education and Research (BMBF) within the Virtual Liver project (Grant No. 0315766), LungSys II (Grant No. 0316042G), MoPS (Grant No. 0315449D) and NoPain (Grant No. 0316177A), and the European Union within the ERC grant ‘‘LatentCauses.’’ The funders had no role in study design, data collection and analysis, decision to publish, or preparation of the manuscript.

**Competing Interests:** The authors have declared that no competing interests exist.

\* Email: jan.hasenauer@helmholtz-muenchen.de

This is a *PLOS Computational Biology* Methods article.

## Introduction

Multi-cellular organisms are faced with diverse, ever changing environments. To ensure survival and evolutionary success, microbial systems exploit cell-to-cell variability originating from bet-hedging strategies which increase the robustness against environmental changes [1]. Such bet-hedging relies on the formation of cellular subpopulations with distinct phenotypes and has been observed in the context of food source selection [2] and cellular stress response [3]. More complex organisms, such as mammals, evolved strategies to actively detect and respond to environmental changes. The building blocks for the necessary structures and functional units are cell types with distinct properties [4]. These cell types, e.g., neurones and immune cells, split up in further cellular subpopulations – cluster of cells with similar properties – to allow for a fine-grained recognition and tailored response. Due to the ubiquity of structured population heterogeneity, the analysis of subpopulation characteristics and causal differences between subpopulations is crucial for a holistic understanding of biological processes.

Heterogeneous cell populations are usually investigated using molecular and cell-biological methods with single cell resolution. Currently available methods include microscopy [5,6], flow cytometry [7], single-cell PCR [8–10] and single-cell mass spectrometry [11]. While some microscopy based approaches provide possibly time-resolved data [5], most experimental techniques do not allow for the tracking of individual cells but provide snapshots of the population. In this study, we considered these snapshot data, which can provide information about cellular properties, such as protein expression and phosphorylation. An illustration of snapshot data is provided in Figures 1A and B.

The analysis of population snapshot data can be approached using a multitude of statistical methods, e.g., thresholding, density based methods and mixture modelling. The selection of the method is highly problem specific [12]. Thresholding methods are the most commonly used tools to identify the size of a subpopulation, e.g., the size of a subpopulation expressing a particular marker [13]. Based on a control experiment a threshold (or gate) is defined based on which cells are classified as marker positive or negative. While thresholding works in cases of clearly separated subpopulations (Figure 1A), it fails for strongly overlapping heterogeneous populations (Figure 1B) as no appropriate threshold exists, resulting in large numbers of false positives and/or false negatives. Furthermore, thresholding only detects large changes rendering it insensitive. An improved sensitivity is achieved by density based methods, namely histogram-based and kernel density estimation (KDE)-based methods [14–19], which compare the full distributions. Nevertheless, also density based methods tend to underestimate the size of positive/responsive subpopulations. This is not the case for mixture models which describe the cell population as a weighted sum of the underlying subpopulations. The underlying subpopulations are described using simple distributions functions [7,20–22], those statistical properties, e.g., mean and variance, describe the subpopulation. The outcome of a mixture model based data analysis depends, more or less sensitively, on the distribution assumption [7]. To assess the temporal evolution of subpopulations, matching is performed [7,12].

In addition to the aforementioned shortcoming, currently available statistical methods can only analyse measured snapshot data. None of the methods provides directly mechanistic insights, prediction for hidden network components, hypotheses regarding causal factors for the population heterogeneity or estimates for reaction rates. To gain such additional insight and to simultaneously analyse multiple snapshots, a mechanistic description of the underlying process is required. Mostly, such descriptions are based on ordinary differential equations (ODEs). Commonly used ODE models, however, do not allow for the integration of distributional information but only use the measured mean concentration [23–26]. A summary of data analysis tools and their key properties is provided in Figure 1C.

In the following, we propose ODE constrained mixture models (ODE-MMs), a combination of mixture models and ODE based pathway models which exploits their individual advantages (Figure 1D). This novel class of models describes the individual snapshots using mixtures whose components are constrained by ODE models. These ODE models for the subpopulations are derived from the pathway topology and assumptions about causal, mechanistic differences between subpopulations. Due to the underlying mechanistic description of subpopulation dynamics, ODE-MMs can go beyond the obvious. Instead of only analysing the measured quantities and performing error-prone matching across conditions across multiple snapshots, ODE-MMs are capable of determining the dynamics of hidden components and testing for causal differences between subpopulations. This is illustrated using a simulation study of a conversion process.

Exemplarily, ODE-MMs are applied to investigate NGF-induced Erk1/2 phosphorylation in primary sensory neurones, a signalling pathway regulating pain sensitisation. Due to the diverse functional roles of sensory neurones, the cell system is highly heterogeneous. We introduce a dynamical model for NGF-induced Erk1/2 phosphorylation in primary sensory neurones and attempt the unraveling of the subpopulation structure and the source of heterogeneity using ODE-MMs. The results are validated using co-labelling experiments.

## Methods

### Ethics statement

All animal experiments were reported to the responsible authority, the *Landesamtes für Gesundheit und Soziales* (LAGeSo) in Berlin (T0370/05) and approved (license ZH120). All efforts were made to minimise the number of animals used and their suffering.

### Measurement data

In this work we consider collections $\mathcal{D}=\{\mathcal{D}^e_k\}_{e,k}$ of population snapshot data $\mathcal{D}^e_k$, as illustrated in Figures 1A and B. Experimental conditions are indexed by $e$ and time points are indexed by $k$. The individual snapshots $\mathcal{D}^e_k$ are measured at time $t^e_k$ under experimental condition $u^e$. $\mathcal{D}^e_k$ is a collection of single cell measurements $y^e_j(t^e_k)\in\mathbb{R}^{n_y}$, $\mathcal{D}^e_k=\{y^e_j(t^e_k)\}_j$, with $j$ indexing the individual cells. The single cell measurements are assumed to be statistically independent.

### Mixture models

The analysis of the individual population snapshots $\mathcal{D}^e_k$, which are samples of cells, is often approached using mixture models,

$$p(y|\theta)=\sum_{i=1}^{m} w_i\,p(y|\varphi_i)\ \text{ with }\ \theta=\{(w_i,\varphi_i)\}_{i=1}^{m}. \tag{1}$$

Parameters and probability weights of the $i$-th mixture component are denoted by $\varphi_i$ and $w_i\geq 0$, with $\sum_{i=1}^{m} w_i=1$, respectively. Common choices for the individual mixture components $p(y|\varphi_i)$ are normal, log-normal, skew normal, t-, and skew t-distributions [7]. In the case of normal mixtures the component parameters are mean $\mu_i$ and covariance matrix $\Sigma_i$, $\varphi_i=(\mu_i,\Sigma_i)$. The parameters $\theta$ of mixture models can be estimated using maximum likelihood methods,

$$\begin{aligned}&\max_{\theta\in\Theta}\left\{\ell(\theta):=\sum_{j}\,\log\left(\sum_{i=1}^{m} w_i\,p(y_j|\varphi_i)\right)\right\},\\ &\text{subject to}\quad \sum_{i=1}^{m} w_i=1,\end{aligned}$$

in which $\ell(\theta):=\log p(\mathcal{D}|\theta)$ denotes the log-likelihood function of the mixture model and $j$ is the index of the single cell measurement. The set of possible parameter values is denoted by $\Theta$.

The individual mixture components are often regarded as subpopulations with different characteristics, e.g., different expression levels. To analyse collections of snapshots $\mathcal{D}$, a matching of subpopulations detected under different conditions is performed [7,12]. The results of this matching can in principle be used to extract the characteristics of subpopulations and their dependence on time and stimuli. The matching performed between individual conditions is however often questionable, in particular if some populations change their characteristics dramatically or are not/hardly distinguishable under some condition. In this case matching-based methods are highly error-prone [12].

[Figure 1](../assets/figure/figure-1.jpg)

**Figure 1. Illustration of population snapshot data and ODE constrained mixture modelling.** (A) Heterogeneous population consisting of two homogeneous subpopulations with a very different response level. Snapshot data provide at different time points (filled circle) information about the biological state of single cells. This allows for the characterisation of the kinetics of the subpopulations using threshold, histogram and kernel density estimate (KDE) based methods as well as mixture modelling. (B) Heterogeneous population consisting of two heterogenous subpopulations with a large overlap of the dose response behaviour, rendering an analysis using snapshot data difficult. (C) Table including the available analysis tools for population snapshot data and proposed ODE constrained mixture modelling along with key properties of the methods. (D) Sketch of ODE constrained mixture modelling which combines mixture modelling of the measurement data with pathway information, thereby allowing for an improved quantification of subpopulation properties and mechanistic insights. doi:10.1371/journal.pcbi.1003686.g001

### Pathway models

To circumvent shortcomings of mixture modelling, we propose to complement it with pathway information. The responses of subpopulations to different experimental conditions is ultimately determined by the involved metabolic, signalling and gene regulatory pathways. Accordingly, experimental conditions can be matched using models of the underlying biochemical pathway.

Biochemical pathways are mostly modelled using reaction rate equations (RREs) [24], which are systems of ODEs. RREs describe the temporal evolution of the ‘‘average state’’ of cells in a cell population, e.g., the abundance of signalling molecules and their activity, assuming that the population is homogeneous. More precisely, RREs implicitly assume that the variance in the abundance of chemical species across cells is small. Therefore, these models can neither be used to process the distributional information encoded in snapshot data nor to study cellular subpopulations.

While RRE based modelling of heterogenous cell populations consisting of different subpopulations is not desirable, RREs might be used to model the dynamics of rather homogeneous subpopulations. In the following, we will describe the ‘‘average dynamics’’ of cells in the i-th subpopulation using a RRE,

$$\dot{x}_i=f(x_i,\xi_i,u),\quad x_i(0)=x_0(\xi_i,u),\quad i=1,\dots,m, \tag{2}$$

in which $x_i(t)\in\mathbb{R}_+^{n_x}$ is the state of the $i$-th subpopulation at time $t$, $\xi_i\in\mathbb{R}_+^{n_\xi}$ is the parameter vector of the $i$-th subpopulation, and $u(t)\in\mathbb{R}^{n_u}$ is the time-dependent external stimulus. The vector field $f$ encodes the biochemical pathway and $x_0$ models the dependence of the initial condition on subpopulation parameters and experimental conditions. The subpopulation parameters $\xi_i$ are a collection of parameters $k_0$ which are identical in all subpopulations and subpopulation specific parameters $k_i$, $\xi_i=(k_0,k_i)$. Identical parameters might be structural properties, such as affinities. Differences between subpopulations are modelled by differences in their parameters, $k_i\neq k_j$. These parameter discrepancies describe the causal differences between subpopulations, e.g., altered protein abundances, and are biologically essential when studying heterogeneity.

As most experimental procedures only allow for the assessment of a few chemical species, we introduce a measurement model,

$$y_i(t,u)=h(x_i(t,u),\xi_i,u). \tag{3}$$

If merely the $j-$th chemical species is observed this mapping becomes: $h(x_i(t,u),\xi_i,u)=x_{i,j}(t,u)$.

Assuming that the communication across and transitions between subpopulations can be neglected for the process of interest, the dynamics of the overall population are captured by the weighted dynamics of its subpopulations. This idea is exploited by ODE-MMs, and will in the following be illustrated for mixtures of normal distributions and more general mixture distributions.

### RRE constrained mixture of normal distributions

The most commonly used mixture models are mixtures of normal distributions, $p(y|\varphi_i)=\mathcal{N}(y|\mu_i,\Sigma_i)$, which are parameterised by mean $\mu_i$ and covariance $\Sigma_i$. As RREs describe the dynamics of the mean state $x_i(t,u)$ of homogeneous subpopulations, an obvious possibility is to model the condition- and time-dependent measured mean $\mu_i(t,u)$ of the mixture components by RREs,

$$\mu_i(t,u)=y_i(t,u)=h(x_i(t,u),\xi_i,u). \tag{4}$$

Accordingly, the component means ($\mu_i=\mu_i(t,u)$) are determined by the parameters of the subpopulation $i$, $\xi_i=(k_0,k_i)$. The component covariances ($\Sigma_i=\Sigma_i(t,u)$), which summarise cell-to-cell variability within the $i$-th subpopulation and measurement noise, are not constrained by RREs. Accordingly, we obtain RRE constrained mixture of normal distributions,

$$\begin{aligned}p(y|\theta,t,u)&=\sum_{i=1}^{m} w_i\,\mathcal{N}(y|\mu_i(t),\Sigma_i(t))\\ \text{with}\qquad \dot{x}_i&=f(x_i,\xi_i,u),\quad x_i(0)=x_0(\xi_i,u),\\ \mu_i&=h(x_i,\xi_i,u),\end{aligned} \tag{5}$$

with parameters $\theta=\{(w_i,\xi_i,\Sigma_i)\}_{i=1}^{m}$. The mixture parameters, $\varphi_i=(\mu_i,\Sigma_i)$, depend on experimental condition $u$ and time $t$. Furthermore, $\mu_i$ depends implicitly on $\xi_i$ via the ODE model.

In contrast to conventional mixture models (1), ODE-MMs (5) describe the distribution of the observed variables at discrete points and the temporal evolution of subpopulations in response to stimuli. Hence, ODE-MMs establish a mechanistic link between different experimental conditions and time points based on pathway models and differences between subpopulations. This renders error-prone matching of distributions across conditions unnecessary (see discussion in *Mixture models*).

### General class of ODE constrained mixture models

The combination of normal mixture models and RRE models yields simple ODE-MMs. More flexible ODE-MMs are obtained by considering other distributions $p(y|\varphi_i)$, e.g., log-normal, skew normal, t- or skew t-distributions [7]. Furthermore, more sophisticated descriptions of the biochemical processes can be employed, e.g., linear noise approximations [27,28], effective mesoscopic rate equations [29,30] or moment equations [31,32]. These classes of ODE models, $\dot{x}_i=f(x_i,\xi_i,u)$, do not only constrained means but also variances, covariances and higher order moments. Hence, more distribution parameters $\varphi_i$ can be linked to the state of the ODE model, $\varphi_i=h(x_i,\xi_i,u)$. In general, the subpopulation parameters $\xi_i$ contain mechanistic parameters as well as parameters $\nu_i$ which specify statistics of the distribution, $\xi_i=(k_0,k_i,\nu_i)$.

### Parameter estimation and model selection

The analysis of measurement data $\mathcal{D}$ using ODE-MMs requires the estimation of the parameters $\theta$. For this we will use maximum likelihood estimation. The likelihood function is the product of the conditional probability of the snapshot data $\mathcal{D}^e_k$ given the parameters $\theta$. The resulting optimisation problem in terms of the log-likelihood function $\ell(\theta)$ is

$$\begin{aligned}&\max_{\theta\in\Theta}\left\{\ell(\theta):=\sum_{e,k,j}\log\left(\sum_{i=1}^{m} w_i\,p\left(y^{k,e}_j|\varphi^e_i(t_k)\right)\right)\right\}\\ &\text{subject to}\quad \dot{x}_i^e=f(x^e_i,\xi_i,u^e),\quad x^e_i(0)=x_0(\xi_i,u^e)\\ &\qquad\qquad\quad \varphi^e_i=h(x^e_i,\xi_i,u^e),\quad \forall i,e,\\ &\qquad\qquad\quad 1=\sum_{i=1}^{m} w_i.\end{aligned} \tag{6}$$

Note that in contrast to the MMs we sum over all combinations of $k$ and $j$, meaning that all time points and experimental conditions are studied simultaneously.

Optimisation problem (6) belongs to the class of ODE constrained optimisation problems. In general this problem is non-convex and possesses local maxima. To determine the parameter vector $\theta^*$ which maximises the log-likelihood function, global optimisation methods are required. Commonly used global optimisation methods are multi-start local optimisation [33], evolutionary and genetic algorithms [34], particle swarm optimisers [35], simulated annealing [36] and hybrid optimisers [37,38]. For details we refer to available comprehensive surveys of local and global optimisation procedures [33,39–41]. In the following, we will use multi-start local optimisation, an approach which has been shown to be efficient for parameter estimation in RRE models [33].

As the measurement data are limited, the parameters can often not be determined uniquely. In particular the kinetic rates, $k_0$ and $k_i$, as well as the population fraction, $w_i$ often remain uncertain. A variety of methods exist to assess parameter uncertainties, including profile likelihoods [33,42], bootstrapping [43,44], Markov chain Monte Carlo sampling [45,46], Approximate Bayesian Computing [47,48] and local approximation to the objective function [44]. In the remainder, we use profile likelihoods due to their often superior efficiency. Profile likelihoods allow for a global uncertainty analysis of individual parameters by means of repeated optimisation. For details we refer to the work of Raue et al. [42].

The source of the cell-to-cell variability, namely the parameters which differ between subpopulations, are often unknown. ODE-MMs can be used to assess the plausibility of different potential sources of cell-to-cell variability by means of model selection. Models corresponding to different hypotheses can be formulated and fitted to the data. The comparison of these models using model selection criteria such as the Akaike information criterion (AIC) [49] or the Bayesian information criterion (BIC) [50] indicates which model is most appropriate. Using such model selection procedures, ODE-MMs can unravel the population structure by predicting differences in properties which have not been measured or are not even measurable. Furthermore, ODE-MMs provide information about rate constants. In contrast, conventional mixture models can only be used to analyse differences in observed quantities.

### Acquisition of snapshot data for NFG-induced Erk1/2 phosphorylation

The proposed ODE-MMs will be used to analyse NGF-induced Erk1/2 phosphorylation. The respective measurement data for NGF-induced Erk1/2 phosphorylation were acquired using quantitative automated microscopy (QuAM) [13]. The preparation of primary sensory neurones from rat (DRG cell culturing), the cell stimulation, the immunofluorescence labelling and the cell imaging was performed according to the protocol described by Andres et al. [19].

In short, primary sensory neurones derived from L1-L6 DRGs were prepared from male Sprague Dawley rats. Dissociated cells were cultured for 15–20 h before stimulated with NGF. After treatment, cells were fixed with paraformaldehyde and permeabilised with Triton X-100. Nonspecific binding sites were blocked and cultures were probed with primary antibodies (anti-phospho-Erk (Thr-202/Tyr-204) (1:200) and anti-Erk (1:500)) against target proteins, washed three times, and incubated with secondary antibodies. Cells were quantified with a Zeiss Axioplan 2 microscope controlled by the software Metacyte (Metasystems). As selection marker of sensory neurones, cell identification was performed on immunofluorescently-labelled (Erk staining) cells. The fluorescence intensities derived from pErk antibody and Erk antibody were quantified. To compensate for differences in the mean fluorescence intensity between experimental replicates, the data are normalised.

More detailed information, e.g., information about cell culture conditions as well as the detailed immunofluorescence protocol is provided in Supporting Information S1.

## Results

In the following, we will illustrate how ODE-MMs can be used, how the results can be interpreted and what kind of insights can be gained using them. For this purpose, we study a simulation example for which the ground truth is known as well as an application example for which new biological insights are gained using ODE-MMs.

### Simulation example: Conversion process

To illustrate the properties of ODE-MMs and to assess their performance, we consider the conversion process

$$\begin{array}{lll}\mathrm{R}_1: & \mathrm{A}\rightarrow\mathrm{B}, & \text{rate}=k_1u[\mathrm{A}],\\ \mathrm{R}_2: & \mathrm{A}\rightarrow\mathrm{B}, & \text{rate}=k_2[\mathrm{A}],\\ \mathrm{R}_3: & \mathrm{B}\rightarrow\mathrm{A}, & \text{rate}=k_3[\mathrm{B}],\end{array}$$

which is illustrated in Figure 2A. The reactions R<sub>1</sub> and R<sub>2</sub> model a stimulus dependent and a stimulus ($u$) independent (basal) conversion of A to B, respectively. The conversion of B to A is described by reaction R<sub>3</sub>. Concentrations of A and B are denoted by [A] and [B]. The conversion of A to B is modulated by the time-dependent concentration $u$ of an external stimulus, also denoted as input. The governing RRE for this conversion process is

$$\begin{aligned}\frac{d[\mathrm{A}]}{dt}&=-(k_1u+k_2)[\mathrm{A}]+k_3[\mathrm{B}]\\ \frac{d[\mathrm{B}]}{dt}&=+(k_1u+k_2)[\mathrm{A}]-k_3[\mathrm{B}]\end{aligned}$$

with $[\mathrm{A}]+[\mathrm{B}]$ being constant.

#### Population model and artificial data

Artificial data for the conversion process are generated using an ensemble cell population model [51], which belongs to the class of Bayesian hierarchical models. The ensemble consists of single cells whose stimulus response is governed by the RRE stated above. The parameters differ between cells and are drawn from a probability distribution. Ensemble models provide a more detailed description of cell populations and are, in principle, advantageous compared to the ODE-MMs. This description of cell-to-cell variability, namely parameter variability, is thought to be sufficient to describe genetic and epigenetic differences between single cells [51,52]. However, estimating parameters and parameter distributions of ensemble models is computationally very demanding. Already a single simulation of an ensemble model takes minutes, which limits their application. As ODE-MMs can be simulated orders of magnitudes faster, it is interesting to analyse whether they suffice for extracting the key properties of the underlying subpopulations. To address this question, we consider two scenarios: (1) a cell population consisting of two homogeneous subpopulations which do not overlap after stimulation (Figures 2B–D); (2) a cell population consisting of two heterogeneous, highly-overlapping subpopulations (Figures 2E–G). In both scenarios the subpopulations differ in their responsiveness $k_1$ to the stimulation $u(t)$. The remaining parameters, $k_2$ and $k_3$, also vary between individual cells but have the same probability distributions across the two subpopulations. The probability distribution of the parameters $k=(k_1,k_2,k_3)$ in the individual subpopulations and scenarios is depicted in Figures 2D and G. The initial condition of each cell is the steady state reached for $u=0$ and total concentration, $[\mathrm{A}]+[\mathrm{B}]$, equal to one. At $t=0$, the cells are stimulated, $u(t)=1$ for $t>0$, resulting in an increase in the abundance of B. Representative trajectory samples are shown in Figures 2A and D. To obtain the artificial measurement data (Figures 2C and F), the abundance of B is measured for 1,000 cells at $t=0$, 0.1, 0.2, 0.3, 0.5 and 1.0.

#### Hypothesis testing

Given the artificial data sets, we first asked whether ODE-MMs can detect the presence of two subpopulations and unravel the differences between them. To address this, we considered four competing hypotheses:

- H1 No subpopulations.

- H2 Two subpopulations with significantly different stimulus dependent conversion rates A to B ($k_{1,i}$ for subpopulation $i$).

- H3 Two subpopulations with significantly different stimulus independent (basal) conversion rates A to B ($k_{2,i}$ for subpopulation $i$).

- H4 Two subpopulations with significantly different conversion rates B to A ($k_{3,i}$ for subpopulation $i$).

These four scenarios were described using RRE constrained mixture models. To ensure robustness with respect to the distribution assumption, we considered normal distribution and log-normal distributions with the mean parameterized by the RRE as well as log-normal distributions with the median parameterised by the RRE.

The combination of the 4 hypothesis and the 3 distribution assumptions yields 12 models. These 12 models were fitted to the artificial measurement data using multi-start local optimisation. Components weights were constrained to the interval [0,1], reaction rate constants to $[10^{-6},10^{4}]$, and scale parameters (normal distribution: standard deviation; log-normal distribution: log-standard deviation) to $[10^{-2.5},10^{2.5}]$. A detailed specification of the models, the maximal value of the log-likelihood function and the BIC values are provided in Table 1. Based on the BIC values, hypotheses H1, H3 and H4 can be rejected. The same holds for the AIC values. The choice of the distribution and its parameterisation plays a role. However, compared to the different model structures, the influence is negligible. Thus, ODE-MMs determined robustly the correct number of subpopulations and even revealed the differences between the subpopulations.

#### Reconstruction of subpopulation characteristics

Following the hypothesis testing, the best models were analysed in greater detail, starting with comparisons of model predictions with the data. This comparison revealed that the measured means (Figures 2B and E) as well as the full distributions (Figures 2C and F) were described well by the selected ODE-MM. Furthermore, although the data did not contain a label to which subpopulation a cell belongs, the ODE-MM derived estimates for mean concentrations of [B] in the subpopulations agreed well with the true means (Figures 2B and E). For scenario 1 (homogeneous subpopulations) the true and the estimated subpopulation means were actually indistinguishable. Hence, ODE-MM derived state estimates for the subpopulation characteristics can indeed be interpreted as average subpopulation characteristics.

#### Interpretation of ODE-MM parameters

Regarding the parameters, we found for scenario 1 that the ODE-MM estimates of the parameters $k_2$ and $k_3$ agree with the population average (Figure 2D). For the subpopulation specific parameter $k_1$, the ODE-MM estimates correspond to the mean parameter in the subpopulation. Even the relative size of the subpopulations is determined well. For scenario 2, in which the subpopulations are more heterogenous and overlap, the inference of the model properties is more challenging and the estimate for the subpopulation size is slightly off (Figure 2G). This can however be explained by the relatively small number of observed cells. As a reference, the distribution of population size observed when sampling 1,000 cells is depicted in Figure 2G. Furthermore, for the subpopulation which responds only weakly to the stimulus, the ODE-MM estimate of the rate constant $k_1$ does not correspond to the average rate constant in the subpopulation but overestimates it by a factor of ∼1.6. The reason might be a low signal-to-noise ratio. In this subpopulation the basal rate constant $k_2$ exceeds $k_1$ by a factor of ∼5. In combination with the large cell-to-cell variability, this might limit the estimation accuracy.

To assess the uncertainty of the parameters, we computed the profile likelihoods. The confidence intervals derived from the profile likelihoods are relatively tight. This indicates that even for cell populations consisting of heterogeneous subpopulations, population snapshots provide information about the dynamical parameters and the subpopulation statistics. Furthermore, for this artificial example, the average parameters in the subpopulation are always within the confidence intervals for the parameters of the ODE-MM. This suggests that the ODE-MM parameters can be interpreted as average parameters of the subpopulations.

To conclude the simulation example, we found that ODE-MMs facilitate the simultaneous analysis of several snapshot data sets. Furthermore, ODE-MMs can be used for hypothesis testing, and the states of the RREs accurately describe the subpopulations while their parameters provide estimates for the means of the underlying biological quantities.

[Figure 2](../assets/figure/figure-2.jpg)

**Figure 2. Result of an exemplarily study of a conversion process using ODE constrained mixture modelling.** For the conversion process sketched in (A) the cases of homogeneous, non-overlapping subpopulations (B,C,D) and heterogeneous, highly-overlapping subpopulations (E,F,G) are studied. (B,E) Histograms of artificial data for the reversible conversion process (6 time points, 1,000 cells), the best fit achieved using ODE-MM and the distribution predicted for the subpopulations. Artificial data have been generated by sampling single cell parameters from parameter distributions, simulating the single cell model and extracting the concentration of B. ODE-MM was fitted using multi-start local optimisation. (C,F) Representative samples of single cell trajectories for the two subpopulations, the means of the samples and the means for the subpopulations predicted by ODE-MM. (D,G) True parameter distributions (grey shaded area) from which single cell parameters are drawn (purple: subpopulation 1; green: subpopulation 2) and ODE-MM derived parameter estimates including the confidence intervals. Vertical lines mark the maximum likelihood estimates and the horizontal bars represent the confidence intervals corresponding to different confidence levels (80%, 90%, 95% and 99%) computed using profile likelihoods. For the population fraction $w_1$, the true value (circle) is shown and the sampling distribution (line) expected for the measured number of cells (1,000), which provides a measure for the expected estimation error. doi:10.1371/journal.pcbi.1003686.g002

**Table 1.** Parameter estimation and model selection results for conversion process with rather homogeneous subpopulations.

[Table 1](../assets/table/table-1.csv)

| Scenario | Model | m | distribution | ODE const. | variability | # par. | ℓ(θ*)(10⁴) in Scenario 1; ℓ(θ*)(10³) in Scenario 2 | BIC (10⁴) in Scenario 1; BIC (10³) in Scenario 2 | rank | ΔBIC | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H1,1 | 1 | normal | mean | - | 9 | 0.9806 | −1.9534 | 10 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H1,2 | 1 | log-normal | mean | - | 9 | 0.9785 | −1.9493 | 11 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H1,3 | 1 | log-normal | median | - | 9 | 0.9785 | −1.9492 | 12 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H2,1 | 2 | normal | mean | k1 | 17 | 1.0998 | −2.1848 | 3 | 6.215 | not rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H2,2 | 2 | log-normal | mean | k1 | 17 | 1.1001 | −2.1854 | 1 | 0 | optimal |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H2,3 | 2 | log-normal | median | k1 | 17 | 1.1001 | −2.1854 | 2 | 0.429 | not rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H3,1 | 2 | normal | mean | k2 | 17 | 0.9911 | −1.9673 | 9 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H3,2 | 2 | log-normal | mean | k2 | 17 | 1.0013 | −1.9878 | 7 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H3,3 | 2 | log-normal | median | k2 | 17 | 0.9949 | −1.9750 | 8 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H4,1 | 2 | normal | mean | k3 | 17 | 1.0087 | −2.0026 | 4 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H4,2 | 2 | log-normal | mean | k3 | 17 | 1.0077 | −2.0005 | 5 | >10 | rejected |
| Scenario 1: homogeneous, non-overlapping subpopulations after stimulation | ℳ_H4,3 | 2 | log-normal | median | k3 | 17 | 1.0032 | −1.9916 | 6 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H1,1 | 1 | normal | mean | - | 9 | 6.955 | −13.831 | 12 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H1,2 | 1 | log-normal | mean | - | 9 | 6.923 | −13.768 | 10 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H1,3 | 1 | log-normal | median | - | 9 | 6.922 | −13.766 | 11 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H2,1 | 2 | normal | mean | k1 | 17 | 7.059 | −13.970 | 3 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H2,2 | 2 | log-normal | mean | k1 | 17 | 7.069 | −13.991 | 1 | 0 | optimal |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H2,3 | 2 | log-normal | median | k1 | 17 | 7.068 | −13.988 | 2 | 2.928 | not rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H3,1 | 2 | normal | mean | k2 | 17 | 6.990 | −13.833 | 9 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H3,2 | 2 | log-normal | mean | k2 | 17 | 7.003 | −13.858 | 7 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H3,3 | 2 | log-normal | median | k2 | 17 | 6.997 | −13.846 | 8 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H4,1 | 2 | normal | mean | k3 | 17 | 7.025 | −13.901 | 5 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H4,2 | 2 | log-normal | mean | k3 | 17 | 7.027 | −13.906 | 4 | >10 | rejected |
| Scenario 2: heterogeneous, highly-overlapping subpopulations | ℳ_H4,3 | 2 | log-normal | median | k3 | 17 | 7.021 | −13.894 | 6 | >10 | rejected |

For both scenarios (homogeneous subpopulations and heterogeneous subpopulations) four different model hypothesis (H1: no subpopulations; H2: different levels of activatability, $k_1$; H3: different basal activation rates, $k_2$; and H4: different deactivation rates, $k_3$) were tested using three models each, differing in the distribution assumption (normal vs. log-normal) and the ODE constrained properties (subpopulation mean vs. subpopulation median). The resulting 12 ODE-MMs were fitted to the experimental data using multi-start local optimisation (accuracy: 10 digits). The plausibility of models has been evaluated using the Bayesian information criterion (BIC) and models were rejected if $\Delta_{\mathrm{BIC}}=\mathrm{BIC}_i-\mathrm{BIC}_{\mathrm{opt}}>10$ [85]. For both scenarios, ODE-MM unraveled the true underlying population structure (different $k_1$ values in the subpopulations) with high significance. doi:10.1371/journal.pcbi.1003686.t001

### Application example: NGF-induced Erk1/2 signalling

In this section, we use ODE-MMs to perform a data-driven study of NGF-induced Erk1/2 phosphorylation in primary sensory neurones. Primary sensory neurones are commonly used as a cellular model for investigating signalling components mediating pain sensitisation. NGF is known to induce a strong pain sensitisation during inflammation, but also to support neuronal repair during neuropathic pain. Studies showed that NGF binds and activates the receptor tyrosine kinase TrkA [53]. Activation of TrkA leads to the induction of the MAPK/Erk kinase pathway (see Figure 3A) resulting in the phosphorylation of ion channels and protein expression [53].

Beyond the importance of NGF-induced Erk1/2 phosphorylation in pain research, primary sensory neurones are well suited for the evaluation of ODE-MMs as they exhibit a significant degree of cell-to-cell variability. This variability is no nuisance but relevant for their biological function [54]. It has been shown that different neuronal subgroups with different protein abundances and even phosphorylation levels exist [22,54], namely neurones which detect mechanical stimuli, heat, cold or chemicals. The detailed dynamical characteristics of these subpopulations and the causal differences are largely unknown. In the following, we will employ ODE-MMs to quantify the characteristics of the NGF responsive and unresponsive neuronal subpopulations and their sizes, and to assess reaction rate constants which cannot be obtained experimentally (Figures 3B and C).

#### Experimental data

The quantitative assessment of signalling in primary and heterogeneous cells is challenging compared to cell lines as many experimental methods are not applicable. To study the dynamics of the MAPK/Erk pathway we previously introduced a quantitative automated microscopy technique [13]. This technique allows for the quantification of Erk1/2 activity in single cells and provides rich datasets regarding the cell-to-cell variability. Using this technique we recorded kinetics and dose responses of NGF-induced Erk1/2 phosphorylation [13]. The signals we observed represent relative Erk1/2 phosphorylation, $y=s[\mathrm{pErk}]$, as no calibration curve is employed. The unknown scaling constant which related absolute Erk1/2 phosphorylation, [pErk], and the measured quantity $y$ is denoted by $s$.

#### Pathway model

In the literature, it is described that NGF binds to TrkA, yielding the active signalling complex TrkA:NGF. TrkA:NGF-induces the activation of the Ras kinase, which phosphorylates the Raf kinase. The active Raf kinase phosphorylates Mek, which phosphorylates Erk1 and Erk2. In principle the consideration of all these steps is possible, but experimentally the activity of the signalling intermediates Ras, Raf and Mek is difficult to measure in primary sensory neurones as appropriate antibodies are not available. Therefore, we mainly consider a simple pathway model which merely accounts for NGF-TrkA interaction and Erk1/2 phosphorylation. We do not distinguish between Erk1 and Erk2, as their biochemical properties have been demonstrated to be nearly identical (see [55] and references therein). The resulting pathway model A considers five reactions,

$$\begin{array}{lll}\mathrm{R}_1: & \mathrm{TrkA}+\mathrm{NGF}\rightarrow\mathrm{TrkA}:\mathrm{NGF}, & \text{rate}=k_1[\mathrm{TrkA}][\mathrm{NGF}],\\ \mathrm{R}_2: & \mathrm{TrkA}:\mathrm{NGF}\rightarrow\mathrm{NGF}+\mathrm{TrkA}, & \text{rate}=k_2[\mathrm{TrkA}:\mathrm{NGF}],\\ \mathrm{R}_3: & \mathrm{Erk}\rightarrow\mathrm{pErk}, & \text{rate}=k_3[\mathrm{TrkA}:\mathrm{NGF}][\mathrm{Erk}],\\ \mathrm{R}_4: & \mathrm{Erk}\rightarrow\mathrm{pErk}, & \text{rate}=k_4[\mathrm{Erk}],\\ \mathrm{R}_5: & \mathrm{pErk}\rightarrow\mathrm{Erk}, & \text{rate}=k_5[\mathrm{pErk}],\end{array}$$

and is illustrated in Figure 3A. The reactions R<sub>1</sub> and R<sub>2</sub> describes binding and unbinding of TrkA and NGF. Basal and TrkA:NGF-induced phosphorylation of Erk are captured by R<sub>3</sub> and R<sub>4</sub>. The reactions R<sub>5</sub> describes the Erk dephosphorylation. By exploiting conservation of mass,

$$\begin{aligned}{}[\mathrm{TrkA}]+[\mathrm{TrkA}:\mathrm{NGF}]&=[\mathrm{TrkA}]_0\\ {}[\mathrm{NGF}]+[\mathrm{TrkA}:\mathrm{NGF}]&=[\mathrm{NGF}]_0\\ {}[\mathrm{Erk}]+[\mathrm{pErk}]&=[\mathrm{Erk}]_0,\end{aligned}$$

and the well justified assumption that the total NGF concentration is much larger than the total TrkA concentration, $[\mathrm{NGF}]_0\gg[\mathrm{TrkA}]_0$, the dynamics of TrkA:NGF and pErk can be stated as

$$\begin{aligned}\frac{d[\mathrm{TrkA}:\mathrm{NGF}]}{dt}&=k_1[\mathrm{NGF}]_0([\mathrm{TrkA}]_0-[\mathrm{TrkA}:\mathrm{NGF}])\\ &\quad-k_2[\mathrm{TrkA}:\mathrm{NGF}]\\ \frac{d[\mathrm{pErk}]}{dt}&=(k_3[\mathrm{TrkA}:\mathrm{NGF}]+k_4)([\mathrm{Erk}]_0-[\mathrm{pErk}])\\ &\quad-k_5[\mathrm{pErk}]\\ y&=s[\mathrm{pErk}],\end{aligned}$$

with kinetic parameters $k=(k_1,k_2,k_3,k_4,k_5,[\mathrm{TrkA}]_0,[\mathrm{Erk}]_0,s)$. As the absolute concentrations of TrkA and Erk are unknown, this system is structurally non-identifiable. To circumvent this we reformulate the system in terms of $x_1=k_3[\mathrm{TrkA}:\mathrm{NGF}]$ and $x_2=s[\mathrm{pErk}]$, yielding the RRE model

$$\begin{aligned}\frac{dx_1}{dt}&=k_1[\mathrm{NGF}]_0(k_3[\mathrm{TrkA}]_0-x_1)-k_2x_1\\ \frac{dx_2}{dt}&=(x_1+k_4)(s[\mathrm{Erk}]_0-x_2)-k_5x_2\\ y&=x_2.\end{aligned}$$

This ODE model merely depends on the products $s[\mathrm{Erk}]_0$ and $k_3[\mathrm{TrkA}]_0$ and not on the individual parameters $(s,[\mathrm{Erk}]_0)$ and $(k_3,[\mathrm{TrkA}]_0)$, respectively. Thus, we obtain the reduced vector of kinetic parameters $k=(k_1,k_2,k_4,k_5,k_3[\mathrm{TrkA}]_0,s[\mathrm{Erk}]_0)$.

In the remainder, all plots depict the scaled TrkA:NGF and pErk concentrations, $x_1$ and $x_2$.

#### Inference of subpopulation structure

We employed the dynamical pathway model A to assess the population dynamics and to compare the three hypotheses:

- H1 No subpopulations.

- H2 Two subpopulations with significantly different Erk levels ($[\mathrm{Erk}]_{0,i}$ for subpopulation $i$).

- H3 Two subpopulations with significantly different TrkA levels ($[\mathrm{TrkA}]_{0,i}$ for subpopulation $i$).

We only regarded altered abundance of signalling molecules as potential differences between subpopulations. Differences in elementary reaction rates would require mutations or differential post-translational modifications which we consider unlikely. As in the simulation example, the scenarios were described using RRE constrained mixture models. For each scenario we considered normal and log-normal mixture components with means parameterised by the RRE as well as log-normal mixture components with medians parameterised by the RRE. This yielded in total 9 ODE-MMs, which have been fitted using multi-start local optimisation. Properties of models, goodness of fit statistics and obtained BIC values are listed in Table 2. Based upon the BIC (and AIC) values for the different models hypotheses H1 and H2 were rejected compared to H3. Significance levels for the rejections were very high, indicating the presence of two subpopulations with different average levels of TrkA receptors.

We note that the rejection of hypotheses H1 and H2 requires information about the distribution of pErk levels. Even models for the simplest hypothesis, H1, describe the kinetic and dose response of the mean pErk level (Figure 3B). This proves that the mean is not informative enough and implies that simple RRE models are in general insufficient for determining subgroups. Using the distribution of pErk levels in combination with ODE-MMs, H1 can be rejected easily (Figure 3C) due to the strong model-data mismatch for stimulation with 1 nM and 10 nM NGF.

#### Size and characteristics of subpopulations

The selected population structure, H3, assumes different concentrations of the NGF receptor TrkA for the subpopulations. This results in different concentration of TrkA-NGF complexes and ultimately in different Erk phosphorylation levels. The overall Erk concentration, [Erk] + [pErk], is the same for the subpopulations. An illustration of the models and signalling is provided in Figure 4A.

The ODE-MMs representing H3 explain the kinetic and dose response measurements of the mean pErk concentration as well as the pErk distribution. Measurement data and fits for the best two models, ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub>, are depicted in Figures 4B and C. These two models exploit different parameterisations of the log-normal distributions (see Table 2). In ℳ<sub>H3,2</sub> the mean is parameterised using the RRE, while in ℳ<sub>H3,3</sub> the median is parameterised. The latter yields a slightly better fit, however, the differences are minor and not statistically significant. As ℳ<sub>H3,3</sub> does not describe the time-dependent mean, splines are used to obtain Figure 4B (bottom).

The maximum likelihood estimation of the model parameters provides estimates for the relative size of the subpopulations and their pErk levels. Roughly 70% of the cells belong to the subpopulation with low TrkA levels (subpopulation 1) and 30% of the cells possess high TrkA levels (subpopulation 2). Subpopulation 1 hardly responds to NGF, while subpopulation 2 responds with a 4-fold increase in pERK levels for a 1 nM NGF stimulation. The maximal response is reached after 10 minutes and the response amplitude saturates for NGF concentration $>1$ nM. The differences between the subpopulations sound large, however, a direct extraction of these insights from the data is impossible due the the large overlap of subpopulations. This renders the proposed ODE-MMs, which incorporate pathway information, essential.

#### Quantification of kinetic parameters and abundance differences

Beyond subpopulation differences in observed pErk levels, ODE-MMs rendered quantities accessible which could not be measured. In particular the Erk dephosphorylation rate and the NGF-TrkA affinities could be inferred. Furthermore, we found a 30-fold difference between TrkA levels in the two subpopulations. This information is valuable as TrkA antibodies with high sensitivity and specificity are not available for immunofluorescence based experiments in cultures of primary sensory neurones. A practical identifiability analysis using profile likelihood showed that all estimated parameters – kinetic parameters, subpopulation sizes and standard deviations – are identifiable (Figure 4D; and Figures 1 and 2 in Supporting Information S1). Indeed, the confidence intervals for most parameters, in particular the subpopulation sizes and standard deviations, are rather narrow (Tables 2, 3 and 4 in Supporting Information S1). This and the rather consistent estimates obtained using different models (Supporting Information S1), indicate the reliability of the parameter estimates.

The ODE-MMs ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub> for H1 possess 17 parameters while the ODE-MMs ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub> for H3 possess 30 parameters. As the ODE-MMs for H1 possess 13 parameters less than the ODE-MMs for H3 we expected that the parameters of ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub> are more well determined than the parameters of ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub>. The comparison of parameter uncertainties for H1 (Figure 3D) and for H3 (Figure 4D) yielded however a surprising, counterintuitive result. While the kinetic parameters of ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub> were mostly practically non-identifiable, all parameters of ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub> were practically identifiable. A possible explanation is that ODE-MMs for H1 cannot exploit all information encoded in the distribution as the model is not flexible enough, rendering the data less informative and causing non-identifiability of parameters. This on the other hand means that the informativeness of data depends on the model used to analyse them. More flexible models might not only provide deeper insights but also provide more reliable estimates.

[Figure 3](../assets/figure/figure-3.jpg)

**Figure 3. Models for NGF-induced Erk1/2 signalling without subpopulations.** (A) Schematic of model for NGF-induced Erk1/2 signalling. Arrows represent conversion reactions and regulatory interactions. (B) Mean and standard deviation of measured pErk levels (kinetic: *n* = 4, 18797 cells; dose response: *n* = 4, 12205 cells) as well as simulated mean for the models ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub>. (C) Histograms of the measured pErk levels (data of biological replica are pooled) and corresponding distributions computed using model ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub>. Simulation results for ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub> are very similar leading to significant overplotting. pErk levels in (B) and (C) are in arbitrary units of intensity (UI). (D) Maximum likelihood estimates of parameters and confidence intervals for the parameters of ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub>. Vertical lines mark the maximum likelihood estimates and the horizontal bars represent the confidence intervals corresponding to different confidence levels (80%, 90%, 95% and 99%) computed using profile likelihoods. doi:10.1371/journal.pcbi.1003686.g003

#### Comparison of pathway models

Pathway model A (Figure 5A, left) which we studied so far merely accounts for TrkA and Erk dynamics. In the literature more detailed models for NGF-induced Erk1/2 activation have been proposed [56–60]. Although these pathway models have been developed for cell lines, such as the rat pheochromocytoma cell line (PC12), we expect the structure of the pathway to be similar in primary DRG neurones. In contrast, protein abundances and reaction rates are most likely altered, which limits the reusability of the available quantitative information. In addition, cell lines are most likely more homogeneous than the primary DRG neurons considered in this project.

To evaluate the robustness of our predictions with respect to the choice of the pathway description, we considered two additional pathway models. Pathway models B and C (Figure 5A, middle and right) account for the signal amplification cascade and a negative feedback, two key features of the NGF-induced Erk1/2 activation pathway. These models are therefore more flexible and possess a larger number of unknown parameters. For details on the models and their mathematical descriptions we refer to the Supporting Information S1.

**Table 2.** Parameter estimation and model selection results for NGF-induced Erk1/2 signalling (pathway model A).

[Table 2](../assets/table/table-2.csv)

|  | m | distribution | ODE const. | variability | # par. | ℓ(θ*)(10⁴) | BIC (10⁴) | rank | ΔBIC | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ℳ_H1,1 | 1 | normal | mean | - | 17 | −5.2890 | 10.5955 | 9 | >10 | rejected |
| ℳ_H1,2 | 1 | log-normal | mean | - | 17 | −3.7659 | 7.5495 | 6 | >10 | rejected |
| ℳ_H1,3 | 1 | log-normal | median | - | 17 | −3.7556 | 7.5288 | 5 | >10 | rejected |
| ℳ_H2,1 | 2 | normal | mean | [Erk]_0 | 30 | −4.0348 | 8.1006 | 8 | >10 | rejected |
| ℳ_H2,2 | 2 | log-normal | mean | [Erk]_0 | 30 | −3.6482 | 7.3274 | 4 | >10 | rejected |
| ℳ_H2,3 | 2 | log-normal | median | [Erk]_0 | 30 | −3.6262 | 7.2835 | 3 | >10 | rejected |
| ℳ_H3,1 | 2 | normal | mean | [TrkA]_0 | 30 | −3.9846 | 8.0002 | 7 | >10 | rejected |
| ℳ_H3,2 | 2 | log-normal | mean | [TrkA]_0 | 30 | −3.5847 | 7.2003 | 2 | 2.189 | not rejected |
| ℳ_H3,3 | 2 | log-normal | median | [TrkA]_0 | 30 | −3.5846 | 7.2001 | 1 | 0 | optimal |

For each biological hypothesis (H1: no subpopulations; H2: different levels of total Erk, [Erk]<sub>0</sub>; H3: different levels of total TrkA, [TrkA]<sub>0</sub>) three models, differing in the distribution assumption (normal vs. log-normal) and the ODE constrained properties (subpopulation mean vs. subpopulation median), have been specified and fitted to the experimental data using multi-start local optimisation (accuracy: 10 digits). For the model selection using the Bayesian information criterion (BIC) we found that H1 and H2 could be rejected according to [85] as Δ<sub>BIC</sub> = BIC<sub>i</sub> − BIC<sub>opt</sub> > 10. The subpopulations seemed to follow a log-normal distribution. The two models, ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub>, which only differ in the ODE constrained property were acceptable. doi:10.1371/journal.pcbi.1003686.t002

As for pathway model A, we carried out the parameter estimation and model selection for pathway models B and C (Supporting Information S1). Interestingly, for all pathway models we found the same ranking of subpopulation structures. Two subpopulations with different TrkA concentrations, log-normally distributed pErk levels and ODE-constrained subpopulation median (ℳ<sub>H3,3</sub>) were always preferred. Furthermore, our comparison of BIC values (Figure 5B) revealed that the influence of the pathway model on the BIC values is small in comparison with the influence of the subpopulation structure (H1–H3) and the distribution assumptions. This indicates that for an accurate description of the measurement data, the subpopulation structures is more important than a more detailed description of the signalling pathway.

The hypothesis testing using different pathway models supported our prediction that TrkA is the key source of cell-to-cell variability. Moreover, the maximum likelihood estimates for the size of the responsive subpopulations (Figure 5C) were consistent. For the kinetic parameters such a comparison was not possible as (i) the meaning of parameters differ between pathway models and (ii) many parameters of the pathway models B and C are non-identifiable. As for more detailed pathway models we expect that the parameter identifiability becomes even worse, we did not study the most detailed and sophisticated model for the NGF signalling pathway [58,59].

#### Validation of subpopulation structure

To validate the ODE-MM derived prediction that subpopulations do not possess different Erk levels (H2) but different TrkA levels (H3), co-labelling experiments have been performed. In addition to Erk phosphorylation also total Erk is quantified using a second antibody. As both measurements provide only relative information the scales are not comparable. For details regarding the experiments, we refer to the section *Materials and Methods* in Supporting Information S1.

Figures 6A and B depict the distribution of pErk and total Erk levels observed under control conditions and after stimulation with 1 nM NGF for 30 minutes. As expected, cells with high total Erk levels tend to possess high pErk levels. The Pearson correlation is 0.895 for the control and 0.696 for the stimulation. The significant correlation decreases after NGF stimulation is caused by the appearance of a group of cells with high pErk signals. To analyse the NGF-induced response in more detail we fit a simple 2-dimensional mixture of normal distribution to the logarithmized data. Figure 6B shows the level sets of the two mixture components, which are denoted by subpopulations 1 and 2. By comparing Figures 6A and B we found that subpopulation 1 is similar to the control population. Hence, subpopulation 1 hardly responds to the NGF stimulation. In contrast, subpopulation 2 has a significantly increased average pErk level.

As subpopulations 1 and 2 have similar total Erk but different pErk distributions, total Erk is not the cause of the different activation potentials of the subpopulations. This verifies the rejection of hypothesis H2, which assumed a predominant role of the total Erk. The different activation potentials have to be caused by a further network compound such as TrkA. This partially validates hypothesis H3. However, the differences could in principle also be due to intermediate signalling components, such as Raf and Mek, which are not considered in the model. While a conclusive proof of H3 would require a simultaneous labelling of pErk and TrkA, which is currently infeasible due to the lack of appropriate TrkA antibodies, there are three – in our opinion convincing – indications that TrkA causes the population split. First of all, the available measurement data can be described by assuming different TrkA levels. Secondly, the estimate for the fraction of cells with high TrkA levels (≈30%) derived via ODE-MMs from the pErk kinetic and dose response (Figure 4B) agrees perfectly with the size of the responsive subpopulation found by co-labelling pErk and Erk (subpopulation 2, Figure 6B). The size of the responsive subpopulation has been determined from the co-labelling data using mixture modelling, which yields for this 2D data robust results as the subpopulations are rather different. Finally, Kashiba et al. [61] found that 35% of primary sensory neurones are TrkA positive, which is in good agreement with the size of the responsive subpopulation we found using ODE-MM and co-labelling.

[Figure 4](../assets/figure/figure-4.jpg)

**Figure 4. Models for NGF-induced Erk1/2 signalling with two subpopulations which have different TrkA levels.** (A) Schematic of model for NGF-induced Erk1/2 signalling. Arrows represent conversion reactions and regulatory interactions. The frequency of an object is used to illustrate its abundance. (B) Mean and standard deviation of measured pErk levels (kinetic: *n* = 4, 18797 cells; dose response: *n* = 4, 12205 cells) as well as simulated mean for the models ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub>. (C) Histograms of the measured pErk levels (data of biological replica are pooled) and corresponding distributions computed using model ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub>. Simulation results for ℳ<sub>H3,2</sub> and ℳ<sub>H3,3</sub> are very similar leading to significant overplotting. pErk levels in (B) and (C) are in arbitrary units of intensity (UI). (D) Maximum likelihood estimates of parameters and confidence intervals for the parameters of ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub>. Vertical lines mark the maximum likelihood estimates and the horizontal bars represent the confidence intervals corresponding to different confidence levels (80%, 90%, 95% and 99%) computed using profile likelihoods. doi:10.1371/journal.pcbi.1003686.g004

[Figure 5](../assets/figure/figure-5.jpg)

**Figure 5. Comparison of three different pathway models for the NGF-induced Erk1/2 activation.** (A) Schematics of three model for NGF-induced Erk1/2 activation. Pathway model A is a simple two component model, while pathway models B and C contain a detailed description of the signalling cascade. Pathway model C also accounts for a negative feedback from pErk to Ras activation. (B) Comparison of different pathway models (colour-coded), hypotheses about the cell-to-cell variability (H1, H2 and H3) and distribution assumptions (distribution: normal vs. log-normal; ODE-constrained: mean or media). BIC values indicate that differences between the pathway models are small compared to differences arising from different variability hypotheses and distribution assumptions. (C) Maximum likelihood estimates of the subpopulations sizes found for each pathway model. doi:10.1371/journal.pcbi.1003686.g005

To conclude, in this section we proved the applicability of ODE-MMs to practically relevant biological problems. We used ODE-MMs to study data from primary sensory neurones and to determine subpopulation characteristics and kinetic rates. Furthermore, we provided a data-driven explanation for the observed cell-to-cell variability and validated this explanation partially using new experimental data.

[Figure 6](../assets/figure/figure-6.jpg)

**Figure 6. Two-dimensional analysis of Erk and pErk levels.** Joint distribution of pErk levels and total Erk levels under (A) control conditions and after (B) stimulation with 1 nM NFG for 30 minutes, along with the corresponding histograms (pooled data of *n* = 3 biological replicates, 4134 cells). Measured pErk levels, *s*<sub>1</sub>[pErk], and total Erk levels, *s*<sub>2</sub>([Erk] + [pErk]), are in arbitrary units of intensity. (B) Data measured after stimulation with 1 nM NGF have been fitted with a 2-component normal mixture model, of which the level set and the components weights are depicted. Using the mixture model the measured cells are assigned to the subpopulations and the corresponding contribution to the histogram are colour-coded. doi:10.1371/journal.pcbi.1003686.g006

## Discussion

Most multicellular organisms and microbial colonies consist of subpopulations with distinct biological functions. A study of mechanistic differences between these subpopulations and their functions is crucial for a holistic understanding of such complex biological systems. In this work, we introduced ODE constrained mixture models, a novel class of data analysis tools which can help to detect subpopulations and to analyse differences between them using population snapshot data. A simulation example illustrates that ODE-MMs possess a higher sensitivity than classical mixture models and ODE models, which originates from the simultaneous exploitation of distribution information and dependencies between experimental conditions. Furthermore, ODE-MMs provide mechanistic insights, e.g., estimates for kinetic parameters and abundance differences between subpopulations. In contrast to population models relying on a stochastic description of the individual cell [62–64] or ensemble models with parameter distributions [65,66], which can in principle also be used to analyse systems with different subpopulations, the computation time is significantly reduced. Furthermore, ODE-MMs are easily applicable as they merely rely on ODE models, for which numerical simulation as well as parameter estimation is well established [33].

To assess and illustrate the properties of ODE-MMs, we studied the response of primary sensory neurones to NGF stimulation. Therefore, we considered single-cell data for Erk1/2 phosphorylation levels collected by quantitative automated microscopy (QuAM) [13,18]. Using these data we performed model selection and found that the cell population consists of two subpopulations with different abundances of the NGF receptor TrkA. The responsive subpopulation with high TrkA levels constituted 30% of the overall population. By performing co-labelling experiments in which pErk1/2 and total Erk1/2 have been measured, we validated the existence of two subpopulations and found strong indications that TrkA is the causal factor for the population split. Thus, ODE-MMs enabled the inference of the population structure using only measurement of pErk1/2. Even the estimated size of the subpopulation with high TrkA expression was consistent with the newly collected as well as the literature data. This implies that ODE-MMs have the potential to significantly reduce the number of different measurements required to analyse heterogeneous populations and are even capable of predicting causal factors for the population split which have not been observed.

Beyond insights in subpopulation substructures, ODE-MM can improve estimates of kinetic parameters. This has been revealed by a profile likelihoods based uncertainty analysis of ODE-MMs for NGF-induced Erk1/2 phosphorylation. We found that kinetic parameters of ODE-MMs with two subpopulations are better identifiable than kinetic parameters of ODE-MMs without subpopulation structure. In many situations additional model complexity and an increased number of parameters results in increased parameter uncertainty. This is however not the case if the more complex model can exploit additional features of the data. In this case the data are effectively more informative for a more complex model resulting in a reduced parameter uncertainty. We are not aware of papers which reported this generic observation.

For our analysis of NGF-induced Erk1/2 phosphorylation we considered three pathway models. While these models consider key network motifs, such as an amplification cascade and a negative feedback loop, they are simple compared to the most detailed models (see [56–60] and references therein). These more detailed models have however been developed for cell lines and it is unclear how well they describe the signalling in primary sensory neurones. Furthermore, all three models we studied fit the experimental data and provided consistent predictions for the population structure, indicating a certain degree of robustness with respect to the pathway model. However, model extension may become necessary if the amount of available measurement data for primary sensory neurones increases, other stimuli are included or the biological question changes.

In this study we employed reaction rate equation models to constrained means and medians of mixture components. A further improvement of the sensitivity of ODE-MMs might be achieved by using ODE models which capture the cell-to-cell variability within subpopulations. Possible choices are linear noise approximations [27,28], effective mesoscopic rate equations [29,30] or moment equations [31,32]. These ODE models allow for an improved mechanistic description of the single cell dynamics, in particular the explicit consideration of intrinsic and/or extrinsic noise [67]. Intrinsic noise is related to the stochasticity of biochemical reactions. Extrinsic noise can originate from variation outside the considered signalling pathway and can be related to cell size, cell cycle state or the history of a cell. A variety of modelling approaches has been proposed for systems exhibiting intrinsic noise [1,62–64,68–70], extrinsic noise [51,65,71–73] and combinations of both [52,74,75]. The aforementioned deterministic, ODE-based approximation of these modelling approaches could build the basis for the description of the subpopulation dynamics. The consideration of more general ODE constraints describing the temporal correlation of stochastic processes [76,77] might even allow for the study of single-cell dynamics based on time-lapse microscopy data. In this context explicit models of the measurement noise might be beneficial, which have not been considered here, as the covariance was nevertheless a free parameter.

Consistent with our studied biological applications, we considered the special case of constant population sizes. There are however many situations in which spontaneous [5] or stimulus-induced cell-type transitions [5,10,78] occur. While such scenarios have not been considered in this manuscript and are not captured by our formulation, ODE-MMs can be generalised to studying such cell systems. Changing subpopulation sizes might be captured using parametric functions, splines or dynamic mechanistic models.

In our studies, ODE-MM parameters have been estimated by solving the maximum likelihood problem using multi-start local optimisation. The computational efficiency of this approach could probably be improved by using expectation maximisation (EM) algorithms [79]. Also the profile likelihood-based uncertainty analysis approach we used would profit from this. To obtain uncertainty bounds not only for parameters but also for model predictions, prediction profile likelihoods [80] or Bayesian methods [46] can be used.

The availability of pathway information in databases like KEGG [81], BioPath [82], BioCyc [83] and others is steadily increasing. We illustrated that integrating this information with snapshot data yields additional insights. ODE-MMs are however not only applicable to pure snapshot datasets but can be used to analyse mixed sets of snapshot and population average data (e.g., Western blots). Furthermore, we expect that the methods scale well. Solely, the numerical simulation of the ODE models is critical, but for this, efficient and reliable solvers exist which can easily handle systems with hundreds of chemical species [84]. Therefore, ODE-MMs should be applicable to large-scale datasets, such as transcriptomics, proteomics and metabolomics. This renders ODE-MMs potentially very valuable for the analysis of heterogeneous groups, not only cell populations, but also patient cohorts.

## Supporting Information

**Code S1 MATLAB code used for ODE constrained mixture modelling.** This zip-file contains the MATLAB code for the simulation example (conversion process) and the application example (NGF-induced Erk1/2 phosphorylation) presented in the paper. We provide implementations for the models, the parameter estimation, the uncertainty analysis and the model selection. In addition to the implementation, also all data and result files (.mat) are included. (ZIP)

**Supporting Information S1 Supplemental notes regarding the computational modelling.** This document provides a detailed description of the different pathway models, the parameter estimation, the uncertainty analysis and the model selection. Furthermore, numerical results of the parameter estimation, the uncertainty analysis and the model selection are listed and illustrated. (PDF)

## Acknowledgments

The authors are grateful for helpful comments and proof-reading by Fabian Fröhlich and Donna Ankerst.

## Author Contributions

Conceived and designed the experiments: JH CH TH. Performed the experiments: CH. Analyzed the data: JH CH. Contributed reagents/materials/analysis tools: TH. Wrote the paper: JH CH. Developed and implemented the analysis tools: JH CH FJT.

## References

1. Eldar A, Elowitz MB (2010) Functional roles for noise in genetic circuits. Nature 467: 1–7.

2. Ozbudak EM, Thattai M, Lim HN, Shraiman BI, van Oudenaarden A (2004) Multistability in the lactose utilization network of Escherichia coli. Nature 427: 737–740.

3. Nester EW, Stocker BA (1963) Biosynthetic latency in early stages of deoxyribonucleic acidtransformation in Bacillus subtilis. J Bacteriol 86: 785–796.

4. Arendt D (2008) The evolution of cell types in animals: emerging principles from molecular studies. Nature Reviews Genetics 9: 868–882.

5. Schroeder T (2011) Long-term single-cell imaging of mammalian stem cells. Nat Methods 8: 30–35.

6. Rimon N, Schuldiner M (2011) Getting the whole picture: combining throughput with content in microscopy. J Cell Sci 124: 3743–3751.

7. Pyne S, Hu X, Wang K, Rossin E, Lin T, et al. (2009) Automated high-dimensional ow cytometric data analysis. Proc Natl Acad Sci U S A 106: 8519–8124.

8. Taniguchi K, Kajiyama T, Kambara H (2009) Quantitative analysis of gene expression in a single cell by qPCR. Nature Methods 6: 503–506.

9. Taniguchi Y, Choi PJ, Li GW, Chen H, Babu M, et al. (2010) Quantifying E. coli proteome and transcriptome with single-molecule sensitivity in single cells. Science 329: 533–538.

10. Moignard V, Macaulay IC, Swiers G, Buettner F, Schütte J, et al. (2013) Characterization of transcriptional networks in blood stem and progenitor cells using high-throughput single-cell gene expression analysis. Nat Cell Biol 15: 363–372.

11. Ibàñez AJ, Fagerer SR, Schmidt AM, Urban PL, Jefimovs K, et al. (2013) Mass spectrometry-based metabolomics of single yeast cells. Proc Natl Acad Sci U S A 110: 8790–8794.

12. O’Neill K, Aghaeepour N, Špidlen J, Brinkman R (2013) Flow cytometry bioinformatics. PLoS Comput Biol 9: e1003365.

13. Andres C, Meyer S, Dina OA, Levine JD, Hucho T (2010) Quantitative automated microscopy (QuAM) elucidates growth factor specific signalling in pain sensitization. Molecular Pain 6: 1–16.

14. Cox C, Reeder JE, Robinson RD, Suppes SB, Wheeless LL (1988) Comparison of frequency distribution in ow cytometry. Cytometry 9: 291–298.

15. Bagwell B (1996) A journey through ow cytometric immunouorescence analyses – finding accurate and robust algorithms that estimate positive fraction distributions. Clin Immunol Newsletter 16: 33–37.

16. Lampariello F (2000) On the Kolmogorov-Smirnov statistical test for immunouorescence histogram comparison. Cytometry Part A 39: 179–188.

17. Lampariello F (2009) Ratio analysis of cumulatives for labeled cell quantification from immunouorescence histograms derived from cells expressing low antigen levels. Cytometry Part A 75A: 665–674.

18. Andres C, Hasenauer J, Allgöwer F, Hucho T (2012) Threshold-free population analysis identifies larger DRG neurons to respond stronger to NGF stimulation. PLoS ONE 7: e34257.

19. Andres C, Hasenauer J, Ahn HS, Joseph EK, Theis FJ, et al. (2013) Wound healing growth factor, basic FGF, induces Erk1/2 dependent mechanical hyperalgesia. Pain 154: 2216–2226.

20. Song C, Phenix H, Abedi V, Scott M, Ingalls BP, et al. (2010) Estimating the stochastic bifurcation structure of cellular networks. PLoS Comput Biol 6: e1000699.

21. Singh DK, Ku CJ, Wichaidit C, Steininger RJ, Wu LF, et al. (2010) Patterns of basal signaling heterogeneity can distinguish cellular populations with different drug sensitivities. Mol Syst Biol 6.

22. Isensee J, Diskar M, Waldherr S, Buschow R, Hasenauer J, et al. (2014) Pain modulators regulate the dynamics of PKA-RII phosphorylation in subgroups of sensory neurons. Journal of Cell Science 127: 216–229.

23. Schöberl B, Eichler-Jonsson C, Gilles ED, Muller G (2002) Computational modeling of the dynamics of the MAP kinase cascade activated by surface and internalized EGF receptors. Nat Biotechnol 20: 370–375.

24. Klipp E, Nordlander B, Krüger R, Gennemark P, Hohmann S (2005) Integrative model of the response of yeast to osmotic shock. Nat Biotechnol 23: 975–982.

25. Schöberl B, Pace EA, Fitzgerald JB, Harms BD, Xu L, et al. (2009) Therapeutically targeting ErbB3: A key node in ligand-induced activation of the ErbB receptor–PI3K axis. Science Signaling 2: ra31.

26. Bachmann J, Raue A, Schilling M, Böhm ME, Kreutz C, et al. (2011) Division of labor by dual feedback regulators controls JAK2/STAT5 signaling over broad ligand range. Mol Syst Biol 516.

27. Elf J, Ehrenbarg M (2003) Fast evaluation of uctuations in biochemical networks with the linear noise approximation. Genome Res 13: 2475–2484.

28. van Kampen NG (2007) Stochastic processes in physics and chemistry. Amsterdam: North-Holland, 3rd edition.

29. Grima R (2010) An effective rate equation approach to reaction kinetics in small volumes: Theory and application to biochemical reactions in nonequilibrium steady-state conditions. J Chem Phys 133.

30. Ramaswamy R, González-Segredo N, Sbalzarini I, Grima R (2012) Discreteness-induced concentration inversion in mesoscopic chemical systems. Nat Comm 3.

31. Engblom S (2006) Computing the moments of high dimensional solutions of the master equation. Appl Math Comp 180: 498–515.

32. Lee CH, Kim KH, Kim P (2009) A moment closure method for stochastic reaction networks. J Chem Phys 130: 134107.

33. Raue A, Schilling M, Bachmann J, Matteson A, Schelke M, et al. (2013) Lessons learned from quantitative dynamical modeling in systems biology. PLoS ONE 8: e74335.

34. Bäck T (1996) Evolutionary algorithms in theory and practice: evolution strategies, evolutionary programming, genetic algorithms. New York and Oxford: Oxford University Press.

35. Yang X (2010) Nature-inspired metaheuristic algorithms. Luniver Press, 2nd edition.

36. Kirkpatrick S, Gelatt Jr CD, M P Vecchi MP (1983) Optimization by simulated annealing. Science 220: 671–680.

37. Balsa-Canto E, Peifer M, Banga JR, Timmer J, Fleck C (2008) Hybrid optimization method with general switching strategy for parameter estimation. BMC Syst Biol 2.

38. Vaz A, Vicente L (2007) A particle swarm pattern search method for bound constrained global optimization. J Global Optim 39: 197–219.

39. Moles CG, Mendes P, Banga JR (2003) Parameter estimation in biochemical pathways: A comparison of global optimization methods. Genome Res 13: 2467–2474.

40. Banga JR (2008) Optimization in computational systems biology. BMC Syst Biol 2.

41. Weise T (2009) Global optimization algorithms: Theory and application. ebook, Nature Inspired Computation and Applications Laboratory (NICAL), University of Science and Technology, China. URL http://www.it-weise.de/.

42. Raue A, Kreutz C, Maiwald T, Bachmann J, Schilling M, et al. (2009) Structural and practical identifiability analysis of partially observed dynamical models by exploiting the profile likelihood. Bioinf 25: 1923–1929.

43. DiCiccio TJ, Efron B (1996) Bootstrap confidence intervals. Statist Sci 11: 189–228.

44. Joshi M, Seidel-Morgenstern A, Kremling A (2006) Exploiting the bootstrap method for quantifying parameter confidence intervals in dynamical systems. Metabolic Eng 8: 447–455.

45. Vyshemirsky V, Girolami MA (2008) Bayesian ranking of biochemical system models. Bioinf 24: 833–839.

46. Hug S, Raue A, Hasenauer J, Bachmann J, Klingmüller U, et al. (2013) High-dimensional Bayesian parameter estimation: Case study for a model of JAK2/STAT5 signaling. Mathematical Biosciences 246: 293–304.

47. Sisson SA, Fan Y, Tanaka MM (2007) Sequential Monte Carlo without likelihoods. Proc Natl Acad Sci U S A 104: 1760–1765.

48. Toni T, Welch D, Strelkowa N, Ipsen A, Stumpf MPH (2009) Approximate Bayesian computation scheme for parameter inference and model selection in dynamical systems. J R Soc Interface 6: 187–202.

49. Akaike H (1973) Information theory and an extension of the maximum likelihood principle. In: 2nd International Symposium on Information Theory, Tsahkadsor, Armenian SSR. Akademiai Kiado, volume 1, pp. 267–281.

50. Schwarz G (1978) Estimating the dimension of a model. Ann Statist 6: 461–464.

51. Hasenauer J, Waldherr S, Doszczak M, Radde N, Scheurich P, et al. (2011) Identification of models of heterogeneous cell populations from population snapshot data. BMC Bioinf 12.

52. Zechner C, Ruess J, Krenn P, Pelet S, Peter M, et al. (2012) Moment-based inference predicts bimodality in transient gene expression. Proc Nati Acad Sci U S A 109: 8340–8345.

53. Nicol GD, Vasko MR (2007) Unraveling the story of NGF-mediated sensitization of nociceptive sensory neurons: ON or OFF the Trks? Mol Interv 7: 26–41.

54. Julius D, Basbaum AI (2001) Molecular mechanisms of nociception. Nat 413: 203–210.

55. Fritsche-Guenther R, Witzel F, Sieber A, Herr R, Schmidt N, et al. (2011) Strong negative feedback from Erk to Raf confers robustness to MAPK signalling. Mol Syst Biol 7.

56. Brightman FA, Fell DA (2000) Differential feedback regulation of the MAPK cascade underlies the quantitative differences in EGF and NGF signalling in PC12 cells. FEBS Letters 482: 169–174.

57. Brown KS, Hill CC, Calero GA, Myers CR, Lee KH, et al. (2004) The statistical mechanics of complex signaling networks: Nerve growth factor signaling. Phys Biol 1: 184–195.

58. Sasagawa S, i Ozaki Y, Fujita K, Kuroda S (2005) Prediction and validation of the distinct dynamics of transient and sustained ERK activation. Nat Cell Biol 7: 365–373.

59. Fujioka A, Terai K, Itoh RE, Aoki K, Nakamura T, et al. (2006) Dynamics of the Ras/ERK MAPK cascade as monitored by uorescent probes. J Biol Chem 281: 8917–8926.

60. Kholodenko BN (2007) Untangling the signalling wires. Nat Cell Biol 9: 247–249.

61. Kashiba H, Noguchi K, Ueda Y, Senba E (1995) Coexpression of trk family members and low–affnity neurotrophin receptors in rat dorsal root ganglion neurons. Brain Res Mol Brain Res 30: 158–164.

62. Shahrezaei V, Swain PS (2008) Analytical distributions for stochastic gene expression. Proc Natl Acad Sci U S A 105: 17256–17261.

63. Shahrezaei V, Swain P (2008) The stochastic nature of biochemical networks. Curr Opin Biotechnol 19: 369–374.

64. Wilkinson DJ (2009) Stochastic modelling for quantitative description of heterogeneous biological systems. Nat Rev Genet 10: 122–133.

65. Spencer SL, Gaudet S, Albeck JG, Burke JM, Sorger PK (2009) Non-genetic origins of cell-to-cell variability in TRAIL-induced apoptosis. Nat 459: 428–433.

66. Hasenauer J, Waldherr S, Radde N, Doszczak M, Scheurich P, et al. (2010) A maximum likelihood estimator for parameter distributions in heterogeneous cell populations. Procedia Computer Science 1: 1649–1657.

67. Swain PS, Elowitz MB, Siggia ED (2002) Intrinsic and extrinsic contributions to stochasticity in gene expression. Proc Natl Acad Sci U S A 99: 12795–12800.

68. Munsky B, Trinh B, Khammash M (2009) Listening to the noise: random uctuations reveal gene network parameters. Mol Syst Biol 5.

69. Neuert G, Munsky B, Tan RZ, Teytelman L, Khammash M, et al. (2013) Systematic identification of signal-activated stochastic gene regulation. Science 339: 584–587.

70. Hasenauer J, Wolf V, Kazeroonian A, Theis FJ (2013) Method of conditional moments (MCM) for the chemical master equation. Journal of Mathematical Biology [Epub ahead of print].

71. Huh D, Paulsson J (2011) Non-genetic heterogeneity from stochastic partitioning at cell division. Nat Gen 43: 95–102.

72. Hilfinger A, Paulsson J (2011) Separating intrinsic from extrinsic uctuations in dynamic biological systems. Proc Nati Acad Sci U S A 109: 12167–12172.

73. Aldridge BB, Gaudet S, Lauffenburger DA, Sorger PK (2011) Lyapunov exponents and phase diagrams reveal multi-factorial control over TRAIL-induced apoptosis. Mol Syst Biol 7: 553.

74. Hasenauer J, Waldherr S, Doszczak M, Radde N, Scheurich P, et al. (2011) Analysis of heterogeneous cell populations: a density-based modeling and identification framework. J Process Control 21: 1417–1425.

75. Toni T, Tidor B (2013) Combined model of intrinsic and extrinsic variability for computational network design with application to synthetic biology. PLoS Comput Biol 9: e1002960.

76. Komorowski M, Costa MJ, Rand DA, Stumpf MPH (2011) Sensitivity, robustness, and identifiability in stochastic chemical kinetics models. Proc Natl Acad Sci U S A 108: 8645–8650.

77. Lestas I, Paulsson J, Ross NE, Vinnicombe G (2008) Noise in gene regulatory networks. IEEE Trans Autom Control 53: 189–200.

78. Heinrich S, Geissen E, Kamenz J, Trautmann S, Widmer C, et al. (2013) Determinants for robustness in spindle assembly checkpoint signalling. Nature Cell Biology 15: 1328–1339.

79. Dempster AP, Laird NM, Rubin DB (1977) Maximum likelihood from incomplete data via the EM algorithm. J R Stat Soc B 39: 1–38.

80. Kreutz C, Raue A, Timmer J (2012) Likelihood based observability analysis and confidence intervals for predictions of dynamic models. BMC Syst Biol 6.

81. Kanehisa M, Goto S, Furumichi M, Tanabe M, Hirakawa M (2010) KEGG for representation and analysis of molecular networks involving diseases and drugs. Nucleic Acids Res 38: D355–D360.

82. Reitz M, Sacher O, Tarkhov A, Trümbach D, Gasteiger J (2004) Enabling the exploration of biochemical pathways. Org Biomol Chem 2: 3226–3237.

83. Caspi R, Altman T, Dale JM, Dreher K, Fulcher CA, et al. (2010) The MetaCyc database of metabolic pathways and enzymes and the BioCyc collection of pathway/genome databases. Nucleic Acids Res 38: D473–D479.

84. Chen WW, Schoeberl B, Jasper PJ, Niepel M, Nielsen UB, et al. (2009) Input–output behavior of ErbB signaling pathways as revealed by a mass action model trained against dynamic data. Mol Syst Biol 5.

85. Kass RE, Raftery AE (1995) Bayes factors. J Am Stat Assoc 90: 773–795.

## Conversion notes

- Source: Hasenauer J, Hasenauer C, Hucho T, Theis FJ (2014) ODE Constrained Mixture Modelling: A Method for Unraveling Subpopulation Structures and Dynamics. PLoS Comput Biol 10(7): e1003686. doi:10.1371/journal.pcbi.1003686. CC BY 4.0.
- Floats are placed at paragraph boundaries: the Author Summary follows the Abstract; Figure 2 and Table 1 close the simulation example; Figure 4 follows the paragraph it interrupts in print.
- The reference-list font in the source PDF lacks the fl/ffi ligature glyphs (e.g. 'ow cytometry' for flow cytometry); references are transcribed as printed.
- Kept as printed: the Figure 4 caption names ℳ<sub>H1,2</sub>/ℳ<sub>H1,3</sub> for panel D, whose legend shows ℳ<sub>H3,2</sub>/ℳ<sub>H3,3</sub>.
- Code S1 (pcbi.1003686.s001.zip, the authors' MATLAB implementation and data) is not converted; it is described in the Supporting Information section.
