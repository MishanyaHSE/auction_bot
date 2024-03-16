FROM python:3.9.5
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p photos
ARG CLEAR_DB
ENV CLEAR_DB=${CLEAR_DB}
COPY run_bot.sh /run_bot.sh
RUN chmod +x /run_bot.sh
CMD ["/run_bot.sh"]
