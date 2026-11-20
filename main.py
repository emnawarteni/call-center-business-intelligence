import pandas as pd
import psycopg2
import pygrametl
from pygrametl.tables import Dimension, FactTable

# Chargement

agents = pd.read_csv(r"C:\2éme BI\S2\Modélisation Multidimensionnelles et Entrepôts de Données\projet\agents.csv")
clients = pd.read_csv(r"C:\2éme BI\S2\Modélisation Multidimensionnelles et Entrepôts de Données\projet\clients.csv")
appels = pd.read_csv(r"C:\2éme BI\S2\Modélisation Multidimensionnelles et Entrepôts de Données\projet\appels.csv")

# Nettoyage
appels['duree_appel'] = appels['duree_appel'].fillna(appels['duree_appel'].mean())
appels['temps_attente'] = appels['temps_attente'].fillna(appels['temps_attente'].mean())
appels = appels.drop_duplicates()

median = appels['duree_appel'].median()
appels['duree_appel'] = appels['duree_appel'].apply(
    lambda x: median if x < 0 or x > 60 else x
)

# Fusion
data = appels.merge(agents, on='id_agent') \
             .merge(clients, on='id_client')

# Temps
data['date_appel'] = pd.to_datetime(data['date_appel'])
data['jour'] = data['date_appel'].dt.day
data['mois'] = data['date_appel'].dt.month
data['annee'] = data['date_appel'].dt.year
data['heure'] = data['date_appel'].dt.hour

# Connexion PostgreSQL
from getpass import getpass

connection = psycopg2.connect(
    host="localhost",
    port="5433",
    database="call",
    user="postgres",
    password=getpass("Mot de passe PostgreSQL : ")
)

wrapper = pygrametl.ConnectionWrapper(connection)

# Dimensions
dim_agent = Dimension(
    name='dim_agent',
    key='id_agent',
    attributes=['nom', 'equipe', 'experience_annees']
)

dim_client = Dimension(
    name='dim_client',
    key='id_client',
    attributes=['sexe', 'age', 'region']
)

dim_temps = Dimension(
    name='dim_temps',
    key='id_temps',
    attributes=['date_appel', 'jour', 'mois', 'annee', 'heure']
)

dim_type = Dimension(
    name='dim_type_appel',
    key='id_type',
    attributes=['type_appel']
)

# Fact
fact = FactTable(
    name='fact_appel',
    keyrefs=['id_agent', 'id_client', 'id_temps', 'id_type'],
    measures=['duree_appel', 'temps_attente', 'satisfaction_client']
)

# ETL
for _, row in data.iterrows():

    agent_key = dim_agent.ensure({
        'id_agent': row['id_agent'],
        'nom': row['nom'],
        'equipe': row['equipe'],
        'experience_annees': row['experience_annees']
    })

    client_key = dim_client.ensure({
        'id_client': row['id_client'],
        'sexe': row['sexe'],
        'age': row['age'],
        'region': row['region']
    })

    temp_key = dim_temps.ensure({
        'date_appel': row['date_appel'],
        'jour': row['jour'],
        'mois': row['mois'],
        'annee': row['annee'],
        'heure': row['heure']
    })

    type_key = dim_type.ensure({
        'id_type': abs(hash(row['type_appel'])) % 10000,
        'type_appel': row['type_appel']
    })

    fact.insert({
        'id_agent': agent_key,
        'id_client': client_key,
        'id_temps': temp_key,
        'id_type': type_key,
        'duree_appel': row['duree_appel'],
        'temps_attente': row['temps_attente'],
        'satisfaction_client': row['satisfaction_client']
    })

# Commit
wrapper.commit()

# Export Excel
query = """
SELECT f.*, 
       a.nom, 
       c.sexe, c.age, c.region,
       t.date_appel, t.mois, t.annee,
       ty.type_appel
FROM fact_appel f
JOIN dim_agent a ON f.id_agent = a.id_agent
JOIN dim_client c ON f.id_client = c.id_client
JOIN dim_temps t ON f.id_temps = t.id_temps
JOIN dim_type_appel ty ON f.id_type = ty.id_type
"""

df = pd.read_sql(query, connection)
df.to_excel("resultat_call_center.xlsx", index=False)

print("✅ ETL + Excel OK")

connection.close()

import matplotlib.pyplot as plt


fig, axs = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle("Dashboard Call Center", fontsize=16)

# ======================
# 1. Appels par mois
# ======================
appels_mois = df.groupby('mois')['id_appel'].count()
axs[0, 0].bar(appels_mois.index, appels_mois.values)
axs[0, 0].set_title("Appels par mois")
axs[0, 0].set_xlabel("Mois")
axs[0, 0].set_ylabel("Nb appels")

# ======================
# 2. Type appel
# ======================
type_appel = df['type_appel'].value_counts()
axs[0, 1].bar(type_appel.index, type_appel.values)
axs[0, 1].set_title("Type d'appel")

# ======================
# 3. Région
# ======================
region = df['region'].value_counts()
axs[0, 2].bar(region.index, region.values)
axs[0, 2].set_title("Appels par région")

# ======================
# 4. Satisfaction par agent
# ======================
top_agents = df.groupby('nom')['satisfaction_client'].mean().sort_values()
axs[1, 0].barh(top_agents.index, top_agents.values)
axs[1, 0].set_title("Satisfaction par agent")

# ======================
# 5. Relation attente vs satisfaction
# ======================
axs[1, 1].scatter(df['temps_attente'], df['satisfaction_client'])
axs[1, 1].set_title("Attente vs Satisfaction")
axs[1, 1].set_xlabel("Temps attente")
axs[1, 1].set_ylabel("Satisfaction")


axs[1, 2].axis('off')

plt.tight_layout()
plt.show()