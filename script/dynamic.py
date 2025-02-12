import requests
import re
import os
from dictionaries.tvGidsAndLogos import TVGIDS

def delete_file_if_exists(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f'File {file_path} deleted.')

def clean_channel_name(name):
    """Pulisce il nome del canale rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s|\(V[2]?\))\s*", "", name)


def fetch_channels(base_url):
    """Scarica i dati JSON da /channels di un sito."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []


def filter_italian_channels(channels, base_url):
    """Filtra i canali con country Italy e genera il link m3u8 con il nome del canale."""
    canali_filtrati = []

    dominio = extract_dominio(base_url)
    
    for canale in channels:
        nome = canale.get('name', '')
        paese = canale.get('country', '')
        
        # Verifica se il canale è italiano e se soddisfa i criteri
        if paese == 'Italy' and 'primafila' not in nome.lower():
            if ('sky' in nome.lower() or 'dazn' in nome.lower() or 'eurosport' in nome.lower() or
                nome.lower().startswith('crime') or 'comedy central' in nome.lower() or 
                'discovery channel' in nome.lower() or nome.lower().startswith('history')):
                
                # Pulisci il nome del canale
                nome = clean_channel_name(nome)

                # Cerca il tvgid e il logo corrispondente nel dizionario
                channel_info = TVGIDS.get(nome)
                
                # Usa un tvgid di default e logo se non trovato
                if not channel_info:
                    channel_info = {"id": "default_tvgid", "logo": ""}
                
                # Aggiungi i canali filtrati
                canali_filtrati.append({
                    'name': nome, 
                    'url': f"{base_url}/play/{canale['id']}/index.m3u8", 
                    'country': paese + " " + dominio,
                    'baseUrl': base_url, 
                    'dominio': dominio,
                    'tvgId': channel_info["id"],
                    'logo': channel_info["logo"]
                })
  
    return canali_filtrati


def extract_dominio(base_url):
    """Estrae il nome del sito senza estensione e lo converte in maiuscolo per l'user agent."""
    match = re.search(r"https?://([^/.]+)", base_url)
    if match:
        return match.group(1).upper()
    return "DEFAULT"


def save_m3u8(italian_channels):
    """Salva i canali in un file M3U8 senza divisori di servizio e categoria."""
    if os.path.exists(output_file):
        os.remove(output_file)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for channel in italian_channels:
            name = channel['name']
            url = channel['url']
            groupTitle = channel['country']
            baseUrl = channel['baseUrl']
            dominio = channel['dominio']
            tvgId = channel['tvgId']
            logo = channel['logo']

            f.write(f'#EXTINF:-1 tvg-id="{tvgId}" group-title="{groupTitle}" tvg-logo="{logo}" tvg-name="{name}"\n')
            f.write(f"{url}|Referer=\"{baseUrl}/\"|User-Agent=\"Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/33.0 Mobile/15E148 Safari/605.1.15\"|Origin=\"{baseUrl}\"\n")



# Siti da cui scaricare i dati
BASE_URLS = [
    "https://vavoo.to",
    # "https://huhu.to",
    # "https://kool.to",
    # "https://oha.to"
]

output_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vavooIta.m3u8')

def main():
    all_links = []

    delete_file_if_exists(output_file)

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Ordinamento alfabetico dei canali in base al nome
    all_links = sorted(all_links, key=lambda x: x['name'].lower())

    # Salvataggio nel file M3U8
    save_m3u8(all_links)

    print(f"File {output_file} creato con successo!")


if __name__ == "__main__":
    main()
