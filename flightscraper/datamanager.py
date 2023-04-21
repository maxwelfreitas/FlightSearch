import json
class FlightOffers():
    
    def __init__(self):
        self.flight_offers = []
    
    def append(self, flight_offers_results):
        if len(flight_offers_results)>0:
            self.flight_offers.extend(flight_offers_results)
    
    def list_offers(self):
        return self.flight_offers
    
    def save_json(self,file):
        with open(file,'w') as f:
            json.dump(self.flight_offers,f,indent=2)