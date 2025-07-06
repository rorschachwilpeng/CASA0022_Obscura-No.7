# 🌊 Hydrological Network Data

## Overview
Hydrological network data includes river density and drainage systems, reflecting regional drainage capacity and water flow patterns essential for flood risk assessment and environmental modeling.

## Data Sources

### Primary Source: Open-Meteo Historical Weather API
- **URL**: https://open-meteo.com/en/docs/historical-weather-api?latitude=51.5085&longitude=-0.1257&hourly=soil_moisture_7_to_28cm
- **Coverage**: Soil moisture data as proxy for hydrological conditions
- **Spatial Resolution**: Point-based data for London coordinates (51.5085°N, -0.1257°W)
- **Temporal Resolution**: Hourly data availability
- **Format**: JSON, CSV

## Data Description

### Hydrological Variables
- **River Density**: Length of rivers per unit area (km/km²)
- **Drainage Network**: Stream order and connectivity patterns
- **Catchment Areas**: Watershed boundaries and drainage basins
- **Flow Capacity**: Channel capacity and discharge rates
- **Soil Moisture (7-28cm)**: Root zone soil moisture content

### Data Characteristics
- **Geographic Focus**: London metropolitan area and Thames basin
- **Temporal Coverage**: Historical data available from 1940 onwards
- **Data Quality**: High-resolution hydrological and soil data
- **Update Frequency**: Real-time soil moisture with static drainage network
- **Units**: River density in km/km², soil moisture in m³/m³

## Environmental Significance
Hydrological network data is essential for:
- Flood risk assessment and early warning systems
- Urban drainage system design and capacity planning
- Water resource management and allocation
- Ecosystem health monitoring (riparian habitats)
- Climate change impact assessment (changing precipitation patterns)
- Sustainable urban planning and green infrastructure
- Water quality monitoring and pollution control

## Data Processing Notes
- River density values are continuous and non-negative
- Consider seasonal variations in soil moisture and flow
- Account for urban development impacts on natural drainage
- Quality control includes hydrological validation
- Spatial interpolation may be required for ungauged areas

## Usage Guidelines
1. **Data Access**: Use Open-Meteo API for soil moisture data
2. **Preprocessing**: Apply temporal averaging and spatial interpolation
3. **Quality Checks**: Validate hydrological patterns and seasonal consistency
4. **Integration**: Combine with precipitation and land use data for comprehensive analysis

## Related Variables
- Precipitation (drives hydrological processes)
- Land use (affects runoff and infiltration)
- Temperature (affects evapotranspiration)
- Soil properties (influence water retention and drainage)

---
*Data Category: Geospatial & Topographic Factors*  
*Last Updated: July 2025* 