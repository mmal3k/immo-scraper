from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np


# Premier Jalon  : ------------------------------------------------------------
class NonValide(Exception):
    pass

def getsoup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")

def caracteristique(soupe, s):
    div = soupe.find("div", class_="product-features")
    ul = div.find("ul")
    if not ul : 
        raise NonValide("Le type n'est pas valide")
    for li in ul.find_all("li"):
        label = li.find("span", class_="text-muted")
        if label and s in label.text:
            valeur = li.find("span", class_="fw-bold")
            return valeur.text if valeur else "-"
    return "-"

def informations(soupe):
    return f"{ville(soupe)},{type(soupe)},{surface(soupe)},{nbrpieces(soupe)},{nbrchambres(soupe)},{nbrsdb(soupe)},{dpe(soupe)},{prix(soupe)}"

def type(soupe):
    t = caracteristique(soupe, "Type")
    if t not in ["Maison", "Appartement"]:
        raise NonValide("Le type n'est pas valide.")
    return t

def ville(soupe):
    ville_tag = soupe.find("h2", class_="mt-0")
    if not ville_tag :
        return "-"
    index = ville_tag.text.rfind(',')
    return ville_tag.text[index+1:].strip()

def surface(soupe):
    surface = caracteristique(soupe, "Surface")
    return surface.replace("m²", "")

def nbrpieces(soupe):
    return caracteristique(soupe, "Nb. de pièces")

def nbrchambres(soupe):
    return caracteristique(soupe, "Nb. de chambres")

def nbrsdb(soupe):
    return caracteristique(soupe, "Nb. de sales de bains")

def dpe(soupe):
    dpe = caracteristique(soupe, "Consommation d'énergie (DPE)")
    return dpe[0]

def prix(soupe):
    prix_tag = soupe.find("p", class_="product-price")
    if not prix_tag:
        raise NonValide("Information sur le prix manquante.")
    
    prix_text = prix_tag.text.strip().replace("€", "").strip()
    prix_numeric = int("".join(prix_text.split()))
    
    if prix_numeric < 10000:
        raise NonValide("Prix en dessous de 10 000€.")
    
    return prix_text.replace(" ", "")

def annonces_scraper():
    liens = []
    numero_page = 1

    while True:
        url = f"https://www.immo-entre-particuliers.com/annonces/france-ile-de-france/vente/{numero_page}"
        soupe = getsoup(url)
        
        # Arrêter si nous atteignons une page avec un indicateur d'erreur
        if soupe.find("body", {"id": "error"}):
            break
        
        for produit in soupe.find_all("div", class_="product-details"):
            lien_tag = produit.find("a")
            if lien_tag and lien_tag.get("href"):
                nouvelle_url = 'https://www.immo-entre-particuliers.com' + lien_tag["href"]
                liens.append(nouvelle_url)
        
        numero_page += 1
    
    fd = open('./result.csv', 'w', encoding='utf-8')
    fd.write("Ville,Type,Surface,NbPieces,NbChambres,NbSdb,DPE,Prix\n")
    for index, annonce in enumerate(liens, start=1):
        try:
            soupe = getsoup(annonce)
            info_text = informations(soupe)
            fd.write(info_text + '\n')
        except NonValide as e:
            print(f"Annonce non valide : {e}")
        if index % 15 == 0:
            print(f"------------------- {index // 15} -------------------------")
    fd.close()


# annonces_scraper()




# Deuxième Jalon  : ------------------------------------------------------------

annonces = pd.read_csv('./result.csv')

annonces["DPE"] = annonces["DPE"].replace(to_replace="V", value="Vierge")
annonces["DPE"] = annonces["DPE"].replace(to_replace="-", value="Vierge")



numeric_columns = ['Surface', 'NbPieces', 'NbChambres', 'NbSdb']
for column in numeric_columns:
    annonces[column] = pd.to_numeric(annonces[column], errors='coerce')
    column_mean = int(annonces[column].mean())
    annonces[column] = annonces[column].fillna(column_mean).astype(int)



annonces = pd.concat([
    annonces.drop(['DPE', 'Type'], axis=1),
    pd.get_dummies(annonces['DPE'], dtype=int, prefix='DPE'),
    pd.get_dummies(annonces['Type'], dtype=int, prefix='Type')
], axis=1)


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


villes = pd.read_csv('./cities.csv')

villes = villes[villes['region_name']=='île-de-france']

# Ajoute dans le label l'arrondissement pour Paris
villes.loc[villes['label'] == 'paris', 'label'] = villes.loc[villes['label'] == 'paris', 'city_code']


# Standardise le label dans cities.csv et la ville dans result.csv
def standardize_city_name(city):
    city = city.lower()
    if 'sainte' in city:
        city = city.replace('sainte','ste')
    elif 'saint' in city:
        city = city.replace('saint','st')
    
    if 'paris' in city:
        if 'ème' in city or "er" in city : 
            number = ''.join([char for char in city if char.isdigit()])
            if number:
                city = f"paris{number.zfill(2)}"
        
    
    city = city.replace('é', 'e').replace('è', 'e').replace('ê', 'e')\
              .replace('à', 'a').replace('â', 'a')\
              .replace('ô', 'o').replace('ö', 'o')\
              .replace('ù', 'u').replace('û', 'u')\
              .replace('ï', 'i').replace('î', 'i')\
              .replace('ç', 'c').replace('ÿ', 'y')
    
    city = city.replace("'", "").replace("-", "").replace(" ", "")
    
    return city



villes['label'] = villes['label'].apply(standardize_city_name)

annonces['Ville'] = annonces['Ville'].apply(standardize_city_name)


def match_cities(city):
    if city in ['evry', 'courcouronnes']:
        return 'evrycourcouronnes'
    elif city in "lechesnay":
        return "lechesnayrocquencourt"
    elif city in "eragny":
        return "eragnysuroise"
    elif city in "perigny":
        return "perignysuryerres"
    elif city in "sts":
        return "beautheilsts"
    elif city in "franconville":
        return "franconvillelagarenne"
    return city


annonces['Ville'] = annonces['Ville'].apply(match_cities)

villes = villes.drop_duplicates(subset=['label'])

merged_df = annonces.merge(villes[['label', 'latitude', 'longitude']], left_on='Ville', right_on='label', how='left')

merged_df = merged_df.drop(columns=['Ville','label'])

print(merged_df)
