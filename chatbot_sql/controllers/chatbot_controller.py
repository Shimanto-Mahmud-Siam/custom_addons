from odoo import http
from odoo.http import request
import requests
import logging
import json
import re
from functools import reduce

OLLAMA_URL = "http://localhost:11434/api/generate"
_logger = logging.getLogger(__name__)

class ChatbotController(http.Controller):

    def _generate_fallback_domain(self, user_message):
        """Generate safe Odoo domain filters using pattern matching rules"""
        message = user_message.lower().strip()
        
        # Check if this is a service-related query
        service_keywords = ['delivery', 'shipping', 'service', 'charge', 'fee']
        is_service_query = any(keyword in message for keyword in service_keywords)
        
        # Build domain filters dynamically
        domain = []
        
        # 1. Product type/material filters (gold, silver, bangles, bracelets, etc.)
        product_keywords = ['gold', 'silver', 'bangle', 'bracelet', 'earring', 'ring', 'necklace', 'chain']
        matched_keywords = []
        for keyword in product_keywords:
            if keyword in message:
                matched_keywords.append(keyword)
        
        # Add name filters for matched keywords (AND logic - product must match all keywords)
        for kw in matched_keywords:
            domain.append(['name', 'ilike', kw])
        
        # 2. Price constraints - extract ALL numbers (only for non-service queries)
        if not is_service_query:
            prices = re.findall(r'\b(\d+)\b', message)
            
            # Handle range queries
            if 'between' in message or 'range' in message or 'from' in message:
                if len(prices) >= 2:
                    price1, price2 = sorted([int(p) for p in prices[:2]])
                    domain.append(['list_price', '>=', price1])
                    domain.append(['list_price', '<=', price2])
                elif prices:
                    domain.append(['list_price', '<=', int(prices[0])])
                else:
                    domain.append(['list_price', '>=', 0])
            # Handle single constraints (under, within, below, above, over)
            else:
                # Find matching constraint keyword and operator
                constraint_map = {
                    'under': ('<=', 15000),
                    'within': ('<=', 15000),
                    'below': ('<=', 15000),
                    'above': ('>', 50000),
                    'over': ('>', 50000)
                }
                
                constraint_op = None
                default_price = None
                
                # Check for constraint keywords
                for keyword, (op, default) in constraint_map.items():
                    if keyword in message:
                        constraint_op = op
                        default_price = default
                        break
                
                # Apply constraint if found
                if constraint_op:
                    price_val = int(prices[-1]) if prices else default_price
                    domain.append(['list_price', constraint_op, price_val])
                    if constraint_op == '<=':  # For "under" constraints, ensure >= 0
                        domain.append(['list_price', '>=', 0])
                else:
                    # Default: show products with prices
                    domain.append(['list_price', '>=', 0])
        
        # 3. Service filter - only add if not already service query
        if is_service_query:
            domain.append(['type', '=', 'service'])
        else:
            domain.append(['type', '!=', 'service'])
        
        # 4. Special cases for labor cost - only if not service query
        if ('labor' in message or 'cost' in message) and not is_service_query:
            domain.append(['labor_cost', '>', 0])
        
        _logger.info(f"Generated fallback domain: {domain}")
        return domain

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


    @http.route('/chatbot/query', type='json', auth='public', methods=['POST'])
    def chatbot_query(self, **post):
        user_message = post.get('message')
        if not user_message:
            return {"error": "No message provided."}

        _logger.info(f"Chatbot query received: {user_message}")

        # Step 1: Ask LLM to generate structured JSON intent instead of SQL
        database_schema = """
        Database Schema:
        - product_template (id, name, list_price, final_sale_price, labor_cost, type)
        - res_partner (id, name, email, phone, company_name)
        - res_users (id, login, email)
        
        IMPORTANT: Use 'product.template' model for all product queries. Product types: 'consu' (consumable), 'service' (delivery/shipping), 'product' (stockable).
        """
        
        payload = {
            "model": "sqlcoder",
            "prompt": f"{database_schema}\n\nUser request: {user_message}\n\nCRITICAL RULES:\n1. Respond ONLY with a JSON object in the EXACT format below.\n2. Do not write SQL queries.\n3. Do not return product data.\n4. Return Odoo domain filters for searching.\n5. Product type 'service' should be excluded unless the user asks for 'delivery' or 'shipping'.\n\nREQUIRED JSON FORMAT (copy this structure exactly):\n{{\n  \"model\": \"product.template\",\n  \"filters\": [\n    [\"field_name\", \"operator\", \"value\"],\n    [\"list_price\", \">=\", 2000],\n    [\"list_price\", \"<=\", 8000]\n  ],\n  \"order\": \"list_price DESC\",\n  \"limit\": 10\n}}\n\nFor 'between X and Y' queries, use two separate filters: [\"list_price\", \">=\", X] and [\"list_price\", \"<=\", Y]\nFor 'under X' queries, use: [\"list_price\", \"<\", X]\nFor 'above X' queries, use: [\"list_price\", \">\", X]\nFor material searches, use: [\"name\", \"ilike\", \"material_name\"]\n\nJSON Response:",
            "stream": False
        }

        intent = None
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            raw_response = response_data.get('response', '').strip()
            
            if not raw_response:
                _logger.warning("Ollama returned empty response, using fallback")
                intent = None
            else:
                _logger.info(f"Raw LLM response: {raw_response}")
                
                # Try to parse JSON response
                try:
                    intent = json.loads(raw_response)
                    _logger.info(f"Parsed intent: {intent}")
                except json.JSONDecodeError as e:
                    _logger.warning(f"Failed to parse JSON from LLM: {e}, using fallback")
                    intent = None
            
        except requests.exceptions.ConnectionError:
            _logger.warning("Ollama not available, using fallback domain generation")
            intent = None
        except requests.exceptions.Timeout:
            _logger.warning("Ollama timeout, using fallback domain generation")
            intent = None
        except Exception as e:
            _logger.warning(f"Ollama error: {e}, using fallback domain generation")
            intent = None
            
        # Step 2: Validate intent and build safe domain
        try:
            # If LLM failed or returned invalid intent, use fallback
            if not intent or intent.get('model') != 'product.template':
                _logger.info("Using fallback domain generation")
                domain = self._generate_fallback_domain(user_message)
                order = 'list_price DESC'
                limit = 10
            else:
                # Validate LLM intent
                domain = intent.get('filters', [])
                if not isinstance(domain, list):
                    domain = []
                
                # Validate each filter is a list of 3 elements
                validated_domain = []
                for filter_item in domain:
                    if isinstance(filter_item, list) and len(filter_item) == 3:
                        validated_domain.append(filter_item)
                
                domain = validated_domain
                order = intent.get('order', 'list_price DESC')
                limit = min(intent.get('limit', 10), 50)  # Cap at 50 for performance
            
            # Add smart service filter if not already present
            service_keywords = ['delivery', 'shipping', 'service', 'charge', 'fee']
            is_service_query = any(keyword in user_message.lower() for keyword in service_keywords)
            
            # Check if service filter already exists
            has_service_filter = any(
                isinstance(f, list) and len(f) == 3 and f[0] == 'type' 
                for f in domain
            )
            
            if not has_service_filter:
                if is_service_query:
                    domain.append(['type', '=', 'service'])
                else:
                    domain.append(['type', '!=', 'service'])
            
            # Step 3: Safely execute the search using Odoo ORM
            products = request.env['product.template'].search(
                domain,
                order=order,
                limit=limit
            )
            
            # Step 4: Format results safely
            data = []
            for product in products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'list_price': product.list_price,
                    'final_sale_price': product.final_sale_price,
                    'product_url': f"/shop/product/{product.id}"
                }
                
                # Add labor_cost if it exists and is relevant
                if hasattr(product, 'labor_cost') and product.labor_cost:
                    product_data['labor_cost'] = product.labor_cost
                
                data.append(product_data)
            
            # Return clean, formatted results
            _logger.info(f"Query executed successfully: {len(data)} results")
            return {
                "success": True,
                "count": len(data),
                "results": data,
                "message": f"Found {len(data)} result(s)"
            }
            
        except Exception as e:
            _logger.error(f"Chatbot query failed: {e}")
            return {
                "success": False,
                "error": "I'm sorry, I couldn't process that request."
            }