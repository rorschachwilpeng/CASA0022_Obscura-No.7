# 💧 Humidity Data

## Overview
Humidity data measures the amount of water vapor in the atmosphere, which is crucial for understanding weather patterns, human comfort, and environmental conditions.

## Data Sources

### Primary Source: Open-Meteo Historical Weather API
- **URL**: https://open-meteo.com/en/docs/historical-weather-api?latitude=51.5085&longitude=-0.1257&hourly=relative_humidity_2m
- **Coverage**: Historical weather data with high temporal resolution
- **Spatial Resolution**: Point-based data for London coordinates (51.5085°N, -0.1257°W)
- **Temporal Resolution**: Hourly data availability
- **Format**: JSON, CSV

## Data Description

### Humidity Variables
- **Relative Humidity**: Percentage of water vapor relative to saturation capacity
- **Absolute Humidity**: Actual water vapor content in the air (g/m³)
- **Specific Humidity**: Water vapor mass per unit mass of air
- **Dew Point**: Temperature at which air becomes saturated

### Data Characteristics
- **Geographic Focus**: London metropolitan area
- **Temporal Coverage**: Historical data available from 1940 onwards
- **Data Quality**: High-resolution meteorological reanalysis data
- **Update Frequency**: Real-time data with historical archives
- **Units**: Relative humidity in percentage (%), absolute humidity in g/m³

## Environmental Significance
Humidity data is essential for:
- Weather prediction and atmospheric modeling
- Human comfort and health assessments
- Agricultural irrigation planning
- Building ventilation and energy efficiency
- Air quality monitoring
- Ecosystem water balance studies
- Urban heat island effect analysis

## Data Processing Notes
- Relative humidity values range from 0-100%
- Consider diurnal variations (daily cycles)
- Seasonal patterns significantly affect humidity levels
- Quality control includes validation against physical limits
- Missing data interpolation may be required

## Usage Guidelines
1. **Data Access**: Use Open-Meteo API with London coordinates
2. **Preprocessing**: Apply temporal aggregation (hourly to daily/monthly)
3. **Quality Checks**: Validate humidity ranges and seasonal consistency
4. **Integration**: Combine with temperature and pressure data for comprehensive analysis

## Related Variables
- Temperature (inversely related to relative humidity)
- Precipitation (humidity is a precursor to precipitation)
- Wind speed (affects humidity distribution)
- Solar radiation (influences evaporation and humidity)

---
*Data Category: Meteorological & Climate Factors*  
*Last Updated: July 2025* 