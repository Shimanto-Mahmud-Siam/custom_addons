{
    'name': 'Chatbot SQL Integration',
    'version': '1.0',
    'summary': 'LLM-powered chatbot using Ollama SQLCoder to query PostgreSQL data',
    'depends': ['website'],
    'data': ['views/chatbot_template.xml'],
    'assets': {
        'web.assets_frontend': [
            'chatbot_sql/static/src/js/chatbot_widget.js',
        ],
    },
}
