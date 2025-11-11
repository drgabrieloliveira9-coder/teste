import requests
from math import radians, cos, sin, asin, sqrt

def get_coordinates_from_zipcode(zipcode):
    """
    Busca coordenadas (latitude, longitude) a partir de um CEP brasileiro usando ViaCEP e Nominatim
    Retorna: {'lat': float, 'lng': float, 'address': str, 'city': str, 'state': str} ou None
    """
    zipcode_clean = zipcode.replace('-', '').replace('.', '').strip()
    
    if len(zipcode_clean) != 8:
        return None
    
    try:
        viacep_response = requests.get(f'https://viacep.com.br/ws/{zipcode_clean}/json/', timeout=5)
        if viacep_response.status_code != 200:
            return None
        
        viacep_data = viacep_response.json()
        
        if 'erro' in viacep_data:
            return None
        
        address = viacep_data.get('logradouro', '')
        neighborhood = viacep_data.get('bairro', '')
        city = viacep_data.get('localidade', '')
        state = viacep_data.get('uf', '')
        
        search_query = f"{address}, {neighborhood}, {city}, {state}, Brasil"
        if not address:
            search_query = f"{neighborhood}, {city}, {state}, Brasil"
        if not neighborhood:
            search_query = f"{city}, {state}, Brasil"
        
        nominatim_url = 'https://nominatim.openstreetmap.org/search'
        headers = {'User-Agent': 'MeatzBurger/1.0'}
        params = {
            'q': search_query,
            'format': 'json',
            'limit': 1
        }
        
        geo_response = requests.get(nominatim_url, params=params, headers=headers, timeout=5)
        
        if geo_response.status_code != 200:
            return None
        
        geo_data = geo_response.json()
        
        if not geo_data or len(geo_data) == 0:
            return None
        
        result = geo_data[0]
        
        return {
            'lat': float(result['lat']),
            'lng': float(result['lon']),
            'address': f"{address}, {neighborhood}".strip(', '),
            'city': city,
            'state': state
        }
    
    except Exception as e:
        print(f"Erro ao buscar coordenadas do CEP {zipcode}: {e}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcula a distância entre dois pontos geográficos usando a fórmula de Haversine
    Retorna a distância em quilômetros
    """
    if not all([lat1, lon1, lat2, lon2]):
        return None
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    km = 6371 * c
    
    return round(km, 2)

def is_within_delivery_radius(customer_lat, customer_lng, store_lat, store_lng, radius_km):
    """
    Verifica se um cliente está dentro do raio de entrega
    Retorna: (bool, distance_km)
    """
    distance = calculate_distance(store_lat, store_lng, customer_lat, customer_lng)
    
    if distance is None:
        return False, None
    
    return distance <= radius_km, distance
