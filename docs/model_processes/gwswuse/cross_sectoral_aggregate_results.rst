.. _cross_sectoral_aggregate_results:

################################
Cross-Sectoral Aggregate Results
################################

After calculating sector-specific results for consumptive uses, water withdrawals, returns, and net withdrawals from or towards groundwater and surface water, the sector-specific results for each variable are summed to derive cross-sectoral totals. To compute the aggregate cross-sectoral results, sector-specific results must be harmonized with regard to temporal resolution and unit consistency. This process involves initially summing results across the household, industrial production, thermal power, and livestock sectors, then dividing by 365 days and multiplying by the number of days in the month to standardize to units of :math:`{m}^{3}`:math:`{/}`:math:`{m}^{3}`{month}`. These values can then be combined with irrigation-specific results to finalize the aggregate cross-sectoral results.

Consumptive Wateruse
********************

.. math::
	CU_{tot}(y,m,id) = CU_{tot,irr}(y,m,id) + \frac{CU_{tot,dom}(y,id) + CU_{tot, man}(y,id) + CU_{tot,tp}(y,id) + CU_{tot,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


.. math::
	CU_{gw}(y,m,id) = CU_{gw,irr}(y,m,id) + \frac{CU_{gw,dom}(y,id) + CU_{gw, man}(y,id) + CU_{gw,tp}(y,id) + CU_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	CU_{sw}(y,m,id) = CU_{sw,irr}(y,m,id) + \frac{CU_{sw,dom}(y,id) + CU_{sw, man}(y,id) + CU_{sw,tp}(y,id) + CU_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


Wateruse
********
.. math::
	WU_{tot}(y,m,id) = WU_{tot,irr}(y,m,id) + \frac{WU_{tot,dom}(y,id) + WU_{tot,man}(y,id) + WU_{tot,tp}(y,id) + WU_{tot,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

.. math::
	WU_{gw}(y,m,id) = WU_{gw,irr}(y,m,id) + \frac{WU_{gw,dom}(y,id) + WU_{gw,man}(y,id) + WU_{gw,tp}(y,id) + WU_{gw,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

.. math::
	WU_{sw}(y,m,id) = WU_{sw,irr}(y,m,id) + \frac{WU_{sw,dom}(y,id) + WU_{sw,man}(y,id) + WU_{sw,tp}(y,id) + WU_{sw,liv}(y,id)}{365 d / year} * \frac{#days(m)}{month}

.. math::
	WU_{tot}(y,m,id) = WU_{tot,irr}(y,m,id) + WU_{tot,dom}(y,id) + WU_{tot,man}(y,id) + WU_{tot,tp}(y,id) + WU_{tot,liv}(y,id)

.. math::
	WU_{gw}(y,m,id) = WU_{gw,irr}(y,m,id) + WU_{gw,dom}(y,id) + WU_{gw,man}(y,id) + WU_{gw,tp}(y,id) + WU_{gw,liv}(y,id)

.. math::
	WU_{sw}(y,m,id) = WU_{sw,irr}(y,m,id) + WU_{sw,dom}(y,id) + WU_{sw,man}(y,id) + WU_{sw,tp}(y,id) + WU_{sw,liv}(y,id)

Returns
*******

.. math::
	RF_{tot}(y,m,id) = RF_{tot,irr}(y,m,id) + \frac{RF_{tot,dom}(y,id) + RF_{tot,man}(y,id) + RF_{tot,tp}(y,id) + RF_{tot,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	RF_{gw}(y,m,id) = RF_{gw,irr}(y,m,id) + \frac{RF_{gw,dom}(y,id) + RF_{gw,man}(y,id) + RF_{gw,tp}(y,id) + RF_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	RF_{sw}(y,m,id) = RF_{sw,irr}(y,m,id) + \frac{RF_{sw,dom}(y,id) + RF_{sw,man}(y,id) + RF_{sw,tp}(y,id) + RF_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}


Net Abstractions
****************

.. math::
	NA_{gw}(y,m,id) = NA_{gw,irr}(y,m,id) + \frac{NA_{gw,dom}(y,id) + NA_{gw, man}(y,id) + NA_{gw,tp}(y,id) + NA_{gw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}

.. math::
	NA_{sw}(y,m,id) = NA_{sw,irr}(y,m,id) + \frac{NA_{sw,dom}(y,id)+NA_{sw, man}(y,id) + NA_{sw,tp}(y,id) + NA_{sw,liv}(y,id)}{365 d/year} * \frac{#days(m)}{month}
