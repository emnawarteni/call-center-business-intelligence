CREATE TABLE Dim_Agent (
    id_agent INT PRIMARY KEY,
    nom VARCHAR(50),
    equipe VARCHAR(10),
    experience_annees INT
);
CREATE TABLE Dim_Client (
    id_client INT PRIMARY KEY,
    sexe VARCHAR(10),
    age INT,
    region VARCHAR(50)
);
CREATE TABLE Dim_Temps (
    id_temps SERIAL PRIMARY KEY,
    date_appel TIMESTAMP,
    jour INT,
    mois INT,
    annee INT,
    heure INT
);
CREATE TABLE Dim_Type_Appel (
    id_type SERIAL PRIMARY KEY,
    type_appel VARCHAR(50)
);
CREATE TABLE Fact_Appel (
    id_appel INT PRIMARY KEY,
    id_agent INT,
    id_client INT,
    id_temps INT,
    id_type INT,
    duree_appel FLOAT,
    temps_attente FLOAT,
    appel_resolu INT,
    satisfaction_client INT,
    FOREIGN KEY (id_client) REFERENCES Dim_Client(id_client),
    FOREIGN KEY (id_temps) REFERENCES Dim_Temps(id_temps),
    FOREIGN KEY (id_type) REFERENCES Dim_Type_Appel(id_type)
);