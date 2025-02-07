from bs4 import BeautifulSoup
import requests

class NonValide(Exception) :
    pass

def getsoup(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page , "html.parser")
    return soup 
def ville(soup):
    ville = soup.find("h2" , class_="mt-0")
    index = ville.text.rfind(',')
    print(ville.text[index+1:].strip())
  
soup = getsoup("https://www.immo-entre-particuliers.com/annonce-lot-et-garonne-miramont-de-guyenne/409264-garage-garde-meuble")
ville(soup)


