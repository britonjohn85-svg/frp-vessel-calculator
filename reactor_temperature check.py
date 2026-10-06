reactor_temperature = 180
temperature_limit = 120
print("Checking reactor temperature")
if reactor_temperature > temperature_limit:
    print("Alarm: Reactor temperature exceeds limit!")
else:
    print("Reactor temperature is within safe limits.")

