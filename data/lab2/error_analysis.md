# Lab 2 - Analyse des erreurs

Les seuils ont été choisis sur tuning. Seul le groupe evaluation fournit une mesure indépendante. Les alertes ne prouvent pas un plagiat.

## Résumé des classifications

| Méthode | Groupe | FP | FN |
|---|---|---:|---:|
| token | tuning | 3 | 0 |
| token | evaluation | 1 | 0 |
| ast | tuning | 0 | 0 |
| ast | evaluation | 0 | 0 |

## Études de cas

### Cas 1: pair-037

- Méthode : token
- Groupe : evaluation
- Erreur : faux_positif
- Score : 0.1429
- Seuil : 0.1111
- Explication : Les deux solutions partagent un modèle autorisé. Cette ressemblance ne prouve pas un plagiat.
- Lignes concernées : 5-5 et 5-5

### Cas 2: pair-031

- Méthode : token
- Groupe : tuning
- Erreur : faux_positif
- Score : 0.4286
- Seuil : 0.1111
- Explication : Les deux solutions partagent un modèle autorisé. Cette ressemblance ne prouve pas un plagiat.
- Lignes concernées : 4-4 et 4-4

### Cas 3: pair-034

- Méthode : token
- Groupe : tuning
- Erreur : faux_positif
- Score : 0.1579
- Seuil : 0.1111
- Explication : Deux solutions indépendantes peuvent avoir des structures communes.
- Lignes concernées : 2-2 et 2-2

### Cas 4: pair-035

- Méthode : token
- Groupe : tuning
- Erreur : faux_positif
- Score : 0.1154
- Seuil : 0.1111
- Explication : Deux solutions indépendantes peuvent avoir des structures communes.
- Lignes concernées : 5-6 et 2-3
