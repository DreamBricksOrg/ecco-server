"""Ponto de entrada principal da aplicação OBS Controller API"""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.core.config import get_settings
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )