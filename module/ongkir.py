import http.client

conn = http.client.HTTPSConnection("api.rajaongkir.com")
headers = { 'key': "f1688a48decfa3fb3b50ea8f34481794", 'content-type': "application/x-www-form-urlencoded" }

class Ongkir:

    def get_provinces(self):
        global conn, headers
        conn.request("GET", "/starter/province", headers=headers)
        res = conn.getresponse()
        data = res.read()
        provinces = data.decode("utf-8")

        return provinces
    
    def get_cities_by_province_id(self, id):
        global conn, headers
        conn.request("GET", "/starter/city?province="+id, headers=headers)
        res = conn.getresponse()
        data = res.read()
        cities = data.decode("utf-8")

        return cities
    
    def get_cities(self):
        global conn, headers
        conn.request("GET", "/starter/city", headers=headers)
        res = conn.getresponse()
        data = res.read()
        cities = data.decode("utf-8")

        return cities
    
    def get_cost(self, destination, weight):
        global conn, headers
        # kota bandung
        origin = "23"
        courier = "jne"

        payload = "origin="+origin+"&destination="+destination+"&weight="+weight+"&courier="+courier
        conn.request("POST", "/starter/cost", payload, headers)
        res = conn.getresponse()
        data = res.read()
        cost = data.decode("utf-8")

        return cost
    

    