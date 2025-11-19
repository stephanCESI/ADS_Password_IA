# Système intelligent d’évaluation et de génération de mots de passe robustes à l’aide de l’IA

## Problématique
Les méthodes classiques d’évaluation de mots de passe permettent-elles réellement d’estimer leur robustesse ?  
Un modèle d’apprentissage automatique peut-il mieux prédire la vulnérabilité ou la “devinabilité” d’un mot de passe, et permettre la création de mots de passe plus sûrs que les générateurs traditionnels ?

## Description
Ce projet d’ADS (Application de la Démarche Scientifique) est réalisé dans le cadre de la 4ème année à l’école d’ingénieurs CESI, spécialité informatique avec orientation cybersécurité. Il a été motivé par l’observation que les failles liées aux mots de passe restent une cause majeure d’intrusion dans les systèmes d’information. Malgré l’existence d’outils d’évaluation et de générateurs automatiques, de nombreux utilisateurs continuent d’adopter des mots de passe faibles, et les méthodes classiques d’évaluation ne reflètent pas toujours la vulnérabilité réelle face aux techniques modernes de compromission. Ces méthodes traditionnelles se basent principalement sur des règles simples comme la longueur ou la diversité des caractères, ce qui limite leur capacité à détecter des patterns exploités par les attaquants.

L’objectif de ce projet est de concevoir un **système d’évaluation intelligent** capable d’attribuer un score de robustesse à chaque mot de passe testé, sur une échelle de 0 à 100. Le système combine les techniques classiques normalisées avec un modèle d’apprentissage automatique entraîné sur un dataset construit à partir de sources variées. Il est capable d’analyser les patterns problématiques, de mesurer l’entropie et de proposer une interprétation des faiblesses du mot de passe, tout en évitant que certaines règles soient surreprésentées dans le modèle.

La seconde partie du projet consiste à comparer différentes méthodes de génération de mots de passe, afin d’évaluer leur robustesse à l’aide du modèle développé. L’ensemble sera intégré dans un **POC web local**, permettant à l’utilisateur d’évaluer, comprendre et améliorer ses mots de passe de manière simple et interactive.

## Mots-clés
- Cybersécurité  
- Intelligence artificielle  
- Robustesse (de mots de passe)  
- Évaluation  
- Génération
