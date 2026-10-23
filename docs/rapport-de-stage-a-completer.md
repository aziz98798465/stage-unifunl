# Rapport de stage — brouillon à compléter

> Ce document est une trame. Remplacer les champs entre crochets par des faits confirmés. Ne pas conserver une activité que tu n’as pas réellement effectuée.

## Page de garde

- **Nom et prénom :** [À COMPLÉTER]
- **Établissement / formation :** [À COMPLÉTER]
- **Entreprise :** Unifunl [à confirmer selon la convention]
- **Tuteur en entreprise :** [À COMPLÉTER]
- **Encadrant pédagogique :** [À COMPLÉTER]
- **Période réelle :** du [JJ/MM/AAAA] au [JJ/MM/AAAA]
- **Titre :** Développement d’outils web de scraping et de vérification de liens

## Remerciements

[À rédiger seulement pour les personnes que tu souhaites réellement remercier.]

## 1. Présentation et contexte

[Présenter l’entreprise, l’équipe, le contexte du stage et le besoin tel que validé avec l’encadrant. Ne pas déduire l’organisation à partir du seul dépôt.]

## 2. Objectifs et périmètre

Le dépôt contient un scraper de produits adapté à Books to Scrape, un exemple Playwright pour une page JavaScript, une API Flask et un vérificateur de liens cassés. Il comprend des interfaces web, des exports CSV/JSON et des tests automatisés.

[Confirmer que ces outils correspondent au besoin réellement confié et préciser les tâches éventuellement effectuées hors dépôt.]

## 3. Réalisation technique

### 3.1 Scraping statique

Requests et BeautifulSoup récupèrent et analysent le HTML. L’extracteur Books to Scrape collecte titre, prix, devise et image, suit une pagination bornée et exporte JSON/CSV.

### 3.2 Pages dynamiques

Le script Playwright visite Quotes to Scrape, attend le rendu JavaScript et extrait texte, auteur et tags.

### 3.3 API et interfaces

Flask expose les interfaces et les routes documentées dans `README.md`. L’interface affiche les produits, le rapport de liens et l’analyse IA facultative.

### 3.4 Vérificateur de liens et sécurité

Le vérificateur contrôle les URL, suit les redirections de façon contrôlée, borne les réponses et propose des exports. Une limite résiduelle DNS rebinding est décrite dans le rapport technique.

### 3.5 Analyse LLM

Le module OpenAI optionnel demande un résumé, une catégorie et des champs structurés. Il impose une taille d’entrée, un schéma de sortie, une limite locale d’appels et un timeout.

**Validation externe :** [À COMPLÉTER après qu’une clé autorisée a été configurée. Aucun appel réel au fournisseur n’a été effectué lors de la préparation de cette trame.]

## 4. Organisation et difficultés

- Méthode de travail : [À COMPLÉTER]
- Difficultés rencontrées : [À COMPLÉTER selon ton expérience]
- Corrections demandées par l’équipe : [À COMPLÉTER; ne pas inventer]
- Revue avec le tuteur : [date et retours réels, ou indiquer qu’elle n’a pas eu lieu]

## 5. Tests et résultats

- Tests automatisés : [mettre le dernier résultat réellement observé]
- Essais réseau réalisés : [site, date, limites, résultat réellement obtenu]
- Analyse LLM : [résultats réels, ou « non testée faute de clé »]
- Déploiement : [environnement et URL uniquement si déployé et autorisé]

## 6. Compétences et bilan personnel

- Compétences techniques acquises : [À COMPLÉTER par le stagiaire]
- Compétences de collaboration : [À COMPLÉTER]
- Ce qui a bien fonctionné : [À COMPLÉTER]
- Améliorations envisagées : [À COMPLÉTER]

## Conclusion

[Résumer ce qui a été réellement livré, les limites et les apprentissages personnels.]

## Annexes

- Liste des 30 tâches et leur statut vérifié : `docs/verification-taches-stage.md`.
- Démonstration : `docs/presentation-demo.md`.
- Installation et utilisation : `README.md`.
