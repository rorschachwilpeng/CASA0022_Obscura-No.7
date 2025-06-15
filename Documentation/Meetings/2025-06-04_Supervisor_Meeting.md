# Meeting with Supervisor - June 4, 2025

## 📋 Meeting Details
- **Date**: June 4, 2025
- **Project**: Obscura No.7
- **Participants**: Student, Supervisor Valerio
- **Topic**: Hardware Architecture, Interaction Methods & Research Positioning

---

## 🔧 Current Hardware Architecture Review

| Component | Current Purpose | Status |
|-----------|----------------|---------|
| Raspberry Pi 4 | Main controller, system operation, display control | ✅ Implemented |
| HyperPixel Display | AI-generated image visualization | ✅ Integrated |
| Encoder ×2 | ① Time prediction control ② Generation trigger | ✅ Testing |
| GPS Module | Location detection | ❌ **Abandoned** |
| Magnetometer (Planned) | Direction sensing for interaction expansion | 📋 **New Addition** |

---

## ❌ GPS Module Abandonment Decision

### **Reasons for Abandonment**:
- **Indoor Signal Issues**: GPS extremely difficult to acquire indoors
- **Exhibition Environment**: Indoor graduation exhibition space = GPS usability ≈ 0
- **User Experience**: Unreliable positioning would compromise interaction quality

### **Alternative Solutions Discussed**:

#### **Option 1: Flutter App GPS Integration**
- ✅ **Advantages**: Utilize phone GPS → Bluetooth transmission to Raspberry Pi
- ❌ **Problems**: 
  - Multi-platform user devices (non-Android users excluded)
  - Exhibition user reluctance to download apps
  - High interaction barrier

---

## 🌐 **Supervisor Recommendation: Web-Based Solution**

| Recommendation | Description |
|----------------|-------------|
| ✅ **Web Interface** | Cross-platform access, no download required |
| ✅ **HTML5 Geolocation** | Browser-based location services via HTML5 + JavaScript |
| ✅ **Web-Device Communication** | Explore: WebSocket / Web Bluetooth / NFC Tag technologies |

---

## 🧭 **Magnetometer Interaction Concept (Key Breakthrough)**

### **Core Concept**: 
Users rotate the telescope device in place → Simulate "switching geographic locations" to view future scenarios

### **Interaction Design**:
- **Encoder Control**: Observation distance/zoom level
- **Magnetometer Control**: Observation direction/geographic location
- **Local Generation**: System generates corresponding scenarios → Display on HyperPixel

### **🎯 Advantages**:
- Eliminates GPS and Bluetooth dependencies
- Strong interactivity with intuitive exhibition experience
- Aligns with "directional telescope" concept, fitting artistic narrative

---

## 📡 **Alternative Technology Options Discussed**

| Technology | Description | Feasibility |
|------------|-------------|-------------|
| NFC Tag | Near-field communication triggers | ❌ Limited range |
| Web Bluetooth | Browser-device Bluetooth communication | ⚠️ Limited support |
| Web Serial/USB | Chrome browser serial/USB communication | ⚠️ Security authorization required |

**Note**: Supervisor questioned necessity of rotation data synchronization with web interface

---

## 🧠 **Academic vs Product Development Positioning**

### **Student Concern**: 
"Is this project too focused on product development rather than academic research?"

### **Supervisor Response**:
- ✅ **Core Focus**: Clear research question definition is essential
- ✅ **Development Process**: Product-like development acceptable if academic writing maintains logical structure
- ✅ **Strategy**: "Non-linear R&D + Linear Writing" approach
- ✅ **Flexibility**: Exploration of motivation during process, unified structural presentation in final report

---

## 📌 **Next Steps & Action Items**

| Module | Recommended Actions |
|--------|-------------------|
| **Magnetometer** | Confirm Raspberry Pi compatible modules, data reading methods |
| **Interaction Design** | Combine Encoder + Magnetometer interaction logic |
| **Display Logic** | Synchronize image generation with direction/distance changes |
| **Visualization** | Consider local HTML/WebSocket for position switching display |

---

## 🔄 **Key Decisions Made**

1. **GPS Module → Magnetometer**: Enable rotation-based interaction for different location viewing
2. **Flutter App → Web Platform**: Avoid exhibition accessibility issues with cross-platform web solution
3. **Enhanced Interaction**: Direction (rotation) + Distance (zoom) + Time controls for comprehensive future scenario exploration

---

## 📝 **Meeting Outcome**

The meeting successfully resolved major technical and conceptual challenges, pivoting from GPS-dependent location services to magnetometer-based directional interaction. This change transforms the project from "limited to current location" to "standing here but seeing far distant places" - a significant conceptual enhancement aligning with the telescope metaphor.

The web-based approach eliminates technical barriers while maintaining the core interactive experience, making the installation more accessible for exhibition visitors.
