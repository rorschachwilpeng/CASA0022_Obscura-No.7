# 🌿 Vegetation & Water Health Data

## Overview
Vegetation and water health data include NDVI (Normalized Difference Vegetation Index) and NDWI (Normalized Difference Water Index) measurements, reflecting vegetation coverage, water body conditions, and overall ecosystem health.

## Data Sources

### Primary Source: Open-Meteo Historical Weather API
- **URL**: https://open-meteo.com/en/docs/historical-weather-api?latitude=51.5085&longitude=-0.1257&hourly=soil_moisture_7_to_28cm
- **Coverage**: Soil moisture data as proxy for vegetation health conditions
- **Spatial Resolution**: Point-based data for London coordinates (51.5085°N, -0.1257°W)
- **Temporal Resolution**: Hourly data availability
- **Format**: JSON, CSV

## Data Description

### Vegetation Health Variables
- **NDVI (Normalized Difference Vegetation Index)**: Vegetation density and health
- **NDWI (Normalized Difference Water Index)**: Water content in vegetation and water bodies
- **Soil Moisture (7-28cm)**: Root zone moisture supporting vegetation
- **Vegetation Coverage**: Percentage of green coverage per area
- **Ecosystem Health Indicators**: Biodiversity and habitat quality metrics

### Data Characteristics
- **Geographic Focus**: London metropolitan area and green spaces
- **Temporal Coverage**: Historical data available from 1940 onwards
- **Data Quality**: High-resolution environmental and vegetation data
- **Update Frequency**: Real-time soil moisture with periodic vegetation mapping
- **Units**: NDVI/NDWI values (-1 to +1), soil moisture in m³/m³

## Environmental Significance
Vegetation and water health data are essential for:
- **Urban Green Space Assessment**: Quantifying green infrastructure effectiveness
- **Biodiversity Monitoring**: Tracking ecosystem health and habitat quality
- **Carbon Sequestration Studies**: Measuring vegetation carbon storage capacity
- **Air Quality Improvement**: Evaluating vegetation's air purification services
- **Urban Heat Island Mitigation**: Assessing cooling effects of vegetation
- **Climate Change Adaptation**: Monitoring vegetation resilience to environmental stress
- **Sustainable Development Planning**: Supporting green city initiatives

## Data Processing Notes
- NDVI values range from -1 (water/snow) to +1 (dense vegetation)
- NDWI values help distinguish vegetation water content and water bodies
- Consider seasonal variations in vegetation growth and water availability
- Account for urban vegetation management and irrigation effects
- Quality control includes vegetation index validation and temporal consistency

## Usage Guidelines
1. **Data Access**: Use Open-Meteo API for soil moisture data, combine with satellite imagery for NDVI/NDWI
2. **Preprocessing**: Apply temporal averaging and vegetation index calculations
3. **Quality Checks**: Validate vegetation indices and seasonal patterns
4. **Integration**: Combine with climate and land use data for comprehensive ecosystem analysis

## Related Variables
- Precipitation (affects vegetation growth and water availability)
- Temperature (influences vegetation phenology and growth rates)
- Solar radiation (drives photosynthesis and vegetation productivity)
- Land use (urban planning affects vegetation distribution)

---
*Data Category: Geospatial & Topographic Factors*  
*Last Updated: July 2025* 