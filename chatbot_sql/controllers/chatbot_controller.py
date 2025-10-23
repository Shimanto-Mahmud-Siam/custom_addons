from odoo import http
from odoo.http import request
import requests
import logging

OLLAMA_URL = "http://localhost:11434/api/generate"
_logger = logging.getLogger(__name__)

class ChatbotController(http.Controller):

    @http.route('/chatbot/test-db', type='json', auth='public', methods=['POST'])
    def test_database_connection(self, **post):
        """Test endpoint to verify database connection works"""
        try:
            # Use Odoo's database connection
            cr = request.env.cr
            
            # Test query
            test_query = "SELECT name FROM res_partner LIMIT 3;"
            cr.execute(test_query)
            rows = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            
            data = [dict(zip(columns, row)) for row in rows]
            return {"query": test_query, "result": data, "status": "success"}
        except Exception as e:
            return {"error": f"Database connection error: {e}", "status": "failed"}

    @http.route('/chatbot/test-sql', type='json', auth='public', methods=['POST'])
    def test_sql_execution(self, **post):
        """Direct SQL test endpoint - bypasses Ollama"""
        sql_query = post.get('query', 'SELECT name FROM res_partner LIMIT 3;')
        
        try:
            # Use Odoo's database connection
            cr = request.env.cr
            
            # Only allow SELECT queries for security
            if not sql_query.strip().upper().startswith('SELECT'):
                return {"error": "Only SELECT queries are allowed for security reasons", "query": sql_query}
            
            cr.execute(sql_query)
            rows = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            
            data = [dict(zip(columns, row)) for row in rows]
            return {"query": sql_query, "result": data, "count": len(data)}
        except Exception as e:
            return {"error": f"SQL execution error: {e}", "query": sql_query}

    @http.route('/chatbot/query', type='json', auth='public', methods=['POST'])
    def chatbot_query(self, **post):
        user_message = post.get('message')
        if not user_message:
            return {"error": "No message provided."}

        _logger.info(f"Chatbot query received: {user_message}")

        # Step 1: Ask SQLCoder to generate SQL
        payload = {
            "model": "sqlcoder",
            "prompt": f"Generate a PostgreSQL SELECT query for: {user_message}. Only return the SQL query, no explanation.",
            "stream": False
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            raw_response = response_data.get('response', '').strip()
            
            if not raw_response:
                return {"error": "Ollama returned an empty response"}
            
            # Extract SQL query from the response (remove timestamps and extra text)
            import re
            # Look for SELECT statement, allowing for multiline and various formats
            sql_match = re.search(r'(SELECT.*?;)', raw_response, re.IGNORECASE | re.DOTALL)
            if not sql_match:
                # Try without semicolon
                sql_match = re.search(r'(SELECT.*?)(?:\n|$)', raw_response, re.IGNORECASE | re.DOTALL)
            
            if sql_match:
                sql_text = sql_match.group(1).strip()
                # Clean up extra whitespace and newlines
                sql_text = ' '.join(sql_text.split())
                if not sql_text.endswith(';'):
                    sql_text += ';'
            else:
                # Fallback: use the raw response if no SELECT found
                sql_text = raw_response.strip()
                if not sql_text.upper().startswith('SELECT'):
                    return {"error": "Generated response doesn't contain a valid SELECT query", "raw_response": raw_response}
                
            _logger.info(f"Generated SQL: {sql_text}")
            
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434 and the sqlcoder model is installed."}
        except requests.exceptions.Timeout:
            return {"error": "Ollama request timed out. Please try again."}
        except Exception as e:
            _logger.error(f"Ollama error: {e}")
            return {"error": f"Ollama error: {e}"}

        # Step 2: Execute SQL using Odoo's database connection
        try:
            # Use Odoo's database connection
            cr = request.env.cr
            
            # Only allow SELECT queries for security
            sql_text_clean = sql_text.strip()
            if not sql_text_clean.upper().startswith('SELECT'):
                return {"error": "Only SELECT queries are allowed for security reasons", "query": sql_text}
            
            cr.execute(sql_text)
            rows = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            
            data = [dict(zip(columns, row)) for row in rows]
            _logger.info(f"Chatbot SQL query executed: {sql_text}")
            return {"query": sql_text, "result": data}
        except Exception as e:
            _logger.error(f"Chatbot SQL execution error: {e}")
            return {"error": f"SQL execution error: {e}", "query": sql_text}
