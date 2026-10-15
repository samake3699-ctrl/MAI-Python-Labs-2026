# Lab 2 - Rapport de performances

## Comparaison avant / après optimisation

| Entrées | Avant (s) | Après (s) | Gain (%) |
|---:|---:|---:|---:|
| 100 | 0.494 | 0.169 | 65.8 |
| 1000 | 4.172 | 1.769 | 57.6 |
| 5000 | 16.794 | 8.285 | 50.7 |

## Méthodologie

- Trois répétitions par taille.
- Mesures réalisées sur 100, 1000 et 5000 entrées.
- Données synthétiques reproductibles.
- Comparaison avec une référence fixe.
- Lecture JSONL progressive.
- Temps mesuré avec time.perf_counter().
- Allocations Python suivies avec tracemalloc.
- Génération des données exclue du chronométrage.

## Optimisation

Les caractéristiques Token et AST de la référence sont calculées une seule fois par exécution.

## Analyse cProfile

- `extract_ast_features` : 1001 appels, 4.069 s cumulées.
- `dump` : 17906 appels, 2.520 s cumulées.
- `extract_code_tokens` : 1001 appels, 0.556 s cumulées.

## Limites

- Le jeu de données est synthétique.
- Les mesures ne couvrent pas toutes les paires.
- tracemalloc ne mesure pas toute la RAM Windows.
- Les temps cumulés cProfile se chevauchent.
- Une similarité élevée ne prouve pas un plagiat.
