# 🏔️ Geology & Soil Data

## Overview
Geology and soil data provide information about geological types, soil characteristics, and soil depth at different layers, influencing water infiltration, runoff, ground stability, and surface environmental conditions.

## Data Sources

### Primary Source: Open-Meteo Historical Weather API
- **URL**: https://open-meteo.com/en/docs/historical-weather-api?latitude=51.5085&longitude=-0.1257&hourly=soil_moisture_0_to_7cm
- **Coverage**: Multi-layer soil moisture data for London area
- **Spatial Resolution**: Point-based data for London coordinates (51.5085°N, -0.1257°W)
- **Temporal Resolution**: Hourly data availability
- **Format**: JSON, CSV

## Data Description

### Soil Variables
- **Soil Depth 0-7cm**: Surface soil layer characteristics
  - **Environmental Significance**: 🔥 Surface thermal exchange and vegetation growth
  - **Applications**: Urban heat island effects, short-term environmental prediction
- **Soil Depth 7-28cm**: Root zone soil characteristics
  - **Environmental Significance**: 🌱 Root zone ecology and plant health
  - **Applications**: Vegetation survival rates, urban greening assessment
- **Soil Moisture Content**: Water content at different soil depths
- **Soil Type Classification**: Geological composition and soil texture
- **Permeability**: Water infiltration and drainage capacity

### Data Characteristics
- **Geographic Focus**: London metropolitan area
- **Temporal Coverage**: Historical data available from 1940 onwards
- **Data Quality**: High-resolution soil moisture and geological data
- **Update Frequency**: Real-time soil moisture monitoring
- **Units**: Soil moisture in m³/m³, depth in centimeters

## Environmental Significance
Geology and soil data are essential for:
- Urban heat island effect modeling (surface thermal exchange)
- Vegetation health assessment and urban greening planning
- Flood risk assessment (infiltration vs. runoff)
- Foundation stability analysis for construction
- Contamination and pollution migration studies
- Climate change adaptation (soil carbon storage)
- Ecosystem service evaluation

## Data Processing Notes
- Soil moisture values range from 0 to saturation point
- Consider seasonal variations and precipitation effects
- Account for urban soil compaction and modification
- Quality control includes physical property validation
- Spatial interpolation may be required for comprehensive coverage

## Usage Guidelines
1. **Data Access**: Use Open-Meteo API for multi-layer soil data
2. **Preprocessing**: Apply temporal averaging and depth-specific analysis
3. **Quality Checks**: Validate soil moisture ranges and geological consistency
4. **Integration**: Combine with precipitation and vegetation data for comprehensive analysis

## Related Variables
- Precipitation (affects soil moisture content)
- Temperature (influences evapotranspiration and soil thermal properties)
- Vegetation (root systems interact with soil layers)
- Land use (urban development affects soil properties)

---
*Data Category: Geospatial & Topographic Factors*  
*Last Updated: July 2025* 