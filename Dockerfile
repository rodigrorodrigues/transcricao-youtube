FROM python:3.11-slim

# Instalando curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Configurando diretório de trabalho
WORKDIR /app

# Copiando os arquivos de dependências
COPY requirements.txt .

# Instalando dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiando o código da aplicação
COPY main.py .

# Expondo a porta da aplicação
EXPOSE 9199

# Configurando variáveis de ambiente
ENV PORT=9199
ENV DEBUG=False

# Comando para iniciar a aplicação
CMD ["python", "main.py"]

# Comando para iniciar a aplicação
CMD ["python", "main.py"]
