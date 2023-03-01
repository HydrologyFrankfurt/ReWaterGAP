.. _leafareaindex:

Leaf Area Index 
+++++++++++++++++++
Leaf Area index consists of two separate modules.

.. _parallel_lai:

1. Parallel Leaf Area Index 
============================
This module contains a daily leaf area indexing method that computes the leaf area index per grid cell. This function is vectorized to compute the LAI parallelly for all grid cells, using the „numpy.vectorize“ function. For further information on the function see: https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html

.. autofunction:: parallel_leaf_area_index.daily_leaf_area_index
     
2. Compute Leaf Area Index 
============================
This module consist of a class and related method(s) which calls the vectorized daily leaf area index from the
:ref:`Parallel Lead Area Index <parallel_lai>` module.
The variables *days,cum_precipitation and growth_status* are updated daily.

.. autoclass:: leafareaindex.LeafAreaIndex
    :members:
