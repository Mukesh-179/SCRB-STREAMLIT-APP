FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=3000

EXPOSE 3000

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=3000", "--server.headless=true", "--browser.gatherUsageStats=false"]