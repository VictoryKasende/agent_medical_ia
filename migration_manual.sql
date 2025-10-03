# Fichier de migration SQL pour PostgreSQL/SQLite
# À exécuter après avoir mis à jour les modèles Django

# ===== Modifications FicheConsultation =====

# Ajouter les nouveaux champs pour les hypothèses
ALTER TABLE chat_ficheconsultation ADD COLUMN hypothese_patient_medecin TEXT NULL;
ALTER TABLE chat_ficheconsultation ADD COLUMN analyses_proposees TEXT NULL;

# Modifier les choix de coloration (nécessite mise à jour des données existantes)
# Note: Les enum Django sont gérés au niveau application, pas base de données

# ===== Nouveau modèle FicheReference =====
CREATE TABLE chat_fichereference (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite
    -- id SERIAL PRIMARY KEY,              -- PostgreSQL
    fiche_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    url TEXT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'other',
    authors VARCHAR(500) NULL,
    year INTEGER NULL,
    journal VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiche_id) REFERENCES chat_ficheconsultation (id) ON DELETE CASCADE
);

CREATE INDEX idx_fichereference_fiche ON chat_fichereference (fiche_id);
CREATE INDEX idx_fichereference_source ON chat_fichereference (source);
CREATE INDEX idx_fichereference_created ON chat_fichereference (created_at);

# ===== Nouveau modèle LabResult =====
CREATE TABLE chat_labresult (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite
    -- id SERIAL PRIMARY KEY,              -- PostgreSQL
    fiche_id INTEGER NOT NULL,
    type_analyse VARCHAR(100) NOT NULL,
    valeur VARCHAR(50) NOT NULL,
    unite VARCHAR(20) NULL,
    valeurs_normales VARCHAR(100) NULL,
    date_prelevement DATE NOT NULL,
    laboratoire VARCHAR(255) NULL,
    fichier VARCHAR(100) NULL,
    commentaire TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiche_id) REFERENCES chat_ficheconsultation (id) ON DELETE CASCADE
);

CREATE INDEX idx_labresult_fiche ON chat_labresult (fiche_id);
CREATE INDEX idx_labresult_date ON chat_labresult (date_prelevement);
CREATE INDEX idx_labresult_type ON chat_labresult (type_analyse);

# ===== Nouveau modèle FicheAttachment =====
CREATE TABLE chat_ficheattachment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite
    -- id SERIAL PRIMARY KEY,              -- PostgreSQL
    fiche_id INTEGER NOT NULL,
    file VARCHAR(100) NOT NULL,
    kind VARCHAR(20) NOT NULL DEFAULT 'other',
    note TEXT NULL,
    uploaded_by_id INTEGER NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiche_id) REFERENCES chat_ficheconsultation (id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES authentication_customuser (id) ON DELETE SET NULL
);

CREATE INDEX idx_ficheattachment_fiche ON chat_ficheattachment (fiche_id);
CREATE INDEX idx_ficheattachment_kind ON chat_ficheattachment (kind);
CREATE INDEX idx_ficheattachment_uploaded ON chat_ficheattachment (uploaded_by_id);

# ===== Modifications modèle Appointment =====
ALTER TABLE chat_appointment ADD COLUMN consultation_mode VARCHAR(20) NOT NULL DEFAULT 'distanciel';
ALTER TABLE chat_appointment ADD COLUMN location_note TEXT NULL;

# ===== Insertion de données de test (optionnel) =====

# Exemples de références bibliographiques
INSERT INTO chat_fichereference (fiche_id, title, source, authors, year, journal, url) 
SELECT 
    1,  -- ID d'une fiche existante
    'Management of Hypertension in Adults',
    'has',
    'Haute Autorité de Santé',
    2024,
    'Recommandations HAS',
    'https://www.has-sante.fr'
WHERE EXISTS (SELECT 1 FROM chat_ficheconsultation WHERE id = 1);

# Exemples de résultats de laboratoire
INSERT INTO chat_labresult (fiche_id, type_analyse, valeur, unite, valeurs_normales, date_prelevement, laboratoire)
SELECT 
    1,  -- ID d'une fiche existante
    'Glycémie à jeun',
    '0.95',
    'g/L',
    '0.70 - 1.10',
    DATE('now'),
    'Laboratoire Central'
WHERE EXISTS (SELECT 1 FROM chat_ficheconsultation WHERE id = 1);

# ===== Vérifications post-migration =====

# Vérifier que les tables ont été créées
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chat_%';

# Vérifier les contraintes
PRAGMA foreign_key_list(chat_fichereference);
PRAGMA foreign_key_list(chat_labresult);
PRAGMA foreign_key_list(chat_ficheattachment);

# Statistiques
SELECT 
    'chat_ficheconsultation' as table_name, COUNT(*) as count FROM chat_ficheconsultation
UNION ALL
SELECT 
    'chat_fichereference' as table_name, COUNT(*) as count FROM chat_fichereference
UNION ALL
SELECT 
    'chat_labresult' as table_name, COUNT(*) as count FROM chat_labresult
UNION ALL
SELECT 
    'chat_ficheattachment' as table_name, COUNT(*) as count FROM chat_ficheattachment;

# ===== Notes de migration =====
/*
1. Sauvegardez votre base de données avant d'exécuter ces commandes
2. Adaptez les types de données selon votre SGBD (SQLite/PostgreSQL)
3. Les migrations Django officielles sont préférables quand possible
4. Testez d'abord sur un environnement de développement

Pour créer les migrations Django automatiquement :
python manage.py makemigrations chat --name=add_new_models
python manage.py migrate

Pour forcer la recréation des migrations :
python manage.py makemigrations chat --empty --name=manual_migration
# Puis éditer le fichier généré avec les operations nécessaires
*/