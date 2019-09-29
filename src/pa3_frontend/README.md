# Frontend
The frontend consists of a django-app storing the results of the OCR in a database and serving them as a website.

## Ansible Playbook
- Copies the sources/secrets for mysql/proxy/frontend to the host
- builds the containers (proxy and frontend)
- runs the docker containers (mysql, proxy, frontend)

Modify through `frontend_directory` (where to keep the docker-source) and `server_url`.

## Docker
The container runs django and apache2. 
At the start, it also collects the static and updates the database.

The container only listens on 443, since the proxy listens and redirects on 80.

## Django
### Models
- **WaitingNumber**: The OCR-result. Where it comes from (`src`), when (`date`) and the `number`
- **WaitingNumberBatch**: Groups the numbers together, when a single recognizer runs OCR for multiple `src`es. 
- **NewestWaitingNumberBatch**: Contains the newest WaitingNumberBatch as a reference, for database-optimisation.
- **StatisticalData**: Compute the average for different periods. Store as sum and len, for optimisation.
### Sites
The app serves its data at the index (`/`) for users and has an 
API with 2 styles for autonomized access (`/api` and `/api2`).
Additionally, `/write` is the entrypoint for data from the recognizers.

### Settings
See the top of pa3_django/pa3/settings.py

You probably want to change `USER_TO_NAMES`, `DATABASES`, 
`OPENINGS`, `ALLOWED_HOSTS` and maybe `TIME_ZONE`.


### Write
To push data to the app, recognizers have to have the following fields in their requests:
- **user**: corresponds to the `USER_TO_NAMES` setting.
- **password**:  corresponds to the `RECOGNIZER_AUTH` setting. One password for all recognizers, 
since all are build from one container, so if one is compromised, probably all are.
- **ts**: timestamp from when the result is (now).
- **numbers**: Array of integers/digit-strings. Corresponds to the `USER_TO_NAMES` setting.
- **begin**: timestamp when the image was taken. Used to compute processing-time.

If there is an image in the request (usually when there is a new OCR-result), 
it has to be in the `raw_image` FILES-field.


### Utils
- **Cron**: calls maintenance-urls on the django regularly (update_news, update_statistics)
- **News**: The django-site also stores and displays news from the offices/places it runs OCR on, 
as it is often the only websites users access and can as such give additional information on the 
state of operations (maintenance, vacations, etc.).
- **Subsciptions**: TODO. Users should be able to register the number they're waiting on in the system, 
and the system tells them when it's their turn.

### Staticfiles
Using whitenoise to service staticfiles