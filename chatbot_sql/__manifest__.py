{
    'name': 'Chatbot SQL Integration',
    'version': '1.0',
    'summary': 'LLM-powered chatbot using Ollama SQLCoder to query PostgreSQL data',
    'depends': ['website'],
    'installable': True,
    'data': [
        'views/chatbot_template.xml',
    ],
    'license': 'LGPL-3',
}
