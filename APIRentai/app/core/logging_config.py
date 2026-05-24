import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'app_file': {
            'class': 'logging.FileHandler',
            'filename': '/app/logs/app.log',
            'formatter': 'default',
        },
        'kafka_file': {
            'class': 'logging.FileHandler',
            'filename': '/app/logs/kafka.log',
            'formatter': 'default',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        'uvicorn': {
            'handlers': ['app_file', 'console'],
            'level': 'INFO',
        },
        'fastapi': {
            'handlers': ['app_file', 'console'],
            'level': 'INFO',
        },
        
        'kafka_service': {
            'handlers': ['kafka_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'aiokafka': {
            'handlers': ['kafka_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['app_file', 'console'],
    },
}

def setup_logging():
    """Aplica a configuração de logging."""
    logging.config.dictConfig(LOGGING_CONFIG)