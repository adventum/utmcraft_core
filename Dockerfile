FROM python:3.11-slim-buster

RUN pip install --upgrade pip

RUN mkdir -p /home/utmcraft
RUN groupadd utmcraft && useradd -g utmcraft utmcraft

ARG APP_HOME=/home/utmcraft/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY utmcraft $APP_HOME
COPY ./requirements_prod.txt $APP_HOME
COPY ./deploy/entrypoint.sh $APP_HOME

RUN apt update && apt install -y netcat
RUN pip install --upgrade -r requirements_prod.txt
RUN python manage.py makemigrations
RUN chmod +x $APP_HOME/entrypoint.sh
RUN chown -R utmcraft:utmcraft $APP_HOME

USER utmcraft

ENTRYPOINT ["/home/utmcraft/web/entrypoint.sh"]
