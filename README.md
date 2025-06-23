"""

      ======================================
                Pipeline Overview
      ======================================


--------------------------------------
   1. Population buckets generation
--------------------------------------
 ### reshape World Bank age-by-sex data into TikTok-style buckets ###

 
reference/worldbank_population_by_age.csv  
  → scripts/build_population_buckets.py  
          → reference/pop_by_country_buckets.csv  
                  → analysis/clean_pop_buckets.py  
                          → reference/pop_by_country_buckets_stripped.csv  


--------------------------------------
       2. TikTok data cleaning
--------------------------------------
### normalize raw TikTok export & map country codes ###

____ToDO_______

- edis output.csv in a way that makes it usable, get rid of 58k rows
- use countries.csv to get the region id for the country in output.csv

_______________
output.csv  
  → analysis/edit_output_tt.py  
          → outputs/tt_clean.csv  


--------------------------------------
       3. Gender-gap computation
--------------------------------------
### combine population buckets & cleaned TikTok data to compute penetration & gaps ###


reference/pop_by_country_buckets_stripped.csv + outputs/tt_clean.csv  
  → analysis/gender_gap_tables.py  
          → outputs/penetration_by_country.csv  
          → outputs/penetration_by_bucket.csv  
          → outputs/overall_gap.csv  
          → outputs/gap_by_country.csv  


--------------------------------------
   4. Penetration summary & ranking
--------------------------------------

### summarize country-level results & rank buckets by gap size ###


outputs/penetration_by_country.csv  
  → analysis/make_penetration_outputs.py  
          → outputs/penetration_summary.csv  
          → outputs/ranking_by_bucket.csv  


--------------------------------------
       5. Pipeline diagnostics
--------------------------------------
### run all steps with logging to catch failures ###


analysis/diagnose_gender_pipeline.py  
  → outputs/pipeline_diagnostics.txt
  
  
  
  """
