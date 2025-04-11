# Use uma imagem base oficial Python para Azure Functions
# Escolha a versão do Python compatível com suas dependências (3.11 ou 3.12)
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

# Instala o FFmpeg e suas dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Cria um diretório não-root para a aplicação
RUN mkdir -p /home/app
WORKDIR /home/app

# Define variáveis de ambiente necessárias para o Azure Functions
ENV AzureWebJobsScriptRoot=/home/app
ENV AzureFunctionsJobHost__Logging__Console__IsEnabled=true
ENV PYTHONUNBUFFERED=1

# Copia o arquivo de dependências e instala os pacotes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação para o diretório de trabalho
COPY . .

# Opcional: Se a sua fonte 'impact.ttf' estiver em 'assets/fonts/impact.ttf'
# Garanta que a pasta e o arquivo sejam copiados
# (O 'COPY . .' acima já deve fazer isso se a pasta 'assets' estiver na raiz)

# Expõe a porta que o Azure Functions usa internamente
EXPOSE 80