


----------------------------------------------------FR VERSION---------------------------------------------




# TP Tkinter - Gestion des Emprunts d'une Bibliotheque

Ce projet est une application de bureau Python realisee avec Tkinter et SQLite.
Elle permet a un bibliothecaire de gerer les livres, les membres et les
emprunts d'une bibliotheque a travers une interface graphique claire.


La base de donnees locale `bibliotheque.db` est creee automatiquement au
premier lancement.

## Connexion Administrateur

Un compte administrateur par defaut est cree automatiquement :

- Nom utilisateur : `admin`
- Mot de passe : `admin123`

## Fonctionnalites Principales

- Gestion des livres : ajouter, modifier, supprimer, rechercher et afficher.
- Gestion des membres : ajouter, modifier, supprimer, rechercher et afficher.
- Gestion des emprunts : choisir un livre, choisir un membre, enregistrer un
  emprunt et enregistrer le retour d'un livre.
- Gestion des retards : statut automatique, nombre de jours de retard et
  penalite de `2 DH` par jour.
- Notifications : alerte au demarrage pour les retards et les retours
  imminents.
- Export PDF : rapport complet avec design et rapport dedie aux retards,
  enregistres dans le dossier `resultat`.
- Export CSV : rapport complet de la bibliotheque et rapport dedie aux retards.
- Interface multilingue : selecteur `FR / EN` dans l'application.
- Statistiques bonus : stock total, exemplaires disponibles, emprunts actifs,
  retards et livres les plus empruntes.

## Regles Metier

- Un livre ne peut pas etre emprunte si aucun exemplaire n'est disponible.
- Un membre ne peut pas emprunter deux fois le meme livre sans le rendre.
- Un livre ne peut pas etre supprime s'il a un emprunt actif.
- Un membre ne peut pas etre supprime s'il a un emprunt actif.
- La date d'emprunt est generee automatiquement.
- La date de retour prevue est generee automatiquement avec une duree de prêt
  de 14 jours.

## Interface

- Theme clair base sur la palette de couleurs demandee dans le sujet.
- Resolution par defaut : `1920 x 1080`.
- Fenetre principale centree.
- Tableaux, formulaires, onglets, boutons et ecran de connexion stylises.
- Interface agrandie pour un affichage confortable en 1080p.
- Icone personnalisee adaptee au projet de bibliotheque.
- Ecran de connexion administrateur avant l'acces a l'application.

## Structure du Projet

- `main.py` : code source principal de l'application.
- `bibliotheque.db` : base de donnees locale SQLite.
- `assets/` : fichiers de l'icone de l'application.
- `resultat/` : resultats PDF generes .
- `README.md` : documentation du projet.

## Organisation du Code

- `DatabaseManager` : gere toutes les operations SQLite.
- `LoginWindow` : affiche l'interface de connexion administrateur.
- `LibraryApp` : gere l'interface Tkinter et les evenements utilisateur.
- `PdfReport` : genere les rapports PDF avec design sans bibliotheque externe.

## Createur

Cette application a ete creee par **Ilyas El Bahi**.






------------------------------------------------ENG VERSION------------------------------------------------






# Tkinter Project - Library Loan Management

This project is a Python desktop application built with Tkinter and SQLite.
It helps a librarian manage books, members, and library loans through a clear
graphical interface.


The local SQLite database `bibliotheque.db` is created automatically when the
application starts for the first time.

## Administrator Login

A default administrator account is created automatically:

- Username: `admin`
- Password: `admin123`

## Main Features

- Book management: add, edit, delete, search, and display books.
- Member management: add, edit, delete, search, and display members.
- Loan management: select a book, select a member, register a loan, and return
  a borrowed book.
- Late return management: automatic status, number of late days, and a penalty
  of `2 DH` per late day.
- Notifications: startup alert for late loans and upcoming returns.
- PDF export: full designed report and late-loan report, saved in the
  `resultat` folder.
- CSV export: full library report and late-loan report.
- Multilingual interface: `FR / EN` selector inside the application.
- Bonus statistics: total stock, available copies, active loans, late loans,
  and most borrowed books.

## Business Rules

- A book cannot be borrowed if no copy is available.
- A member cannot borrow the same book twice without returning it first.
- A book cannot be deleted while it has an active loan.
- A member cannot be deleted while they have an active loan.
- The loan date is generated automatically.
- The expected return date is generated automatically with a 14-day loan period.

## Interface

- Light theme based on the color palette required in the project statement.
- Default resolution: `1920 x 1080`.
- Centered main window.
- Styled tables, forms, tabs, buttons, and login screen.
- Enlarged UI for comfortable use on a 1080p display.
- Custom library icon.
- Administrator login screen before accessing the application.

## Project Structure

- `main.py`: main application source code.
- `bibliotheque.db`: local SQLite database.
- `assets/`: application icon files.
- `resultat/`: generated PDF results.
- `README.md`: project documentation.

## Code Organization

- `DatabaseManager`: handles all SQLite operations.
- `LoginWindow`: displays the administrator login interface.
- `LibraryApp`: manages the Tkinter interface and user events.
- `PdfReport`: generates designed PDF reports without external libraries.

## Creator

This application was created by **Ilyas El Bahi**.
