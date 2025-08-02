# PDSAI Project Documentation

## Project Overview

This project focuses on fetching TikTok data to compute gender gaps and compare to Facebook and Instagram Data. It uses population data to compute standardized rations for comparison. The processing pipeline includes:

1. **Data Cleaning**  
   Cleaning the raw data so all files are in the same format.

2. **Data Transformation**  
   Transform the data, adding computations for ratios, adding columns so files have same structure.

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
   LEVEL=city docker-compose up --build
   ```
   or in PowerShell:
   ```shell
   $env:LEVEL = "city"; docker-compose up --build
   ```

   Alternatively, override the following value in docker-compose.yaml.
   ```yaml
   environment:
      - LEVEL=${LEVEL:-country}
   ```

5. **Analysis**
Either run the analysis in the Jupyter notebooks in src/analyze_data or build you own analysis based on the final datasets stored in data/transformed.