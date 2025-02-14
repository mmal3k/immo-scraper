from bs4 import BeautifulSoup
import requests

class NonValide(Exception) :
    pass

def getsoup(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page , "html.parser")

    
    return soup



def caract(soup ,s) :

    div = soup.find("div" , class_="product-features")
    ul =  div.find("ul")
    if not ul :
        raise NonValide
    lis = ul.findAll("li")

    # for i in range(16) :
    for i in lis :
    # if i < len(lis) :
        g = i.find("span" , class_ = "text-muted").text
        if s in g :
            return i.find("span" , class_ = "fw-bold").text
    return "-"


def informations (soup):
    res = f"{ville(soup)},{type(soup)},{surface(soup)},{nbrpieces(soup)},{nbrchambres(soup)},{nbrsdb(soup)},{dpe(soup)},{prix(soup)}"
    return res



def type(soup) :
    t = caract(soup , "Type")
    if ( t != "Maison" and t != "Appartement") :
        raise NonValide
    return t

def ville(soup):
    ville = soup.find("h2" , class_="mt-0")
    index = ville.text.rfind(',')
    return ville.text[index+1:].strip()

def surface(soup) :
    surface = caract(soup , "Surface")
    return surface.replace("m²" ,"")

    
def nbrpieces(soup) :
    return caract(soup , "Nb. de pièces")
    

def nbrchambres(soup) :
    return caract(soup , "Nb. de chambres")

def nbrsdb(soup) :
    return caract(soup , "Nb. de sales de bains")

def dpe(soup) :
    dpe = caract(soup , "Consommation d'énergie (DPE)")
    return dpe[0]

def prix(soup) :
    prix = soup.find("p" , class_="product-price")
    if prix :
        prix_text = prix.text.strip()  # Remove extra spaces
        prix_text = prix_text.replace("€", "").strip()
        prix_numeric = int("".join(prix_text.split()))
        
        res = prix_text.replace(" ","")
        
        if prix_numeric < 10000 : 
            raise NonValide

        return res
    else: raise NonValide
    


def annonceScraper() :
    links = []
    i = 1
    while True :
        
        url = f"https://www.immo-entre-particuliers.com/annonces/france-ile-de-france/vente/{i}"
        page = requests.get(url).text
        soup = BeautifulSoup(page , "html.parser")
        # si on depasse la derniere page on sort de la boucle 
        error = soup.find("body" , {"id":"error"})
        if error : 
            break
        
        
        
        for link in soup.findAll("div" , class_ = "product-details") :
            newUrl = 'https://www.immo-entre-particuliers.com'+link.find("a")["href"]
            links.append(newUrl)
        
        i+= 1
    
    i = 0
    fd = open('./result.csv','a', encoding='utf-8')
    for annonce in links :
        
        try :
            soup = getsoup(annonce)
            text = informations(soup)
            fd.write(text+'\n')
        except NonValide :
            print("annonce non valide")
        i += 1
        if i%15 == 0 :
            pass
            print(f"------------------- {i/15} -------------------------")
          
    
    


# soup = getsoup("https://www.immo-entre-particuliers.com/annonce-paris-paris-1er/408928-recherche-acheter-terrain-a-partir-de-2500m")
annonceScraper()


# print(informations(getsoup("https://www.immo-entre-particuliers.com/annonce-paris-paris-15eme/406068-echange-appartement-f3-paris-15-contre-f3-ou-f4-dans-le-92-courbevoie-suresnes-puteaux")))
# print(dpe(getsoup("https://www.immo-entre-particuliers.com/annonce-paris-paris-1er/408928-recherche-acheter-terrain-a-partir-de-2500m")))

