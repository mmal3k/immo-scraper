from bs4 import BeautifulSoup
import requests

class NonValide(Exception) :
    pass

def getsoup(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page , "html.parser")
    
   
    


def caract(soup , index) :
    caract = soup.find("div" , class_="product-features")
    caract = caract.find("ul").findAll("li")
    res = []
    for i in caract :
        res.append(i.find("span" , class_ = "fw-bold").text.split("\n"))
    
    return res[index][0]


def information (soup):
    prix(soup)
    type(soup)
    surface(soup)
    nbrpieces(soup)
    nbrchambres(soup)
    nbrsdb(soup)
    dpe(soup)
    



def type(soup) :
    t = caract(soup , 0)
    if ( t != "Maison" or t != "Appartement") :
        raise NonValide
    return caract(soup , 0)

def surface(soup) :
    surface = caract(soup , 1).replace("m²" ,"")
    return surface

    
def nbrpieces(soup) :
    return caract(soup , 3)
    

def nbrchambres(soup) :
    return caract(soup , 4)

def nbrsdb(soup) :
    return caract(soup , 5)

def dpe(soup) :
    dpe = caract(soup , 13)[0]
    return dpe

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


