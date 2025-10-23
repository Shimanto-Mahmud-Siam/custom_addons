from odoo import http
from odoo.http import request
import requests
import logging
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
_logger = logging.getLogger(__name__)

class ChatbotController(http.Controller):

    def _generate_fallback_sql(self, user_message):
        """Generate SQL using pattern matching for common jewelry queries"""
        message = user_message.lower().strip()
        
        # Pattern matching for common jewelry queries
        if 'gold' in message and ('under' in message or '<' in message or 'below' in message):
            # Extract price if mentioned
            price_match = re.search(r'(\d+)', message)
            price = price_match.group(1) if price_match else '50000'
            return f"SELECT name, list_price, final_sale_price FROM product_template WHERE (name::text ILIKE '%gold%') AND list_price < {price} AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'silver' in message and ('under' in message or '<' in message or 'below' in message):
            price_match = re.search(r'(\d+)', message)
            price = price_match.group(1) if price_match else '20000'
            return f"SELECT name, list_price, final_sale_price FROM product_template WHERE (name::text ILIKE '%silver%') AND list_price < {price} AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'under' in message or 'below' in message or '<' in message:
            price_match = re.search(r'(\d+)', message)
            price = price_match.group(1) if price_match else '15000'
            return f"SELECT name, list_price, final_sale_price FROM product_template WHERE list_price < {price} AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'above' in message or 'over' in message or '>' in message:
            price_match = re.search(r'(\d+)', message)
            price = price_match.group(1) if price_match else '50000'
            return f"SELECT name, list_price, final_sale_price FROM product_template WHERE list_price > {price} ORDER BY list_price ASC LIMIT 10;"
            
        elif 'between' in message:
            prices = re.findall(r'(\d+)', message)
            if len(prices) >= 2:
                return f"SELECT name, list_price, final_sale_price FROM product_template WHERE list_price BETWEEN {prices[0]} AND {prices[1]} ORDER BY list_price DESC LIMIT 10;"
                
        elif 'bangles' in message or 'bangle' in message:
            return "SELECT name, list_price, final_sale_price, labor_cost FROM product_template WHERE (name::text ILIKE '%bangle%') AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'earring' in message or 'earrings' in message:
            return "SELECT name, list_price, final_sale_price, labor_cost FROM product_template WHERE (name::text ILIKE '%earring%') AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'bracelet' in message:
            return "SELECT name, list_price, final_sale_price FROM product_template WHERE (name::text ILIKE '%bracelet%') AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'gold' in message:
            return "SELECT name, list_price, final_sale_price, gold_silver_base_price FROM product_template WHERE (name::text ILIKE '%gold%') AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'silver' in message:
            return "SELECT name, list_price, final_sale_price FROM product_template WHERE (name::text ILIKE '%silver%') AND list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'expensive' in message or 'highest' in message or 'most' in message:
            return "SELECT name, list_price, final_sale_price FROM product_template WHERE list_price > 0 ORDER BY list_price DESC LIMIT 10;"
            
        elif 'cheap' in message or 'lowest' in message or 'affordable' in message:
            return "SELECT name, list_price, final_sale_price FROM product_template WHERE list_price > 0 ORDER BY list_price ASC LIMIT 10;"
            
        elif 'labor' in message or 'cost' in message:
            return "SELECT name, list_price, final_sale_price, labor_cost FROM product_template WHERE labor_cost > 0 ORDER BY labor_cost DESC LIMIT 10;"
            
        # Default query - show recent products with prices
        return "SELECT name, list_price, final_sale_price FROM product_template WHERE list_price > 0 ORDER BY list_price DESC LIMIT 10;"

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
        sql_query = post.get('query', 'SELECT login FROM res_users LIMIT 3;')
        
        try:
            cr = request.env.cr
            
            # Security check
            if not sql_query.strip().upper().startswith('SELECT'):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed",
                    "query": sql_query
                }
            
            cr.execute(sql_query)
            rows = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            
            # Format results cleanly
            if not rows:
                return {
                    "success": True,
                    "message": "No results found",
                    "count": 0,
                    "query": sql_query
                }
            
            # Convert to clean format
            data = []
            for row in rows:
                clean_row = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    clean_row[col] = "N/A" if value is None else value
                data.append(clean_row)
            
            return {
                "success": True,
                "count": len(data),
                "results": data,
                "query": sql_query,
                "message": f"Found {len(data)} result(s)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Query failed: {str(e).split('LINE')[0].strip()}",
                "query": sql_query
            }

    @http.route('/chatbot/query', type='json', auth='public', methods=['POST'])
    def chatbot_query(self, **post):
        user_message = post.get('message')
        if not user_message:
            return {"error": "No message provided."}

        _logger.info(f"Chatbot query received: {user_message}")

        # Step 1: Ask SQLCoder to generate SQL with jewelry-specific schema
        jewelry_schema = """
        JEWELRY DATABASE SCHEMA:
        - product_template: main product table (id, name, list_price, compare_list_price, final_sale_price, gold_silver_base_price, gold_silver_base_price_bhori, labor_cost, procost)
        - res_partner: customers/suppliers (id, name, email, phone, company_name)
        - res_users: system users (id, login, email)
        
        IMPORTANT: Use 'product_template' for all jewelry/product queries. Price columns: list_price, final_sale_price, gold_silver_base_price, labor_cost.
        """
        
        payload = {
            "model": "sqlcoder",
            "prompt": f"{jewelry_schema}\n\nUser request: {user_message}\n\nRules:\n1. Write ONLY a PostgreSQL SELECT query\n2. Use product_template table for all jewelry queries\n3. No explanations, no comments, no Python code\n4. Start with SELECT and end with semicolon\n5. Example: SELECT name, list_price FROM product_template WHERE list_price < 15000;\n\nSQL Query:",
            "stream": False
        }

        sql_text = None
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            raw_response = response_data.get('response', '').strip()
            
            if not raw_response:
                _logger.warning("Ollama returned empty response, using fallback")
                sql_text = self._generate_fallback_sql(user_message)
            else:
                # Clean SQL extraction pipeline - remove ALL junk
                _logger.info(f"Raw SQLCoder response: {raw_response}")
                
                # Aggressive cleanup - remove everything that's not essential SQL
                clean_response = raw_response.strip()
                
                # Remove timestamps, extra parentheses, notes, hints, explanations, tags
                cleanup_patterns = [
                    r'<s>\s*',                         # Remove <s> tags
                    r'</s>\s*',                        # Remove </s> tags  
                    r'```sql\s*',                      # Remove ```sql
                    r'```\s*',                         # Remove ```
                    r'\d{4}-\d{2}-\d{2}.*$',           # Remove timestamps
                    r'\)\)+.*$',                       # Remove )) and everything after  
                    r'Note:.*$',                       # Remove notes
                    r'HINT:.*$',                       # Remove hints
                    r'This query.*$',                  # Remove explanations
                    r'--.*$',                          # Remove SQL comments
                    r'/\*.*?\*/',                      # Remove /* comments */
                    r'(?i)explanation.*$',             # Remove explanation text
                    r'(?i)might generate.*$',          # Remove warning text
                ]
                
                for pattern in cleanup_patterns:
                    clean_response = re.sub(pattern, '', clean_response, flags=re.MULTILINE | re.DOTALL)
                
                # Extract only the SQL SELECT statement - be very strict  
                sql_patterns = [
                    r'SQL Query:\s*(SELECT[^;]+;)',                      # After "SQL Query:" label
                    r'(SELECT\s+[^;]*?\s+FROM\s+product_template[^;]*?;)',  # Complete SELECT with product_template
                    r'(SELECT\s+[^;]*?\s+FROM\s+\w+[^;]*?;)',           # Complete SELECT with semicolon
                    r'(SELECT.*?;)',                                     # Any SELECT statement with semicolon
                    r'(SELECT.*?)(?=\n|$)',                             # Any SELECT statement to end of line
                    r'(SELECT\s+[^;]*?\s+FROM\s+\w+[^;]*?)(?=\s*[;)]|$)',  # SELECT...FROM, stop at ; or )
                ]
                
                for pattern in sql_patterns:
                    match = re.search(pattern, clean_response, re.IGNORECASE | re.DOTALL)
                    if match:
                        sql_text = match.group(1).strip()
                        break
                
                if sql_text:
                    # Final cleanup of extracted SQL
                    sql_text = re.sub(r'\s+', ' ', sql_text)           # Normalize spaces
                    sql_text = re.sub(r'\)+\s*$', '', sql_text)        # Remove trailing )
                    
                    # Fix common table name issues for jewelry database
                    sql_text = re.sub(r'\buser\b', 'res_users', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\busers\b', 'res_users', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bpartner\b', 'res_partner', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bpartners\b', 'res_partner', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bproduct\b', 'product_template', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bproducts\b', 'product_template', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bjewelry\b', 'product_template', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bjewellery\b', 'product_template', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bitem\b', 'product_template', sql_text, flags=re.IGNORECASE)
                    sql_text = re.sub(r'\bitems\b', 'product_template', sql_text, flags=re.IGNORECASE)
                    
                    # Ensure proper SQL ending
                    if not sql_text.endswith(';'):
                        sql_text += ';'
                        
                    _logger.info(f"Cleaned SQL: {sql_text}")
                else:
                    _logger.warning("Could not extract SQL from Ollama response, using fallback")
                    sql_text = self._generate_fallback_sql(user_message)
            
        except requests.exceptions.ConnectionError:
            _logger.warning("Ollama not available, using fallback SQL generation")
            sql_text = self._generate_fallback_sql(user_message)
        except requests.exceptions.Timeout:
            _logger.warning("Ollama timeout, using fallback SQL generation")
            sql_text = self._generate_fallback_sql(user_message)
        except Exception as e:
            _logger.warning(f"Ollama error: {e}, using fallback SQL generation")
            sql_text = self._generate_fallback_sql(user_message)
            
        # If SQLCoder returned empty or junk, use fallback
        if not sql_text or not sql_text.strip().upper().startswith('SELECT'):
            _logger.info("SQLCoder returned invalid response, using fallback")
            sql_text = self._generate_fallback_sql(user_message)

        # Step 2: Execute SQL and format results cleanly
        try:
            cr = request.env.cr
            
            # Security check
            if not sql_text.strip().upper().startswith('SELECT'):
                return {"error": "Only SELECT queries are allowed", "query": sql_text}
            
            cr.execute(sql_text)
            rows = cr.fetchall()
            columns = [desc[0] for desc in cr.description]
            
            # Format results in a clean, readable way
            if not rows:
                return {
                    "success": True,
                    "message": "No results found",
                    "count": 0,
                    "query": sql_text
                }
            
            # Convert to clean format
            data = []
            for row in rows:
                clean_row = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Clean up the value display
                    if value is None:
                        clean_row[col] = "N/A"
                    elif isinstance(value, str):
                        clean_row[col] = value.strip()
                    else:
                        clean_row[col] = value
                data.append(clean_row)
            
            # Return clean, formatted results
            _logger.info(f"Query executed successfully: {len(data)} results")
            return {
                "success": True,
                "count": len(data),
                "results": data[:10],  # Limit to first 10 results to avoid overwhelming UI
                "query": sql_text,
                "message": f"Found {len(data)} result(s)" + (" (showing first 10)" if len(data) > 10 else "")
            }
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"SQL execution failed: {error_msg}")
            
            # If SQL execution fails (wrong columns, wrong table, etc), try fallback
            if any(keyword in error_msg.lower() for keyword in ['does not exist', 'no such column', 'syntax error']):
                _logger.warning("SQL execution error detected, retrying with fallback")
                sql_text = self._generate_fallback_sql(user_message)
                
                try:
                    cr.execute(sql_text)
                    rows = cr.fetchall()
                    columns = [desc[0] for desc in cr.description]
                    
                    if not rows:
                        return {
                            "success": True,
                            "message": "No results found",
                            "count": 0,
                            "query": sql_text
                        }
                    
                    data = []
                    for row in rows:
                        clean_row = {}
                        for i, col in enumerate(columns):
                            value = row[i]
                            if value is None:
                                clean_row[col] = "N/A"
                            elif isinstance(value, str):
                                clean_row[col] = value.strip()
                            else:
                                clean_row[col] = value
                        data.append(clean_row)
                    
                    _logger.info(f"Fallback query executed successfully: {len(data)} results")
                    return {
                        "success": True,
                        "count": len(data),
                        "results": data[:10],
                        "query": sql_text,
                        "message": f"Found {len(data)} result(s)" + (" (showing first 10)" if len(data) > 10 else "")
                    }
                except Exception as fallback_error:
                    _logger.error(f"Fallback also failed: {str(fallback_error)}")
                    return {
                        "success": False,
                        "error": f"Query failed: {str(fallback_error).split('LINE')[0].strip()}",
                        "query": sql_text
                    }
            
            # Return original error if not a schema issue
            return {
                "success": False,
                "error": f"Query failed: {error_msg.split('LINE')[0].strip()}",
                "query": sql_text
            }
