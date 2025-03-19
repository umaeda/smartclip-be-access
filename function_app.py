import azure.functions as func
from mangum import Mangum

from main import app

# Crie um manipulador HTTP do Azure Functions que direciona as requisições para o FastAPI
handler = Mangum(app, lifespan="off")

# Defina a função do Azure Functions
async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Cada solicitação HTTP será processada por esta função"""
    return await handler(req, context)