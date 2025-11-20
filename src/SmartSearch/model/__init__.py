from .models import  AI_Interface

ai_interviewer = AI_Interface()
predict = ai_interviewer.next

__all__ = [
	"predict"
]
