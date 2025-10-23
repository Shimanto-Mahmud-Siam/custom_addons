// Simple working chatbot for Odoo
(function() {
    'use strict';

    function init() {
        console.log('Starting chatbot initialization...');
        
        // Force chatbot to be on top of everything
        function forceTopPriority() {
            var chatbot = document.getElementById('chatbot');
            var chatToggle = document.getElementById('chatToggle');
            
            if (chatbot) {
                chatbot.style.zIndex = '2147483647';
                chatbot.style.position = 'fixed';
                chatbot.style.pointerEvents = 'auto';
            }
            
            if (chatToggle) {
                chatToggle.style.zIndex = '2147483647';
                chatToggle.style.position = 'fixed';
                chatToggle.style.pointerEvents = 'auto';
            }
            
            // Lower z-index of competing elements
            var gridItems = document.querySelectorAll('.o_grid_item, .o_grid_item_image, .o_colored_level');
            for (var i = 0; i < gridItems.length; i++) {
                gridItems[i].style.zIndex = '1';
            }
        }
        
        // Apply immediately and repeatedly to ensure it stays on top
        forceTopPriority();
        setInterval(forceTopPriority, 1000); // Check every second
        
        var sendBtn = document.getElementById('sendBtn');
        var chatInput = document.getElementById('chatInput');
        var messagesContainer = document.getElementById('messagesContainer');
        var chatbot = document.getElementById('chatbot');
        var chatToggle = document.getElementById('chatToggle');
        var toggleBtn = document.getElementById('toggleChat');
        
        console.log('Found elements:', {
            sendBtn: !!sendBtn,
            chatInput: !!chatInput, 
            messagesContainer: !!messagesContainer,
            chatbot: !!chatbot,
            chatToggle: !!chatToggle,
            toggleBtn: !!toggleBtn
        });
        
        if (!sendBtn || !chatInput || !messagesContainer) {
            console.error('Missing required elements');
            return;
        }

        var isMinimized = true;

        // Hide welcome message
        var welcomeMsg = document.getElementById('welcomeMessage');
        
        function addMessage(text, isUser) {
            if (welcomeMsg) {
                welcomeMsg.style.display = 'none';
            }
            
            var msgDiv = document.createElement('div');
            msgDiv.style.cssText = 'display: flex; margin-bottom: 12px; ' + 
                (isUser ? 'justify-content: flex-end;' : 'justify-content: flex-start;');
            
            var bubble = document.createElement('div');
            bubble.style.cssText = 
            'max-width: 75%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-wrap: break-word; margin-bottom: 8px; ' + 
            (isUser 
                ? 'background: #3A3A3A; color: #F5F5F5;'      // user bubble
                : 'background: #2A2A2A; color: #EDEDED;');   // bot bubble

            
            
            // Convert \n to <br> for proper line breaks
            var htmlText = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
            bubble.innerHTML = htmlText;
            msgDiv.appendChild(bubble);
            messagesContainer.appendChild(msgDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            return msgDiv;
        }

        function sendMessage() {
            var message = chatInput.value.trim();
            if (!message) return;
            
            console.log('Sending message:', message);
            
            // Add user message
            addMessage(message, true);
            
            // Clear input and show loading
            chatInput.value = '';
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending...';
            
            var loadingMsg = addMessage('🤖 Thinking...', false);
            
            // Make request
            fetch('/chatbot/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { message: message },
                    id: Date.now()
                })
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                console.log('Response received:', data);
                
                // Remove loading message
                messagesContainer.removeChild(loadingMsg);
                
                // Add bot response with clean formatting
                var result = data.result || data;
                var responseText;
                
                if (result.error || result.success === false) {
                    responseText = '❌ ' + (result.error || 'Query failed');
                    if (result.query) {
                        responseText += '\n\n💡 SQL: ' + result.query;
                    }
                } else if (result.success === true) {
                    responseText = '✅ ' + result.message + '\n\n';
                    
                    if (result.results && result.results.length > 0) {
                        responseText += '📋 Results:\n';
                        
                        // Helper function to format values nicely
                        function formatValue(key, value) {
                            // Handle null/undefined
                            if (value === null || value === undefined || value === 'N/A') {
                                return 'N/A';
                            }
                            
                            // Handle JSON objects (like name field with translations)
                            if (typeof value === 'object' && value !== null) {
                                // Try to extract English name
                                if (value.en_US) return value.en_US;
                                if (value.en_us) return value.en_us;
                                // Fallback to first available value
                                var keys = Object.keys(value);
                                if (keys.length > 0) return value[keys[0]];
                                return JSON.stringify(value);
                            }
                            
                            // Format price fields with currency
                            if ((key.includes('price') || key.includes('cost')) && typeof value === 'number') {
                                return '₹' + value.toLocaleString('en-IN', {minimumFractionDigits: 0, maximumFractionDigits: 0});
                            }
                            
                            return value;
                        }
                        
                        // Format results cleanly
                        result.results.forEach(function(row, index) {
                            responseText += '\n' + (index + 1) + '. ';
                            var fields = [];
                            for (var key in row) {
                                if (row.hasOwnProperty(key)) {
                                    var displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, function(l){ return l.toUpperCase(); });
                                    var displayValue = formatValue(key, row[key]);
                                    fields.push(displayKey + ': ' + displayValue);
                                }
                            }
                            responseText += fields.join(' • ');
                        });
                        
                        // Don't show SQL query in user-facing results (keep it clean)
                        // if (result.query) {
                        //     responseText += '\n\n💡 Query: ' + result.query;
                        // }
                    }
                } else {
                    responseText = '❓ Unexpected response format';
                }
                
                addMessage(responseText, false);
            })
            .catch(function(error) {
                console.error('Network error:', error);
                
                // Remove loading message
                messagesContainer.removeChild(loadingMsg);
                
                // Add error message
                addMessage('❌ Network error: ' + error.message, false);
            })
            .finally(function() {
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send';
                chatInput.focus();
            });
        }

        // Ensure initial minimized state visibility
        if (chatbot) chatbot.style.display = 'none';
        if (chatToggle) chatToggle.style.display = 'flex';

        // Toggle chat visibility
        function toggleChat() {
            if (isMinimized) {
                // Show chat
                if (chatbot) chatbot.style.display = 'flex';
                if (chatToggle) chatToggle.style.display = 'none';
                isMinimized = false;
            } else {
                // Hide chat
                if (chatbot) chatbot.style.display = 'none';
                if (chatToggle) chatToggle.style.display = 'flex';
                isMinimized = true;
            }
        }

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        // Toggle functionality
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggleChat);
        }
        if (chatToggle) {
            chatToggle.addEventListener('click', toggleChat);
        }
        
        console.log('Chatbot initialized successfully!');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also try initialization after a short delay to ensure Odoo has fully loaded
    setTimeout(init, 1000);
})();