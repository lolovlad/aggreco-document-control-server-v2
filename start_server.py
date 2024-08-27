from uvicorn import run
from server.main import app


run(app, host="localhost", port=8000)
