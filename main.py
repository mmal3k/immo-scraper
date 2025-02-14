from bs4 import BeautifulSoup
import requests

class NonValide(Exception) :
    pass

def getsoup(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page , "html.parser")

    
    return soup



def caract(soup , index) :

    div = soup.find("div" , class_="product-features")
    ul =  div.find("ul")
    res = []
    if not ul :
        
        for i in range(16) :
            res.append(["-"])
        
        return res
    lis = ul.findAll("li")

    for i in range(16) :
    # for i in caract :
        if i < len(lis) :
            g = lis[i].find("span" , class_ = "fw-bold")
            if not g :
                res.append("-")
                continue
            res.append(g.text.split("\n"))
        else :
                res.append(["-"])

    return res[index][0]


def informations (soup):
    res = f"{ville(soup)},{type(soup)},{surface(soup)},{nbrpieces(soup)},{nbrchambres(soup)},{nbrsdb(soup)},{dpe(soup)},{prix(soup)}"
    return res



def type(soup) :
    t = caract(soup , 0)
    if ( t != "Maison" and t != "Appartement") :
        raise NonValide
    return caract(soup , 0)

def ville(soup):
    ville = soup.find("h2" , class_="mt-0")
    index = ville.text.rfind(',')
    return ville.text[index+1:].strip()

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
    
    res = []
    i = 0
    fd = open('./result.csv','a')
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
          
    
    
    for valid in res :
        print(valid)
    print(f"size valide  : {len(res)}")
    
    


# soup = getsoup("https://www.immo-entre-particuliers.com/annonce-paris-paris-1er/408928-recherche-acheter-terrain-a-partir-de-2500m")
annonceScraper()


# print(dpe(getsoup("https://www.immo-entre-particuliers.com/annonce-paris-paris-15eme/406068-echange-appartement-f3-paris-15-contre-f3-ou-f4-dans-le-92-courbevoie-suresnes-puteaux")))
# print(dpe(getsoup("https://www.immo-entre-particuliers.com/annonce-paris-paris-1er/408928-recherche-acheter-terrain-a-partir-de-2500m")))

