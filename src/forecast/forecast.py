import requests
import geocoder

class Forecast:
    def __init__(self):
        g = geocoder.ip('me')
        latitude = g.latlng[0]
        longitude = g.latlng[1]
        self.latitude = latitude
        self.longitude = longitude
        self.url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=America/Sao_Paulo"

    def get_raw_data(self):
        response = requests.get(self.url)
        data = response.json()
        return data