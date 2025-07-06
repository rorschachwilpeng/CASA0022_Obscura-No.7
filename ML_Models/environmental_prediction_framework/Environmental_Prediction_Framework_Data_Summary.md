# Environmental Prediction Framework Data Summary

## 📊 Data Collection Overview

| Dimension | Hydrological Network | Geology Soil | Urban Flood Risk | Vegetation Water Health | Life Expectancy | Population Distribution | Rail Infrastructure | Atmospheric Pressure | Humidity | NO2 | Precipitation | Solar Radiation | Temperature | Wind Speed |
|-----------|---------------------|--------------|------------------|-------------------------|-----------------|------------------------|-------------------|---------------------|----------|-----|---------------|-----------------|-------------|------------|
| **Geospatial Topographic Factors** | **12,606 records**<br/>1991-01-01 to 2025-07-05<br/>Open-Meteo API | **12,606 records**<br/>1991-01-01 to 2025-07-05<br/>Open-Meteo API | **10,593 records**<br/>1997-01-01 to 2025-12-31<br/>Open-Meteo Flood API | **12,606 records**<br/>1991-01-01 to 2025-07-05<br/>Open-Meteo API | - | - | - | - | - | - | - | - | - | - |
| **Human Activities Socioeconomic Factors**<br/>*(interpolation completed)* | - | - | - | - | **81 records**<br/>2020-2100<br/>Met Office + interpolation | **81 records**<br/>2020-2100<br/>Met Office + interpolation | **81 records**<br/>2020-2100<br/>Met Office + interpolation | - | - | - | - | - | - | - |
| **Meteorological Climate Factors** | - | - | - | - | - | - | - | **12,785 records**<br/>1991-01-01 to 2025-12-31<br/>Open-Meteo API | **12,785 records**<br/>1991-01-01 to 2025-12-31<br/>Open-Meteo API | **4,749 records**<br/>2013-01-01 to 2025-12-31<br/>Open-Meteo API | **12,785 records**<br/>1991-01-01 to 2025-12-31<br/>Open-Meteo API | **12,785 records**<br/>1991-01-01 to 2025-12-31<br/>Open-Meteo API | **12,785 records**<br/>1991-01-01 to 2025-12-31<br/>Open-Meteo API | **12,785 records**<br/>1991-01-01 to 2025-12-31<br/>Open-Meteo API |

---

## 📈 Detailed Data Statistics

### 🌍 Geospatial Topographic Factors (4 sub-dimensions)
- **Data Source**: Open-Meteo Historical Weather API
- **Spatial Coverage**: Three UK cities (London, Manchester, Edinburgh)
- **Data Characteristics**: Annual segmented collection, daily average values

| Sub-dimension | Variable Type | Data Volume | Time Range | File Size |
|---------------|---------------|-------------|------------|-----------|
| Hydrological Network | Reference ET₀ (Reference Evapotranspiration) | 12,606 records | 1991-01-01 to 2025-07-05 | 773KB |
| Geology Soil | Soil Temperature 0-7cm (Shallow Soil Temperature) | 12,606 records | 1991-01-01 to 2025-07-05 | 736KB |
| Urban Flood Risk | River Discharge Maximum (Maximum River Flow) | 10,593 records | 1997-01-01 to 2025-12-31 | 266KB |
| Vegetation Water Health | Soil Moisture 7-28cm (Root Zone Soil Moisture) | 12,606 records | 1991-01-01 to 2025-07-05 | 760KB |

### 👥 Human Activities Socioeconomic Factors (3 sub-dimensions) - **Interpolation Completed**
- **Data Source**: [Met Office Climate Data](https://climate-themetoffice.hub.arcgis.com/)
- **Spatial Coverage**: Three UK cities (London, Manchester, Edinburgh)
- **Processing Method**: Original 9 data points (10-year intervals) → Interpolated to 81 data points (annual intervals)

| Sub-dimension | Variable Type | Data Volume | Time Range | File Size |
|---------------|---------------|-------------|------------|-----------|
| Life Expectancy | Life Expectancy (Expected Lifespan) | 81 records | 2020-2100 | 1.7KB |
| Population Distribution | Population Growth Rate (Population Growth Rate) | 81 records | 2020-2100 | 2.5KB |
| Rail Infrastructure | Railway Line Density (Railway Line Density) | 81 records | 2020-2100 | 2.6KB |

### 🌡️ Meteorological Climate Factors (7 sub-dimensions)
- **Data Source**: Open-Meteo Historical Weather API
- **Spatial Coverage**: Three UK cities (London, Manchester, Edinburgh)
- **Data Characteristics**: Daily observation data, including 2025 extended simulation data

| Sub-dimension | Variable Type | Data Volume | Time Range | File Size |
|---------------|---------------|-------------|------------|-----------|
| Atmospheric Pressure | Atmospheric Pressure | 12,785 records | 1991-01-01 to 2025-12-31 | 723KB |
| Humidity | Relative Humidity | 12,785 records | 1991-01-01 to 2025-12-31 | 339KB |
| NO2 | Nitrogen Dioxide Concentration | 4,749 records | 2013-01-01 to 2025-12-31 | 190KB |
| Precipitation | Precipitation | 12,785 records | 1991-01-01 to 2025-12-31 | 289KB |
| Solar Radiation | Solar Radiation/Evapotranspiration | 12,785 records | 1991-01-01 to 2025-12-31 | 335KB |
| Temperature | Temperature | 12,785 records | 1991-01-01 to 2025-12-31 | 321KB |
| Wind Speed | Wind Speed | 12,785 records | 1991-01-01 to 2025-12-31 | 330KB |

---

## 🔍 Data Quality Description

### ✅ Data Completeness
- **Geospatial Data**: 34.5 years of continuous historical data, perfectly aligned across three cities
- **Socioeconomic Data**: 81 years of future projection data, processed with interpolation completion
- **Meteorological Data**: 35 years of continuous historical + prediction data, NO2 data starts from 2013

### 📊 Data Format Consistency
- **Column Format**: `date, London_[variable], Manchester_[variable], Edinburgh_[variable]`
- **Date Format**: YYYY-MM-DD (ISO 8601 standard)
- **Data Type**: Numerical values, ready for machine learning model implementation

### 🌟 Data Application Value
- **Broad Time Coverage**: Spanning historical, current, and future time periods
- **Complete Dimensions**: Full coverage of geographical, social, and meteorological environmental factors
- **Spatial Comparison**: Three-city data supports regional variation analysis
- **Predictive Modeling**: Suitable for Obscura-No.7 telescope environmental prediction framework

---

*Data Generation Date: July 6, 2025*  
*Total Data Volume: ~2.9MB, 14 sub-dimensions, covering 1991-2100* 