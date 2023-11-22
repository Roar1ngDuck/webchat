FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY . .

COPY requirements.txt ./
RUN apk --no-cache add postgresql-dev gcc python3-dev musl-dev
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_RUN_PORT=8001
ENV FLASK_RUN_HOST=0.0.0.0
ENV DB_URL=postgresql://postgres:postgres@db/webchat

CMD ["flask", "run"]