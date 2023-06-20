# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 15:32:29 2023

@author: nyenah
"""

if (G_dailyRemainingUse[n] > 1.e-12) {
    // Only update NAg if WUsi is existent
    if (G_withdrawalIrrigFromSwb[n] > 0.) {
        eff = G_consumptiveUseIrrigFromSwb[n] / G_withdrawalIrrigFromSwb[n];
        frgi = G_fractreturngw_irrig[n];
        factor = 1 - (1 - frgi) * (1 - eff);
        WUsiNew = 1 / factor * (G_withdrawalIrrigFromSwb[n] * factor - G_dailyRemainingUse[n]);
        if (WUsiNew < 0.) {
            // WUsiNew is below zero, when dailyRemainingUse is bigger than the estimated partion
            // of NAs from Irrigation
            WUsiNew = 0.;
            // unsatisfiedNAsfromirrig is needed to scale the reintroduction of returnflows in NAg
            G_unsatisfiedNAsFromIrrig[n] += G_withdrawalIrrigFromSwb[n] * factor;
            G_unsatisfiedNAsFromOtherSectors[n] += G_dailyRemainingUse[n] - (G_withdrawalIrrigFromSwb[n] * factor);
        } else { // unsatisfied use stems solely from irrigation
            G_unsatisfiedNAsFromIrrig[n] += G_dailyRemainingUse[n];
        };
        returnflowChange = (frgi * (1 - eff) * (WUsiNew - G_withdrawalIrrigFromSwb[n]));
        G_reducedReturnFlow[n] += returnflowChange;
        NAgnew = G_dailydailyNUg[n] - returnflowChange;
        G_dailyRemainingUse[n] = 0.;
        return NAgnew;
    } else {
        G_unsatisfiedNAsFromOtherSectors[n] += G_dailyRemainingUse[n];
        return G_dailydailyNUg[n];
    }
} else if (G_dailyRemainingUse[n] < -1.e-12 ) {
    dailyRemainingUseFromIrrig = G_dailyRemainingUse[n] + G_unsatisfiedNAsFromOtherSectors[n];
    if (dailyRemainingUseFromIrrig < 0.) {
        G_unsatisfiedNAsFromOtherSectors[n] = 0.;
    } else {
        G_unsatisfiedNAsFromOtherSectors[n] += G_dailyRemainingUse[n];
        G_dailyRemainingUse[n] = 0.;
        return G_dailydailyNUg[n];
    }
    if (G_unsatisfiedNAsFromIrrig[n] == 0.){
        // this if clause is catching cases where reduced return flows are tried to be reintroduced, which aren't
        // existing. This can happen in rare cases of numerical inaccuracies.
        G_dailyRemainingUse[n] = 0.;
        return G_dailydailyNUg[n];
    }
    reintroducedRatio = (dailyRemainingUseFromIrrig / G_unsatisfiedNAsFromIrrig[n]);
    if (reintroducedRatio < -1.){
        reintroducedRatio = -1.;
        dailyRemainingUseFromIrrig = G_unsatisfiedNAsFromIrrig[n] * -1.;
    }
    returnflowChange =  (reintroducedRatio * G_reducedReturnFlow[n]);

    G_unsatisfiedNAsFromIrrig[n] += dailyRemainingUseFromIrrig;
    G_reducedReturnFlow[n] += returnflowChange;
    NAgnew = G_dailydailyNUg[n] - returnflowChange;
    G_dailyRemainingUse[n] = 0.;
    return NAgnew;
}
else {
    return G_dailydailyNUg[n];
}
}