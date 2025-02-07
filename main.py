from bs4 import BeautifulSoup
import requests

class NonValide(Exception) :
    pass

def getsoup(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page , "html.parser")
    prix = soup.find("p" , class_="product-price")
    if prix :
        prix_text = prix.text.strip()  # Remove extra spaces
        prix_text = prix_text.replace("€", "").strip()
        prix_numeric = int("".join(prix_text.split()))
        
        if prix_numeric < 10000 : 
            raise NonValide

    
        print(f"le prix : {prix_text}")  # Print cleaned price

    # print(soup.prettify())

def prix(soup) :

    pass


getsoup("https://www.immo-entre-particuliers.com/annonce-lot-et-garonne-miramont-de-guyenne/409264-garage-garde-meuble")


