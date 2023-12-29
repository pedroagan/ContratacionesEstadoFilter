# ContratacionesEstadoFilter
Application to download and filter the tenders stored in "Contrataciones del Estado" (Spain) 

## Configuration

To configure the application it is necessary create a configuration file with the following structure:

```
[EMAIL_CONF]
EMAIL_TO = {EMAIL_TO}
EMAIL_ENABLED = {SEND_EMAIL_ENABLED_DISABLED (True/False)}
EMAIL_SERVER = {EMAIL_SERVER}
EMAIL_PORT = {EMAIL_PORT}
EMAIL_FROM = {EMAIL_ADDRESS}
EMAIL_PASSWD = {EMAIL_PASSWORD}

[EMAIL_MSG]
EMAIL_SUBJECT = {EMAIL_SUBJECT}
EMAIL_TEXT = {ROUTE_TO_FILE_WITH_TEXT}
```

To filter the data, it is necessary to add a filters file:

```
administracion={filter_1}
administracion={filter_2}
organo={filter_3}
organo={filter_4}
title={filter_5}
title={filter_6}
```

## Execution

To execute the application it is necessary launch the following command:

```
python3 ContratacionesEstado.py --config config.ini
```
