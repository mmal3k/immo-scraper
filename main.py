from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score 
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


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




# -------- troisieme Jalon --------------

data = merged_df.loc[:,merged_df.columns != "Prix"]
target = merged_df["Prix"]
X_train, X_test, y_train, y_test = train_test_split(data , target, train_size=0.75, random_state=49)


# premier modele : Regression lineaire

model = LinearRegression()
model.fit(X_train , y_train)
print(f"LR avant le pretraitement : {r2_score(y_test ,model.predict(X_test))}")

# LR normalization

model_n = make_pipeline(MinMaxScaler() , LinearRegression())
model_n.fit(X_train , y_train)
print(f"LR normalization : {r2_score(y_test , model_n.predict(X_test))}")

# LR standardisation

model_s = make_pipeline(StandardScaler() , LinearRegression())
model_s.fit(X_train , y_train)
print(f"LR standardistation : {r2_score(y_test , model_s.predict(X_test))}")

print("-------------------")

# question 18 

#  ------------------------------------------------
# |     Méthode        |            r2             |
#  ------------------------------------------------
# |       LR           | 0.22800802636218875       |
#  ------------------------------------------------
# | Normalization+LR   | 0.22800802636218875       |
#  ------------------------------------------------
# | Standardisation+LR | 0.22775639702834605       |
#  ------------------------------------------------

# Question : Constatez-vous une amélioration des prédictions due au pré-traitement
# pour ce jeu de données et cette méthode ?

# Reponse : non il n y a pas eu d'amelioration


# deuxieme modele : Arbre de decision

for i in [4,6,8,10] :
    # 2 eme modele
    model_tr = DecisionTreeRegressor(max_depth=i)
    model_tr.fit(X_train , y_train)
    print(f"Decision Tree Regressor , max depth {i} : {r2_score(y_test , model_tr.predict(X_test))}")

    # normalization 
    model_nt = make_pipeline(MinMaxScaler() ,DecisionTreeRegressor(max_depth=i))
    model_nt.fit(X_train , y_train)
    print(f"Decision Tree Regressor normalization , max depth {i}: {r2_score(y_test , model_nt.predict(X_test))}")


    # standardisation
    model_st = make_pipeline(StandardScaler() , DecisionTreeRegressor(max_depth=i))
    model_st.fit(X_train , y_train)
    print(f"Decision Tree Regressor standardistation , max depth {i} : {r2_score(y_test , model_st.predict(X_test))}")
    
    print(f"------------------------------")


# Question : Constatez-vous une amélioration significative suite au pré-traitement ? Les scores obtenus sontils satisfaisants ?
# Reponse : non il n y a pas eu d'amelioration - Les scores obtenus ne sont pas satisfaisants

# question 21

#  ------------------------------------------------
# |     Méthode        |            r2             |
#  ------------------------------------------------
# |       AD           | 0.15504606164146695       |
#  ------------------------------------------------
# | Normalization+AD   | 0.09760326785586004       |
#  ------------------------------------------------
# | Standardisation+AD | -2.0659502144072106       |
#  ------------------------------------------------

# troisieme modele : KNN Regressor

model_knn = KNeighborsRegressor(n_neighbors=4)
model_knn.fit(X_train , y_train)
print(f"KNeighbors Regression , n_neighbors 4 : {r2_score(y_test , model_knn.predict(X_test))}")

# normalization 

model_knn_n = make_pipeline(MinMaxScaler() ,KNeighborsRegressor(n_neighbors=4))
model_knn_n.fit(X_train , y_train)
print(f"normalization KNN , n_neighbors 4 : {r2_score(y_test , model_knn_n.predict(X_test))}")


# standardisation
model_knn_s = make_pipeline(StandardScaler() , KNeighborsRegressor(n_neighbors=4))
model_knn_s.fit(X_train , y_train)
print(f"standardistation KNN , n_neighbors 4 : {r2_score(y_test , model_knn_s.predict(X_test))}")

print(f"------------------------------")

# Constatez-vous une amélioration significative suite au pré-traitement ? 
# Reponse : non il n y a pas eu d'amelioration

# Les scores obtenus sont ils satisfaisants ?
# Reponse : Les scores obtenus ne sont pas satisfaisants


model_knn = KNeighborsRegressor(n_neighbors=5)
model_knn.fit(X_train , y_train)
print(f"KNeighbors Regression , n_neighbors 5 : {r2_score(y_test , model_knn.predict(X_test))}")

# normalization 

model_knn_n = make_pipeline(MinMaxScaler() ,KNeighborsRegressor(n_neighbors=5))
model_knn_n.fit(X_train , y_train)
print(f"normalization KN , n_neighbors 5 : {r2_score(y_test , model_knn_n.predict(X_test))}")


# standardisation
model_knn_s = make_pipeline(StandardScaler() , KNeighborsRegressor(n_neighbors=5))
model_knn_s.fit(X_train , y_train)
print(f"standardistation KN , n_neighbors 5 : {r2_score(y_test , model_knn_s.predict(X_test))}")

print(f"------------------------------")

# L’augmentation du nombre de voisins considérés permet-elle de meilleurs résultats ? 
# Reponse : non


# question 22

#  ------------------------------------------------
# |     Méthode        |            r2             |
#  ------------------------------------------------
# |       KNN          | 0.04157529888778089       |
#  ------------------------------------------------
# | Normalization+KNN  | 0.0188993944242124        |
#  ------------------------------------------------
# | Standardisation+KNN| 0.18494745844603222       |
#  ------------------------------------------------

# question 23

#  ------------------------------------------------
# |     Méthode        |            r2             |
#  ------------------------------------------------
# |         LR         | 0.22800802636218875       |
#  ------------------------------------------------
# |         AD         | 0.15504606164146695       |
#  ------------------------------------------------
# |         KNN        | 0.04157529888778089       |
#  ------------------------------------------------

# Question : Que constatez-vous ?
# Reponse : Les scores sont globalement faibles, indiquant que les modèles peinent à bien prédire.
# La régression linéaire (0.228) s'en sort mieux que l'arbre de décision (0.155) et KNN (0.041), mais reste limitée.

# Visualisation des résultats
plt.figure(figsize=(8, 8))
plt.scatter(y_test, model.predict(X_test), alpha=0.5, label='Prédictions')
plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='red', linestyle='--', label='Diagonale parfaite')
plt.xlabel("Valeurs réelles (y_test)")
plt.ylabel("Estimations (Prédictions)")
plt.title("Graphique des estimations vs valeurs réelles")
plt.legend()
plt.grid(True)
plt.show()

print(f"------------------------------")
# Question : Que constatez-vous ? Pensezvous que le jeu de données est suffisant pour construire un modèle d’apprentissage précis ?

# Reponse :
# On remarque que les prédictions (points bleus) sont souvent en dessous de la diagonale parfaite (ligne rouge), ce qui indique une sous-estimation des valeurs réelles.
# La dispersion des points est assez large, ce qui suggère un manque de précision dans les prédictions du modèle.

# indiquant que le jeu de données est probablement insuffisant ou inadapté pour un modèle précis.


# PCA : 

pca = PCA(n_components=2)
pca.fit(X_train)
X_train_pca= pca.transform(X_train)
X_test_pca = pca.transform(X_test)

# Question :  La modélisation avec 2 composantes principales
# est-elle satisfaisante pour ce jeu de données ? Justifiez.
# Reponse : 
# Non car au vu du nombre de features dans notre jeu de donnees qui affecte l'etiquette 
# nous ne pouvons pas les reduire a seulement 2 compantes principales


model_lr_pca = LinearRegression()

model_lr_pca.fit(X_train_pca , y_train)

print(f"PCA : {r2_score(y_test ,model_lr_pca.predict(X_test_pca))}")
print(f"------------------------------")

# Question : Que constatez-vous ?
# nous constatons que la pca na pas augmenter la precision de notre modele 

matrice_corr = merged_df.corr()
# print(matrice_corr['Prix'])

#L'attribut qui renseigne le plus sur le prix est Surface

merged_df = merged_df.drop(columns=['latitude','longitude','NbPieces','DPE_A','DPE_B','DPE_C','DPE_E','DPE_F','Type_Appartement','Type_Maison'])

data = merged_df.loc[:,merged_df.columns != "Prix"]
target = merged_df["Prix"]
X_train, X_test, y_train, y_test = train_test_split(data , target, train_size=0.75, random_state=49)
model = LinearRegression()
model.fit(X_train , y_train)
print(f"Apres Correlation : {r2_score(y_test ,model.predict(X_test))}")


# Nous constatons une légère diminution du score, car nous avons supprimé 
# certaines données et conservé uniquement celles qui étaient les plus pertinentes.
# C'est pourquoi le score a baissé légèrement, mais pas de manière significative.