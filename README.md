# paco-backend

### Generelle Info
***
Nach dem Pullen des Projektes am Besten eine .env Datei im Root Directory erstellen. In dieser stehen die Passwörter und Nutzernamen drin. Diese wird nicht gepusht.
Sobald die Installation abgeschlossen ist und alle Container gestartet wurden stehen folgende Adressen zur Verfügung:

URL für MongoDB:
http://localhost:8081/
Beim ersten öffen mit dem MONGOEXPRESS_LOGIN und MONGOEXPRESS_PASSWORD anmelden.


URL für die Flasks-API:
http://localhost:5000/api

#### .env
***
In der Datei sollten folgende Variablen enthalten sein:
```
MONGO_ROOT_USER=user
MONGO_ROOT_PASSWORD=password
MONGOEXPRESS_LOGIN=dev
MONGOEXPRESS_PASSWORD=dev
MONGODB_USERNAME=apiuser
MONGODB_PASSWORD=apipassword
MONGODB_HOST=mongodb
```

## Installation
***
```
$ docker-compose up -d
```
Danach generiert Docker alles mögliche und installiert die nötigen Flask packages.

### Einen nicht root User für die Datenbank erstellen
***
```
$ docker exec -it mongo bash
$ root@786b840a5df7:/# mongo -u admin -p
> use webapp
> db.createUser({user: 'apiuser', pwd: 'apipassword', roles: [{role: 'readWrite', db: 'webapp'}]})
```
Den gewählten Nutzernamen in der .env Datei bei MONGODB_USERNAME eintragen und das Passwort bei MONGODB_PASSWORD.
Danach nochmal alle Docker Container neu starten.
