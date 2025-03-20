import azure.functions as func
from mangum import Mangum
from main import app as fastapi_app

# Create a Mangum handler to properly handle the routing
# This will help avoid the double slash issue
handler = Mangum(fastapi_app, lifespan="off")

# Create the Azure Functions app
app = func.AsgiFunctionApp(app=handler, http_auth_level=func.AuthLevel.ANONYMOUS)