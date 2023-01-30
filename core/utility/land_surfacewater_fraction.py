# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 19:09:21 2022.

@author: nyenah
"""
import numpy as np
from controller import configuration_module as cm

anthroprogenic = cm.ant


def get_landareafrac(static_data):
    """
    Get lAnd area fraction.

    Parameters
    ----------
    static_data : TYPE
        DESCRIPTION.

    Returns
    -------
    landAreaFrac : TYPE
        DESCRIPTION.

    """
    switch_off_swb = 0

    # continental fraction
    cont_frac = static_data.contfrac.values

    # regulate lake
    reglake_frac = static_data.reglak[0].values

    # Global lake
    glowet_frac = static_data.glowet[0].values

    # Global wetland
    glolake_frac = static_data.glolak[0].values

    # local wetland
    locwet_frac = static_data.locwet[0].values

    # local lake
    loclake_frac = static_data.loclak[0].values

    # global and local reservior
    if anthroprogenic is True:
        glores_frac = static_data.res[0].values
        locres_frac = static_data.locres[0].values
        # local reservoir are added to local lakes based on section 4.1 of
        # Müller Schmied et al. (2021)
        loclake_frac += locres_frac
    else:
        # regulated lakes becomes global lakes (global lake fraction is
        # increased by regulated lake)
        glolake_frac += reglake_frac
        glores_frac = switch_off_swb

    # Note!!!
    # regulated lakes are found in global resevoiur
    land_area_frac = (cont_frac - (glolake_frac + glowet_frac + loclake_frac +
                                   locwet_frac + glores_frac))/100
    return land_area_frac


def get_glolake_area(static_data):
    global_lake_area = static_data.global_lake_area.values

    if anthroprogenic is True:
        pass
    else:
        regulated_lake_status = static_data.regulated_lake_status.values
        reservior_and_regulated_lake_area = \
            static_data.reservoir_and_regulated_lake_area.values

        glo_lake_area = np.where(regulated_lake_status == 1, global_lake_area +
                                 reservior_and_regulated_lake_area,
                                 global_lake_area)
    return glo_lake_area
