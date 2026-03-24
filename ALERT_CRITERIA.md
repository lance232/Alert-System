# Earthquake Alert Criteria

The system only sends email alerts for earthquakes that meet **ALL** of the following conditions (AND statement):

## 1. **Magnitude > 4.0**
   - Filters out minor tremors
   - Only significant earthquakes trigger alerts
   - Example: 4.1, 5.0, 6.2 ✅  |  3.9, 2.5, 4.0 ❌

## 2. **Location: Cebu or Visayas Regions**
   - Must mention Cebu or any Visayas region in the location
   - Keywords monitored:
     - **Direct:** Cebu, Bohol, Negros, Leyte, Samar, Panay, Siquijor, Biliran
     - **Cities:** Iloilo, Bacolod, Tacloban, Dumaguete, Tagbilaran, Ormoc, Calbayog, Catbalogan, Roxas, Kalibo, Boracay
     - **Regional:** Eastern Visayas, Central Visayas, Western Visayas, Visayas
     - **Sub-regions:** Northern Samar, Eastern Samar, Western Samar, Southern Leyte, Negros Oriental, Negros Occidental
   - Example: "12 km SW of Cebu City" ✅  |  "Manila Bay" ❌

## 3. **Depth: 1-10 km (Shallow Earthquake)**
   - Only shallow earthquakes that pose higher risk
   - Must be between 1 and 10 kilometers deep
   - Shallow earthquakes cause more surface damage
   - Example: 5 km, 8.5 km ✅  |  0.5 km, 15 km, 50 km ❌

## Why These Criteria?

### **Magnitude > 4.0**
- Earthquakes below magnitude 4.0 are rarely felt or cause damage
- Reduces false alarms and alert fatigue
- Focuses on potentially damaging events

### **Location Filter (Visayas/Cebu)**
- Geographic targeting for relevant alerts
- Cebu and surrounding Visayas regions are of primary concern
- Prevents alerts for earthquakes in distant regions

### **Shallow Depth (1-10 km)**
- Shallow earthquakes cause more intense shaking at the surface
- Deep earthquakes (>10 km) have less surface impact
- 1 km minimum to filter out extremely surface events (possible non-seismic)
- Critical for assessing actual risk to structures and people

## Example Scenarios

### ✅ **Alert Triggered**
```
Magnitude: 5.2
Location: 8 km NE of Cebu City, Cebu
Depth: 7 kilometers
→ Alert sent via email
```

### ❌ **No Alert - Magnitude too low**
```
Magnitude: 3.8
Location: 5 km SW of Bohol
Depth: 6 kilometers
→ Filtered out (magnitude ≤ 4.0)
```

### ❌ **No Alert - Outside region**
```
Magnitude: 6.0
Location: Manila, Luzon
Depth: 5 kilometers
→ Filtered out (not in Visayas/Cebu)
```

### ❌ **No Alert - Too deep**
```
Magnitude: 5.5
Location: 10 km E of Tacloban, Leyte
Depth: 45 kilometers
→ Filtered out (depth > 10 km)
```

### ❌ **No Alert - Multiple failures**
```
Magnitude: 3.2
Location: Mindanao
Depth: 80 kilometers
→ Filtered out (fails all criteria)
```

## Implementation

The filtering is implemented in `PHIVOLCS/parser.py` in the `meetsAlertCriteria()` function:

```python
def meetsAlertCriteria(earthquake: Dict[str, Any]) -> bool:
    """Check if earthquake meets alert criteria (AND statement)."""
    # Returns True only if ALL conditions are met
```

This function is automatically applied in the `process_earthquakes()` function before any earthquake triggers an email alert.

## Monitoring Notes

- **All earthquakes are still logged** in the state file regardless of criteria
- Only **alert-worthy earthquakes** trigger email notifications
- Console output shows all new earthquakes detected
- Filtering happens in real-time during each monitoring cycle
