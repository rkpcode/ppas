from app.exceptions.base import PharmacyBaseException

class MedicineNotFoundError(PharmacyBaseException):
    def __init__(self, medicine_id: int | str):
        super().__init__(
            message=f"Medicine with identifier {medicine_id} not found.",
            code="MEDICINE_NOT_FOUND",
            status_code=404
        )

class InsufficientStockError(PharmacyBaseException):
    def __init__(self, medicine_name: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock for {medicine_name}. Requested: {requested}, Available: {available}",
            code="INSUFFICIENT_STOCK",
            status_code=400
        )
        
class AuthError(PharmacyBaseException):
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            status_code=status_code
        )
