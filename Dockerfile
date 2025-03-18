FROM python:3.9.6-slim

# mise à jour de l'environnement
RUN apt-get update 
# copie tout ce qui se trouve en local
COPY . .

# INSTALLATION DES DEPENDANCES
RUN pip install -r requirements.txt
# expose le port
EXPOSE 80
CMD [ "python3", "mochi-mochi-modular" ]