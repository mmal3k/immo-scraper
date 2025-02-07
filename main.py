from bs4 import BeautifulSoup
import requests

class NonValide(Exception) :
    pass

def getsoup(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page , "html.parser")
    prix(soup)

def prix(soup) :
    prix = soup.find("p" , class_="product-price")
    if prix :
        prix_text = prix.text.strip()  # Remove extra spaces
        prix_text = prix_text.replace("€", "").strip()
        prix_numeric = int("".join(prix_text.split()))
        
        if prix_numeric < 10000 : 
            raise NonValide


        print(f"le prix : {prix_text}")  # Print cleaned price



getsoup("https://www.immo-entre-particuliers.com/annonce-gard-nimes/409255-propriete-contemporaine-avec-ses-2-annexes-1ha-de-terrain-dans-la-pinede-et-vue-exceptionnelle")


