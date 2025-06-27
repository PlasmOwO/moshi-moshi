# moshi-moshi
Academic project for speech-to-text and translation between Japanese-French.

Ce projet est réalisé sous AWS :
Les fichiers principaux sont :

* api-aws.py : Serveur fastAPI à lancer sous lightsail, il s'occupe de se connecter a AWS Transcribe et AWS Translate
* client-mioni2.py : Client permettant d'envoyer une requête websocket au serveur
* web_moshi2.py : Interface du client qui sert à connecter le micro puis utiliser le client-mioni pour intéragir avec le serveur
* web_moshi2.js : javascript de la page web
* index.html : HTML de la page Web


Architecture : Nous utilisons Lightsail pour héberger le code API-AWS.py
De plus automatiquement, le lightsail effectue un pull de code (similaire à un CI/CD)

Le client doit juste lancer le code  web_moshi2.py et cliquer pour acceter le micro
