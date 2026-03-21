#TODO: Añadir excepciones personalizadas para errores comunes en la aplicación, como errores de validación, errores de base de datos, etc.
# Estas excepciones pueden heredar de una clase base común para facilitar su manejo global en los controladores y middleware.
class AppError(Exception):
    """Clase base para todas las excepciones de negocio de ContractAI."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        # Es vital llamar al __init__ de la clase padre Exception
        super().__init__(self.message)
