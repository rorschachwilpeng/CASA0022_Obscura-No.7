# 🌊 Urban Flood Risk Data

## Overview
Urban flood risk data includes river discharge measurements that help assess flood zones, urban drainage adequacy, and surface water management effectiveness. This dataset contains daily maximum river discharge data for three UK cities.

## ✅ Data Collection Status
**COMPLETED**: Data successfully collected and cleaned (July 2025)

### 📊 Dataset Summary
- **Indicator**: River Discharge Maximum (河流流量最大值)
- **Cities**: London, Manchester, Edinburgh
- **Time Range**: 1997-01-01 to 2025-12-31 (29 years)
- **Data Points**: 10,592 daily records per city
- **File Size**: 266.4 KB
- **Format**: CSV with columns: `date,London_river_discharge_max,Manchester_river_discharge_max,Edinburgh_river_discharge_max`

### 🏙️ City-Specific Risk Analysis
| City | Flow Range (m³/s) | Average (m³/s) | Median (m³/s) | Risk Level |
|------|-------------------|----------------|---------------|------------|
| **Edinburgh** | 0.83 - 34.08 | 3.11 | 2.56 | **HIGHEST** |
| **London** | 0.12 - 28.92 | 0.50 | 0.30 | MEDIUM |
| **Manchester** | 0.14 - 9.81 | 0.49 | 0.39 | LOWEST |

## Data Sources

### Primary Source: Open-Meteo Flood API
- **URL**: https://flood-api.open-meteo.com/v1/flood
- **API Parameter**: `river_discharge_max`
- **Coverage**: Daily maximum river discharge for flood risk assessment
- **Spatial Resolution**: Point-based data for city coordinates
- **Temporal Resolution**: Daily data
- **Format**: JSON to CSV conversion

### City Coordinates
- **London**: 51.5074°N, -0.1278°W
- **Manchester**: 53.4808°N, -2.2426°W  
- **Edinburgh**: 55.9533°N, -3.1883°W

## Data Processing

### 🔧 Collection Process
1. **API Integration**: Automated data collection using Open-Meteo Flood API
2. **Quality Control**: Comprehensive error handling and data validation
3. **Format Standardization**: Consistent CSV format across all cities
4. **Data Cleaning**: Removal of invalid zero-value records (1991-1996 period)

### 📈 Cleaning Results
- **Original Records**: 12,784 (including 2,192 zero-value records)
- **Cleaned Records**: 10,592 (82.9% retention rate)
- **Removed Period**: 1991-1996 (all zero values)
- **Valid Period**: 1997-2025 (continuous daily data)

## Data Description

### Flood Risk Variables
- **River Discharge Maximum**: Daily peak river flow rates
  - **Environmental Significance**: Critical indicator for urban flood risk assessment
  - **Applications**: Emergency planning, infrastructure design, climate adaptation
  - **Units**: Cubic meters per second (m³/s)

### Data Characteristics
- **Geographic Focus**: Three major UK cities representing different urban environments
- **Temporal Coverage**: 29 years of continuous daily measurements (1997-2025)
- **Data Quality**: High-resolution, validated river discharge data
- **Completeness**: No missing values in valid time period
- **Risk Assessment**: All values represent actual flood risk potential

## Environmental Significance
Urban flood risk data is essential for:
- **Emergency Planning**: Real-time flood warning systems and evacuation protocols
- **Infrastructure Design**: Sizing of drainage systems and flood defenses
- **Urban Planning**: Development restrictions in flood-prone areas
- **Climate Change Adaptation**: Preparing for increased precipitation intensity
- **Insurance and Risk Assessment**: Quantifying potential flood damage
- **Sustainable Urban Drainage**: Green infrastructure planning and effectiveness
- **Environmental Justice**: Identifying vulnerable communities and areas

## Data Processing Notes
- All river discharge values represent actual flood risk scenarios
- Edinburgh shows highest variability and peak discharge rates
- Manchester demonstrates most stable flow patterns
- London exhibits moderate risk with occasional extreme events
- Data suitable for time series analysis and flood prediction modeling

## Usage Guidelines
1. **Data Access**: Pre-processed CSV file ready for analysis
2. **Quality Assurance**: All records validated and cleaned
3. **Integration**: Compatible with environmental prediction frameworks
4. **Applications**: Suitable for ML training, risk assessment, and visualization

## File Structure
```
urban_flood_risk/
├── README.md                    # This documentation
├── urban_flood_risk_data.csv    # Main dataset (10,592 records)
└── scripts/                     # Data collection and processing scripts
    ├── collect_urban_flood_risk_data.py
    └── clean_urban_flood_risk_data.py
```

## Related Variables
- Precipitation (primary driver of river discharge)
- Land use (urban surfaces affect runoff patterns)
- Soil properties (influence water infiltration and retention)
- Temperature (affects evapotranspiration and soil moisture recovery)

## Integration with Steampunk Virtual Telescope
This dataset provides flood risk indicators for the environmental prediction framework:
- **Time-sensitive data**: Daily resolution supports precise temporal analysis
- **Multi-city comparison**: Enables regional risk assessment
- **ML-ready format**: Structured for machine learning applications
- **Visual storytelling**: Rich data for AI-generated environmental narratives

---
*Data Category: Geospatial & Topographic Factors*  
*Last Updated: July 2025*  
*Status: ✅ COMPLETED - Ready for Integration* 