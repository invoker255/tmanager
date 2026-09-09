import logging
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        view_name = context['view'].__class__.__name__
        logger.critical(
            f'Unhandled Error in {view_name}: {str(exc)}',
            exc_info=True
        )
    return response
