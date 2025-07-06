# ☀️ Solar Radiation Data

## Overview
Solar radiation data measures the electromagnetic energy from the sun reaching Earth's surface, fundamental for climate modeling, renewable energy applications, and environmental studies.

## Data Sources

### Primary Source: Open-Meteo Historical Weather API
- **URL**: https://open-meteo.com/en/docs/historical-weather-api?latitude=51.5085&longitude=-0.1257&hourly=shortwave_radiation
- **Coverage**: Historical weather data with high temporal resolution
- **Spatial Resolution**: Point-based data for London coordinates (51.5085°N, -0.1257°W)
- **Temporal Resolution**: Hourly data availability
- **Format**: JSON, CSV

## Data Description

### Solar Radiation Variables
- **Global Solar Radiation**: Total solar energy reaching surface
- **Direct Solar Radiation**: Direct beam radiation from sun
- **Diffuse Solar Radiation**: Scattered radiation from sky
- **Reflected Solar Radiation**: Radiation reflected from surfaces
- **UV Radiation**: Ultraviolet component of solar spectrum

### Data Characteristics
- **Geographic Focus**: London metropolitan area
- **Temporal Coverage**: Historical data available from 1940 onwards
- **Data Quality**: High-resolution meteorological reanalysis data
- **Update Frequency**: Real-time data with historical archives
- **Units**: Solar radiation in W/m² (watts per square meter)

## Environmental Significance
Solar radiation data is essential for:
- Solar energy resource assessment
- Climate change impact studies
- Agricultural crop modeling
- Building energy efficiency analysis
- Photosynthesis and ecosystem productivity
- UV exposure and health assessments
- Urban heat island effect studies

## Data Processing Notes
- Solar radiation values are non-negative
- Consider solar zenith angle and day length variations
- Account for cloud cover and atmospheric attenuation
- Quality control includes physical limit validation
- Seasonal and diurnal patterns are significant

## Usage Guidelines
1. **Data Access**: Use Open-Meteo API with London coordinates
2. **Preprocessing**: Apply solar geometry corrections and cloud adjustments
3. **Quality Checks**: Validate radiation values against theoretical maxima
4. **Integration**: Combine with temperature and humidity for energy balance analysis

## Related Variables
- Temperature (solar radiation is primary driver)
- Humidity (affects atmospheric transmission)
- Wind speed (influences convective heat transfer)
- Precipitation (cloud cover affects radiation)

---
*Data Category: Meteorological & Climate Factors*  
*Last Updated: July 2025* 