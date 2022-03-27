# paco-backend

### Generelle Info
***
Nach dem Pullen des Projektes am Besten eine .env Datei im Root Directory erstellen. In dieser stehen die Passwörter und Nutzernamen drin. Diese wird nicht gepusht.
Sobald die Installation abgeschlossen ist und alle Container gestartet wurden stehen folgende Adressen zur Verfügung:

URL für MongoDB:
http://localhost:8081/



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
Danach nochmal alle Docker-Container neustarten.

### Flask-Server starten

Um den Flask-Server zu starten, muss man sich im Projektordner `paco` befinden.

Der Flask-Server im Development-Modus lässt sich über den folgenden Befehl starten:
```
flusk run
```

Vor dem Start des Servers muss der Name einer Flask-Anwendungsdatei dem Flask-Server über eine Umgebungsvariable zugänglich gemacht werden:
```
export FLASK_APP=debug_app
```

Damit die Graphen generiert werden können, sollen die folgenden Dienste laufen (als Docker-Container oder in der Konsole):

- paco-frontend
- paco-backend-graph-api
- paco-data-extraction (für JXES-Dateien)
