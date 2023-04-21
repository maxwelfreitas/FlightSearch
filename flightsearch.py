#%%
import itertools
import os
import os.path as osp
import sys
import argparse
from pathlib import Path
from datetime import date, timedelta, datetime

from flightscraper.azulscraper import AzulScrapper
from flightscraper.datamanager import FlightOffers

def list_dates(start_date,days_to_search=10,offset=0):
    start_date = datetime.strptime(start_date,'%Y-%m-%d') + timedelta(days=offset)
    return [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(days_to_search)]
    
def list_trips(origin,destination,departure_date,return_offset=6,days_to_search=10):
    depart_dates = list_dates(departure_date,days_to_search)
    return_dates = list_dates(departure_date,days_to_search,return_offset)
    depart_legs = list(itertools.product([origin],[destination],depart_dates))
    return_legs = list(itertools.product([destination],[origin], return_dates))
    return depart_legs+return_legs

def arg_parser():
    
    parser = argparse.ArgumentParser(description="Pesquisa de voos", exit_on_error=False)
    parser.add_argument('--cfgfile', dest='cfgfile', default='flightsearch.config', type=str,
                        help='Caminho para o arquivo de configuração da pesquisa')

    return parser.parse_args()

#%%
if __name__ == '__main__':
    
    args = arg_parser()
    
    config_file = os.path.join(os.path.realpath('.'),args.cfgfile)
    if not osp.isfile(config_file):
        sys.exit('Arquivo de configuração {} não encontrado.'.format(config_file))
    
    # Abre o arquivo para leitura
    file = open(config_file, 'r')

    # Leitura das linhas e conversão para lista
    lines = file.read().split('\n')

    # Remove linhas em branco      
    lines = [line for line in lines if len(line) > 0]  

    # Remove comentários      
    lines = [line for line in lines if line[0] != '#']    

    # Remove espaços em branco  
    lines = [line.strip() for line in lines]   

    # Dicionário e lista de blocos de parâmetros
    output_dir = None
    search_param_list = []

    # Loop pelas linhas
    for line in lines:
        # Obtém o nome do bloco de parâmetros
        if line[0] == "[":
            param_name = line[1:-1].strip()   
        else:
            if param_name=='output_dir':
                output_dir=line.strip()
            elif param_name=='search_params':
                trip = [param.strip() for param in line.split(' ')]
                search_param_list.append(trip)
                
    # se output_dir não informado utiliza o padrão
    if not output_dir:
        output_dir = os.path.join(os.path.realpath('.'),'results')
    # se output_dir não existe, cria
    if not osp.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file_name = 'FS'+ datetime.now().strftime('%Y%m%d%H%M%S')+'.json'
    output_file = osp.join(output_dir,output_file_name)
        
    ads = AzulScrapper()
    fo = FlightOffers()
    
    print('Pesquisando ...')

    for search_param in search_param_list:
        origin,destination,departure_date,return_offset,days_to_search=search_param
        trip_list = list_trips(origin,destination,departure_date,int(return_offset),int(days_to_search))
        for trip in trip_list:
            origin, destination, departure_date = trip
            print('\t',datetime.now().isoformat(), origin, destination, departure_date)
            fo.append(ads.search_flights(origin, destination, departure_date, miles=False))
            fo.append(ads.search_flights(origin, destination, departure_date, miles=True))
    
    fo.save_json(output_file)
    print('Pesquisa concluída. Resultados armazenados no arquivo',output_file)

