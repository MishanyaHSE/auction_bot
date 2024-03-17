FROM python:3.9.5
ENV TZ=Europe/Moscow
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p photos
ARG CLEAR_DB
ENV CLEAR_DB=${CLEAR_DB}
COPY run_bot.sh /app/run_bot.sh
RUN chmod +x /app/run_bot.sh
CMD ["/app/run_bot.sh"]
