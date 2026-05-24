import random
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentValidatorService:
    async def validate(self, file_content: bytes):
        '''Valida o documento usando uma IA mockada - Apenas uma simulação'''
        score = round(random.uniform(0.6, 1.0), 2) 
        
        return {
            "is_valid": score >= settings.AI_CONFIDENCE_THRESHOLD,
            "score": score,
            "provider": "mock-ia-service",
            "threshold_applied": settings.AI_CONFIDENCE_THRESHOLD
        }

document_validator = DocumentValidatorService()