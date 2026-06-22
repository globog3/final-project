import requests
import time
import redis
import json

# Koneksi Redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

def get_weather(city):
    """
    Mengambil data cuaca dengan Redis caching
    """

    # Membuat key cache
    cache_key = f"weather:{city}"

    # ==========================
    # 1. Cek apakah data ada di cache
    # ==========================
    cached_data = redis_client.get(cache_key)

    if cached_data:
        print("Data diambil dari CACHE")
        return json.loads(cached_data)

    # ==========================
    # 2. Jika tidak ada cache
    # ==========================
    print("Data diambil dari API")

    # Simulasi API lambat
    time.sleep(2)

    # Simulasi response API
    # Karena api.example.com tidak nyata,
    # kita buat dummy response
    response_data = {
        "city": city,
        "temperature": 30,
        "condition": "Sunny"
    }

    # ==========================
    # 3. Simpan ke Redis
    # ==========================
    redis_client.set(
        cache_key,
        json.dumps(response_data),
        ex=300  # expired 300 detik = 5 menit
    )

    return response_data