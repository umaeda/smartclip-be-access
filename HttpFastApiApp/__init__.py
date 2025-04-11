import logging
import azure.functions as func

# Importa a sua instância do app FastAPI (ajuste o caminho se necessário)
# Supondo que sua instância se chama 'app' e está em 'app/__init__.py'
from app import app as fastapi_app

async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """
    Ponto de entrada da Azure Function que envolve a aplicação FastAPI.
    """
    logging.info(f"Python HTTP trigger function processed a request for route: {req.route_params.get('route')}")

    # Passa a requisição para a aplicação FastAPI usando o AsgiMiddleware
    return await func.AsgiMiddleware(fastapi_app).handle_async(req, context)
