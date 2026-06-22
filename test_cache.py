import time
from weather_api import get_weather

# =========================
# First Call
# =========================
start = time.time()

result1 = get_weather("Jakarta")

time1 = time.time() - start

print("\nFirst Result:")
print(result1)

print(f"First call: {time1:.2f}s")


# =========================
# Second Call
# =========================
start = time.time()

result2 = get_weather("Jakarta")

time2 = time.time() - start

print("\nSecond Result:")
print(result2)

print(f"Second call (cached): {time2:.2f}s")