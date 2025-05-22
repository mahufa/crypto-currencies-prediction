# Cryptocurrency Data Visualization Tool

## Description
This project is a Python-based tool that retrieves, caches, and processes real-time cryptocurrency market data from the CoinGecko API. It uses Pandas for data preprocessing and SQLAlchemy with SQLite for local data storage. The tool lays the foundation for future visualizations and advanced analytics.

## Features
- Retrieves live cryptocurrency market data via the CoinGecko API  
- Implements a custom caching mechanism to reduce redundant API calls  
- Stores data locally in an SQLite database using SQLAlchemy
- Processes and cleans data using Pandas  
- Designed for future integration of data visualizations

## Technologies
- Python  
- Pandas  
- Requests  
- SQLAlchemy  
- SQLite  

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mahufa/crypto-currencies-visualization.git
   ```
   
2. **Set up the environment using Anaconda**.  
   The required dependencies are listed in the `environment.yml` file.

   ```bash
   conda env create -f environment.yml
   conda activate <env_name>
   ```
   Replace <env_name> with the name of the environment specified in the environment.yml file.
   
4. **Run the project in Jupyter Notebook:**
   ```bash
   jupyter notebook
   ```
   Then open and explore the available .ipynb notebooks in the project directory.

---

### Future Enhancements

- Develop comprehensive data visualizations with libraries like Matplotlib
- Improve error handling

---

### License

This project is licensed under the MIT License.
