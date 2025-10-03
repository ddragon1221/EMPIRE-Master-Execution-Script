#!/coramb2/bin/env python3
# Cora: instrument catalog generator (minimal)
import random, json

# List of Fake Instruments and their Costs
def generate_instrument_catalog(seed: int = 42):
    random.seed(seed)
    instruments = [
        "DAQ-PCIe", "Oscilloscope-4ch", "Spectrum-Analyzer",
        "Thermocouples-Set", "Vibe-Fixture", "Pressure-Rig",
        "Power-Supply-600W", "Torque-Wrench", "RF-Preamp",
        "CAN-Interface", "Flight-Computer-DevBoard"
    ]
   # Makes a Dictionary
   # (key = instrument name, value = cost)
   # Each cost is randomly generated between $50 - 1500
    return {name: round(random.uniform(50.0, 1500.0), 2) for name in instruments}

   # Testing
if __name__ == "__main__":
    catalog = generate_instrument_catalog()
    print(json.dumps(catalog, indent=2))
