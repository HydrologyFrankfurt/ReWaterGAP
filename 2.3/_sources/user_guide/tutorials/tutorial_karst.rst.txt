.. _tutorial_karst:

###################################################
Run ReWaterGAP with Karst (**Under Construction**)
###################################################

This tutorial introduces the modifications in ReWaterGAP for handling karst regions and explains the required input files, as well as the assessment methods.

************
Introduction
************

[Insert Introduction here]


*************************
Implemented Modifications
*************************

The following extensions and changes need to be made to the code:

Fraction of karstification 
##########################

A fraction of the continental area is defined as karst. For this fraction, the runoff component (R3) is treated as groundwater recharge.

Groundwater recharge factor (fg)
################################

The original calculation of *fg* has to be replaced by an externally provided input factor.

Semi-arid coarse-texture adjustment
###################################

A grid-cell-specific indicator allows special handling of (semi-)arid regions. If a semi-arid grid cell has *R<sub>gmax</sub> > 5 mm/d* (indicating coarse texture), groundwater recharge occurs only when precipitation exceeds **12.5 mm/d** (instead of being triggered solely by coarse texture).

Maximum groundwater recharge dataset
####################################

A dataset specifying the maximum possible groundwater recharge rate (mm/d) needs to be implemented

*************************
Input Files
*************************

ReWaterGAP requires additional input files for the karst extensions:

`G_ARIDCOARSE.UNF2` 
###################

- The input file for indicating coarse arid gird cells 
- Value: `1`
- Unit: [-]

.. figure:: ../../images/user_guide/tutorial/G_ARIDCOARSE.png

`G_GWRFACTOR.UNF0`
##################

- The input file for groundwater recharge factor 
- Range: `0 – 1`
- Unit: [-]

.. figure:: ../../images/user_guide/tutorial/G_GWRFACTOR.png

`G_KARSTFRAC.UNF0`
##################

- The input file for karst fraction 
- Range: `0 – 0.9`
- Unit: [-]

.. figure:: ../../images/user_guide/tutorial/G_KARSTFRAC.png

`G_GWRMAX.UNF2`
###############

- Specifies the maximum groundwater recharge rate.  
- The input file for gwr max 
- Range: `3 – 7`
- Unit: [mm/d]

.. figure:: ../../images/user_guide/tutorial/G_GWRMAX.png

*******************
Assessments
*******************

To evaluate the impact of the modifications, the following assessments are recommended:

Water balance
#############


Streamflow evaluation
#####################

Validate model outputs against observed streamflow
