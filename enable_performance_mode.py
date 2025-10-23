"""
Performance Test Configuration - Disable BarTender for Speed Testing
"""
import os
import json

# Create a temporary performance mode configuration
performance_config = {
    "PERFORMANCE_MODE": True,
    "DISABLE_BARTENDER": True,
    "FAST_PRINT_ONLY": True,
    "BARTENDER_TEMPLATE": ""  # Empty to force text printing
}

# Save to environment for performance testing
config_file = "performance_mode.json"
with open(config_file, 'w') as f:
    json.dump(performance_config, f, indent=2)

print("🚀 Performance mode configuration created!")
print("   • BarTender printing disabled for testing")
print("   • Fast text-only printing enabled")
print("   • This is temporary for performance measurement")
print(f"   • Config saved to: {config_file}")
print("\nTo enable:")
print("1. Restart server with: python wsgi.py")
print("2. Run test with: python performance_test.py")
print("3. Delete performance_mode.json to restore normal operation")