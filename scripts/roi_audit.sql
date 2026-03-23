SELECT 
  count(*) as total,
  countif(JSON_VALUE(prediction, '$.Outcome') = 'WIN') as wins,
  avg(SAFE_CAST(JSON_VALUE(prediction, '$."Confidence Score"') AS FLOAT64)) as avg_conf
FROM `hkjc-v2.hkjc_dw.mega_sweep_results`
