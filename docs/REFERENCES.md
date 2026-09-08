# Sources and reference material

The following sources informed the architecture and modelling approach.

| Source | Relevance |
|---|---|
| Internal: `CourtEdge_Beginner_Friendly_Build_Journey.docx` | Companion handbook containing the detailed step and code journey. |
| Klaassen, F.J.G.M. and Magnus, J.R. (2003). Forecasting the winner of a tennis match. *European Journal of Operational Research*, 148(2), 257–267. | Founding method for point-based, within-match forecasting; basis for the Markov baseline. |
| Klaassen, F.J.G.M. and Magnus, J.R. (2001). Are points in tennis independent and identically distributed? *Journal of the American Statistical Association*, 96(454), 500–509. | Evidence against a strictly constant point-win probability; motivates the non-i.i.d. Markov experiment. |
| Kovalchik, S. and Reid, M. (2019). A calibration method with dynamic updates for within-match forecasting of wins in tennis. *International Journal of Forecasting*, 35(2), 756–766. | Basis for the dynamic, phase-level calibration experiment. |
| Barnett, T., Brown, A. and Clarke, S. Developing a tennis model that reflects outcomes of tennis matches. Swinburne University. | Discusses applying a revised Markov model to index betting; informs the trading-rules framing. |
| Jeff Sackmann, `tennis_slam_pointbypoint` / `tennis_atp` / `tennis_wta` GitHub repositories. | Primary point-by-point, match and ranking data source (CC BY-NC-SA, non-commercial). |
| tennis-data.co.uk historical match odds. | Used only as an evaluation benchmark for calibration and market-comparison research. |
| LightGBM and XGBoost documentation. | Implementation reference for the learned probability model and meta-model. |
| DuckDB documentation. | Reference for the local analytical feature-and-replay store. |

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 21.
