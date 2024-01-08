# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 19:09:21 2022.

@author: nyenah
"""
import numpy as np
from controller import configuration_module as cm
# For anthropogenic run , cm.ant=True , else naturalised run is activated
anthroprogenic = cm.ant
# Reservoirs are activated if cm.reservior_opt="on", else they are deactivated
reservoir_operation = cm.reservior_opt


def compute_landareafrac(landwater_frac, land_area_frac,
                         resyear_frac=None, res_year=None,
                         glores_frac_prevyear=None):
    """
    Compute land area fraction.

    Parameters
    ----------
    landwater_frac : array
        DESCRIPTION.
    resyear_frac : Tarray
        DESCRIPTION.
    res_year : array
        DESCRIPTION.
    glores_frac_prevyear : array
        DESCRIPTION.

    Returns
    -------
    land_area_frac : TYPE
        DESCRIPTION.

    """
    # continental fraction
    cont_frac = landwater_frac.contfrac.values.astype(np.float64)

    # regulate lake
    reglake_frac = landwater_frac.reglak[0].values.astype(np.float64)

    # Global lake
    glowet_frac = landwater_frac.glowet[0].values.astype(np.float64)

    # Global wetland
    glolake_frac = landwater_frac.glolak[0].values.astype(np.float64)

    # local wetland
    locwet_frac = landwater_frac.locwet[0].values.astype(np.float64)

    # local lake
    loclake_frac = landwater_frac.loclak[0].values.astype(np.float64)

    if anthroprogenic is False:
        # regulated lakes becomes global lakes (global lake fraction is
        # increased by regulated lake)
        # Note!!! regulated lakes are found in global resevoir
        glolake_frac += reglake_frac

        land_area_frac = (cont_frac - (glolake_frac + glowet_frac +
                                       loclake_frac + locwet_frac))/100

        land_area_frac[land_area_frac < 0] = 0

        return land_area_frac
    # =========================================================================
    #     Resevoirs
    # =========================================================================
    if anthroprogenic is True:
        if reservoir_operation is True:

            # Read in global reservoir fraction per year. This reservoir
            # fraction contains accumulated values per year, specifically
            # when a grid cell has more than one reservoir fraction (e.g.,
            # a new dam is built) but with diferernt outflow cells.
            glores_frac = resyear_frac.glores_frac.sel(time=res_year).\
                values.astype(np.float64)
            # changing data dimension from (1,360,720) to (360,720)
            glores_frac = glores_frac[0]

            # ================================================================
            # Compute land area fraction at model start and subsequent years
            # ===============================================================
            if res_year == cm.start.split('-')[0]:  # computed once
                # Read in local reservior.
                locres_frac = landwater_frac.locres[0].values.astype(np.float64)
                # local reservoir are added to local lakes based on section 4.1
                # of Müller Schmied et al. (2021)
                loclake_frac += locres_frac

                land_area_frac = (cont_frac - (glolake_frac + glowet_frac +
                                               loclake_frac + locwet_frac +
                                               glores_frac))/100

                land_area_frac[land_area_frac < 0] = 0

                # Change in global reservoir fraction (needed to adapt resevoir
                # storage and land area fraction.
                # see function adapt_glores_storage in module
                # land_surfacewater_fraction_init.py)
                glores_frac_change = 0
            else:
                # Compute the change in global reservoir fraction every year to
                # adapt land area fraction. The numpy equivalent of the if else
                # statement is written below.

                # if glores_frac_prevyear == 0:
                #     glores_frac_change = glores_frac
                # elif glores_frac > glores_frac_prevyear:
                #     # In this case a grid cell has more than one reservoir
                #     # fraction but different operational year
                #     glores_frac_change = glores_frac - glores_frac_prevyear
                # else:
                #     glores_frac_change = 0

                mask_zero = glores_frac_prevyear == 0
                mask_greater = glores_frac > glores_frac_prevyear
                diff = glores_frac - glores_frac_prevyear

                glores_frac_change = np.where(mask_zero, glores_frac,
                                              np.where(mask_greater, diff, 0))

                # Recompute land area fraction to account for the changes in
                #  reservoir fraction.
                land_area_frac = land_area_frac - (glores_frac_change/100)

                land_area_frac[land_area_frac < 0] = 0

            return land_area_frac, glores_frac_change
        else:
            # regulated lakes becomes global lakes (global lake fraction is
            # increased by regulated lake)
            # Note!!! regulated lakes are found in global resevoir

            glolake_frac += reglake_frac

            land_area_frac = (cont_frac - (glolake_frac + glowet_frac +
                                           loclake_frac + locwet_frac))/100

            land_area_frac[land_area_frac < 0] = 0

            return land_area_frac


def get_glolake_area(landwater_frac):
    """
    Get global lake area.

    Parameters
    ----------
    static_data : TYPE
        DESCRIPTION.

    Returns
    -------
    glo_lake_area : TYPE
        DESCRIPTION.

    """
    global_lake_area = landwater_frac.global_lake_area[0].values.\
        astype(np.float64)

    if anthroprogenic is True:
        if reservoir_operation is False:
            # Add reservoir area to global lake area in case of regulated lake
            regulated_lake_status = landwater_frac.regulated_lake_status.values
            reservior_and_regulated_lake_area = \
                landwater_frac.reservoir_and_regulated_lake_area[0].values.\
                astype(np.float64)

            glo_lake_area = np.where(regulated_lake_status == 1, global_lake_area +
                                     reservior_and_regulated_lake_area,
                                     global_lake_area)
        else:
            glo_lake_area = global_lake_area
    else:
        # Add reservoir area to global lake area in case of regulated lake
        regulated_lake_status = landwater_frac.regulated_lake_status.values
        reservior_and_regulated_lake_area = \
            landwater_frac.reservoir_and_regulated_lake_area[0].values.\
            astype(np.float64)

        glo_lake_area = np.where(regulated_lake_status == 1, global_lake_area +
                                 reservior_and_regulated_lake_area,
                                 global_lake_area)
    return glo_lake_area
