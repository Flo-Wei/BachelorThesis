from Backend.api import app
import uvicorn


def main():
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None,  # Disable uvicorn's logging config
        access_log=True   # Keep access logs but use your format
    )


if __name__ == "__main__":
    main()