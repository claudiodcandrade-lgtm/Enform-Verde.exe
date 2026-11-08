# Protocol for prospective field validation

All pre-field predictions are experimental and must be frozen before the corresponding field measurements are collected or revealed. The software release and scientific validation are separate decisions.

1. Select AOIs, strata, crops, forest physiognomies, compartments and sampling units before fieldwork. Use spatially separated plots, farms or inventory clusters as the independent units.
2. Record the exact source SHA, app version, input geometry, acquisition dates, sensor/product, preprocessing, model ID and parameter file for each prediction. Export the prediction and uncertainty range before field results are entered.
3. Measure reference outcomes with documented protocols, units, depth, plot area, date, operator and instrument. For carbon compartments, preserve dry-mass conversions, allometry and soil bulk-density/coarse-fragment measurements. For agriculture, record crop, phenological stage, management and harvest outcome.
4. Hold out entire spatial units and, for crop forecasts, entire seasons/years. Never split pixels or repeated measurements from the same plot/farm across training and test partitions.
5. Calculate MAE, RMSE, bias, R² when meaningful, interval coverage and width. Report sample count as the number of distinct independent held-out units, alongside raw observation counts. Do not infer accuracy from software-contract or synthetic tests.
6. Preserve missing values and failed acquisitions. Do not replace unavailable field observations with literature values in the validation set.
7. Promote a model from experimental to validated only after independent review confirms source bytes, licensing, unit conversions, split integrity, uncertainty coverage and domain-specific performance. Keep the earlier pre-field predictions immutable.
