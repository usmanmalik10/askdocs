import uvicorn

from runtime import run

if __name__ == "__main__":
    server = uvicorn.Server(uvicorn.Config("main:app", host="127.0.0.1", port=8000, log_level="info"))
    run(server.serve())
