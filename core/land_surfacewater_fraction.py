# -*- coding: utf-8 -*-
# =============================================================================
# This file is part of WaterGAP.

# WaterGAP is an opensource software which computes water flows and storages as
# well as water withdrawals and consumptive uses on all continents.

# You should have received a copy of the LGPLv3 License along with WaterGAP.
# if not see <https://www.gnu.org/licenses/lgpl-3.0>
# =============================================================================
""" Compute Land area fraction with or without reservoir."""
import numpy as np
from controller import configuration_module as cm
# For anthropogenic run , cm.ant=True , else naturalised run is activated
anthroprogenic = cm.ant
# Reservoirs are activated if cm.RESERVOIR_OPT="on", else they are deactivated
reservoir_operation = cm.RESERVOIR_OPT


def compute_landareafrac(landwater_frac, land_area_frac,
                         resyear_frac=None, res_year=None,
                         glores_frac_prevyear=None,
                         init_landfrac_res_flag=None):
    """
    Compute land area fraction.

    Parameters
    ----------
    landwater_frac : array
       Surface water body and  continental fractions  to compute land area fraction, Unit: [-]
    land_area_frac : array
        current land area fraction, Unit: [-]
    resyear_frac : array
        All Reservoir fraction considered between start and end reservoir year, Unit: [-]
    res_year : array
        Active reservoir year , Unit: [year]
    glores_frac_prevyear : array
       Global reservoir fraction of previous year, Unit: [-]
    init_landfrac_res_flag: boolean
        This Flag compute land area fraction at  start day of simulation  
        when reservoirs are active.

    Returns
    -------
    land_area_frac : array
        current land area fraction, Unit: [-]

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
    if anthroprogenic:
        if reservoir_operation:

            # Read in global reservoir fraction per year. This reservoir
            # fraction contains accumulated values per year, specifically
            # when a grid cell has more than one reservoir fraction (e.g.,
            # a new dam is built) but with diferernt outflow cells.
            glores_frac = resyear_frac.gloresfrac.sel(time=res_year).\
                values.astype(np.float64)
            # changing data dimension from (1,360,720) to (360,720)
            glores_frac = glores_frac[0]

            # ================================================================
            # Compute land area fraction at model start and subsequent years
            # ===============================================================
            if init_landfrac_res_flag:  # computed once
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
                glores_frac_change = np.zeros_like(land_area_frac)
            else:
                # Compute the change in global reservoir fraction every year to
                # adapt land area fraction.

                glores_frac_change = glores_frac - glores_frac_prevyear

                # In case there was already a reservoir fraction, adapt only
                # the changes else reservoir fraction increased from 0
                new_land_area_frac = \
                    np.where(glores_frac_prevyear > 0,
                             land_area_frac - (glores_frac_change/100),
                             land_area_frac - (glores_frac/100))

                #  Perform changes only if a new reservoir started operation
                land_area_frac = np.where(glores_frac_change > 0,
                                          new_land_area_frac, land_area_frac)

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
    landwater_frac : array
        variable which contains global lake area, regulated area and status.
        to compute global lake area with or without reservior being active

    Returns
    -------
    glo_lake_area : array
        Global lake area, Unit: [km^2]

    """
    global_lake_area = landwater_frac.global_lake_area[0].values.\
        astype(np.float64)

    if anthroprogenic:
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
