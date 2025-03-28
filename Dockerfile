FROM python:3.9-slim

RUN apt-get update 
#RUN apt-get install portaudio19-dev -y
RUN apt-get install build-essential -y
RUN apt-get install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y
# copie tout ce qui se trouve en local
COPY . .

# INSTALLATION DES DEPENDANCES
RUN pip install -r requirements.txt
# expose le port
EXPOSE 80
CMD ["python3", "mochi-mochi-modular.py"]