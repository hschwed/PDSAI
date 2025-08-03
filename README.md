# PDSAI Project Documentation

## Project Overview

This project focuses on fetching TikTok data to compute gender gaps and compare to Facebook and Instagram Data. It uses population data to compute standardized rations for comparison. The processing pipeline includes:

1. **Data Cleaning**  
   Cleaning the raw data so all files are in the same format.

2. **Data Transformation**  
   Transform the data, adding computations for ratios, adding columns so files have same structure.
   Remark: this currently only works on country level as we do not yet have population data matching subnational levels.

3. **Data Analysis and Visualization**  
   Analyzing the cleaned data, statistical tests, descriptive analysis. Creating visual representations of the data and models.

---
## Repository Structure
```
PDSAI/
├── config/                # Configuration files, specifying paths, apis,
├── data/                  # Raw and processed data
│   ├── cleaned/           # Data after running clean_data scripts
│   ├── raw/               # Raw input data
│   ├── transformed/       # Final output files
├── logging/               # Log file
├── poster_input/          # Input data for presentation session
├── src/                   # Source code for data processing and analysis
│   ├── analyze_data/    
│   ├── check_data/     
│   ├── clean_data/        
│   ├── get_data/          # source for TikTok API request
│   ├── transform_data/      
│   ├── utils/             # Helper functions
├── .dockerignore          # Docker ignore file
├── .env.example           # Example environment variables file
├── .gitignore             # Git ignore file
├── DockerFile             # Docker container setup
├── README.md              # Documentation
├── client.py              # Client interaction with local server endpoint
├── docker-compose.yaml    # Define container and configurations
├── main.py                # Main application entry point
└── requirements.txt       # Python dependencies list
```

---

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hschwed/PDSAI.git
   cd PDSAI

2.  **Copy .env.example:** 
    ```bash
    cp .env.example .env.

3.  **Fill in your credentials in .env**

4. **Build Docker image and start container**
    ```bash
    docker-compose up --build
    ```
   This will run the program and get country-level estimates from TikTok API. If you want to get different granularity level, specify the level first. Choose from: country, province, city or dma.
   Specify the level and run bash command:
   ```bash
    LEVEL="province"; docker compose run --build --service-ports --rm -it api-data-pipeline
   ```
   or in PowerShell:
   ```shell
    $env:LEVEL="province"; docker compose run --build --service-ports --rm -it api-data-pipeline
   ```

   Alternatively, override the following value in docker-compose.yaml.
   ```yaml
   environment:
      - LEVEL=${LEVEL:-country}
   ```

5. **Analysis**
   Either run the analysis in the Jupyter notebooks in src/analyze_data or build your own analysis based on the final datasets stored in data/transformed. Currently provided analyses are focused on country-level data

## Data Glossary
**Detail Level**
- Country: currently data available for 164 countries.
- Province: is a mid-level between city and country. What it refers to depends on the country, e.g. in Germany = Bundesländer, Canada = Province, US = States, Italy = Region, France = Departments etc. Currently province level data is available for 23 countries.
- City: Currently city level data is available for xx countries.
- DMA: Designated Market Area. It’s a geographic region used in the United States to define television and media markets.

**Age**
- ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
- age groups are pre-defined by TikTok. Other data (facebook, instagram) is adjusted to match the age buckets.
- Remark: due to security restrictions on TikTok side, data on age < 18 years is not reliable and should be disregarded.

**Location id**
- field used in the audience_estimate endpoint in TikTok API to make request
- defined by TikTok
- available information is different depending on level
- full json list of locations is downloaded from https://business-api.tiktok.com/portal/docs?id=1739311040498689. Remarkt: contrary to what is suggested in the documentation, the /tool/region endpoint does not provide a comprehensive list.

**Ratios**
- in the final transformed data, gender gap ratio is the female-to-male ratio
- standardized ratio = platform gender gap / population gender gap


