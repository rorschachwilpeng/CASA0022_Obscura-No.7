# 🧠 Intelligent Data Management System & Environmental Prediction Framework

## Overview

This directory contains the Intelligent Data Management System and Environmental Prediction Variable Framework developed for the CASA0022 Obscura No.7 project. The system provides comprehensive data management solutions, supporting multi-dimensional environmental data collection, processing, analysis, and management.

## 📁 Directory Structure

```
ML_Models/
├── 🌍 environmental_prediction_framework/     # Environmental prediction framework
│   ├── meteorological_climate_factors/       # Meteorological and climate factors
│   ├── human_activities_socioeconomic_factors/ # Human activities and socioeconomic factors
│   └── geospatial_topographic_factors/       # Geospatial and topographic factors
├── 🧠 intelligent_data_manager.py            # Intelligent data manager main program
├── 📊 usage_example.py                       # Usage examples
├── 📋 requirements.txt                       # Dependency list
├── 🗂️ data_cache/                           # Data cache directory
├── 📈 metadata/                             # Metadata storage
└── 📝 README.md                             # This file
```

## 🎯 Key Features

### 1. Environmental Prediction Framework
- **Three-dimensional Data Classification**: Meteorological, socioeconomic, and geospatial
- **Standardized Data Sources**: Detailed English documentation for each data category
- **Data Source Mapping**: Clear data sources and acquisition methods
- **Environmental Significance**: Environmental prediction importance for each variable

### 2. Intelligent Data Manager
- **Automatic Data Download**: Support for multiple data formats (CSV, Excel, JSON, API)
- **Cache Management**: Intelligent caching strategy to avoid redundant downloads
- **Data Quality Checks**: Automatic data quality analysis and anomaly detection
- **Metadata Management**: Complete data lineage and version control
- **Automatic Scheduling**: Support for scheduled data updates and backups
- **Multi-format Support**: Unified data loading interface

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Examples
```bash
python usage_example.py
```

### 3. Use Data Manager
```python
from intelligent_data_manager import IntelligentDataManager

# Initialize
dm = IntelligentDataManager()

# Update all data
dm.update_all_data()

# Update data by category
dm.update_all_data(category='meteorological')

# Load data
df = dm.load_data('temperature_data')

# Generate report
report = dm.generate_report()
print(report)
```

## 📊 Environmental Prediction Framework Structure

### 🌤️ Meteorological and Climate Factors
- **Temperature**: Air temperature, surface water temperature, water column temperature
- **Humidity**: Relative humidity, absolute humidity
- **Wind Speed**: 10-meter height wind speed, wind direction
- **Atmospheric Pressure**: Sea level pressure, pressure gradient
- **Solar Radiation**: Global solar radiation, direct radiation
- **Precipitation**: Intensity, accumulation, duration, patterns
- **Sea Level**: Mean sea level, tidal variations

### 🏙️ Human Activities and Socioeconomic Factors
- **Land Use/Land Cover**: Urban development, agriculture, forestry, water bodies
- **Population Distribution**: Population density, age structure, population projections
- **Economic Activity Indicators**: GDP, GVA, per capita income
- **Railway Infrastructure**: Railway density, network connectivity
- **Quality of Life Indicators**: Life expectancy, health indicators

### 🏔️ Geospatial and Topographic Factors
- **Hydrological Network**: River density, watershed characteristics
- **Geology and Soil**: Soil types, soil moisture, geological structure
- **Vegetation and Water Body Health**: NDVI, NDWI, ecosystem indicators
- **Urban Flood Risk**: Flood-prone areas, drainage capacity

## 🔧 Configuration Instructions

### Data Source Configuration
The system automatically generates a `data_config.json` configuration file containing:
- Data source URLs and formats
- Update frequency settings
- API key configuration
- Caching strategy configuration

### Custom Data Sources
New data sources can be added by modifying the configuration file:
```json
{
  "name": "custom_data",
  "url": "https://your-data-source.com/api",
  "format": "csv",
  "update_frequency": "daily",
  "description": "Custom environmental data",
  "local_path": "custom_category/custom_data.csv",
  "category": "custom"
}
```

## 📈 Data Quality Management

The system provides automatic data quality checks:
- **Missing Value Detection**: Calculate missing value ratios
- **Duplicate Record Detection**: Identify duplicate data
- **Anomaly Detection**: Use IQR method to detect outliers
- **Data Integrity Validation**: Validate data format and structure

## 🔄 Automatic Scheduling Features

Support for background automatic operations:
- **Daily Data Updates**: Automatic update of all data sources at 02:00
- **Daily Backups**: Automatic data backup at 01:00
- **Weekly Cleanup**: Automatic cleanup of expired cache files
- **Failure Recovery**: Automatic retry of failed download tasks

## 📚 Documentation

Each data category includes detailed English README documentation containing:
- Data source introduction and links
- Data format and feature descriptions
- Environmental prediction significance
- Data processing recommendations
- Related variable relationships

## 🛠️ Development Guide

### Extending New Data Sources
1. Add data source definition in configuration file
2. Create README documentation in corresponding framework directory
3. Test data download and processing functionality

### Custom Data Processing
```python
# Custom data processing function
def custom_data_processor(df):
    # Data cleaning and transformation
    processed_df = df.dropna()
    return processed_df

# Use custom processor
dm = IntelligentDataManager()
df = dm.load_data('your_data_source')
processed_df = custom_data_processor(df)
```

## 🔍 Troubleshooting

### Common Issues
1. **API Key Error**: Check API key settings in configuration file
2. **Network Connection Issues**: Check network connection and proxy settings
3. **Insufficient Disk Space**: Run cache cleanup or increase storage space
4. **Data Format Error**: Check data source format settings

### Log Viewing
The system automatically generates log files:
```bash
tail -f ML_Models/data_manager.log
```

## 🤝 Contribution Guidelines

1. Follow existing code style and documentation format
2. Create issues for discussion before adding new features
3. Provide complete test cases
4. Update relevant documentation

## 📄 License

This project is part of the CASA0022 Obscura No.7 project and follows the overall project license agreement.

## 🙏 Acknowledgments

Thanks to all data source providers:
- UK Met Office Climate Data Portal
- Open-Meteo Historical Weather API
- London Datastore
- ONS (Office for National Statistics)

---

*Last Updated: July 2025*  
*Project: CASA0022 Obscura No.7 Environmental Prediction System* 