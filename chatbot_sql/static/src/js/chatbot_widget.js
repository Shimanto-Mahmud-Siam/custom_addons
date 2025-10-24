// Simple working chatbot for Odoo
(function() {
    'use strict';

        function init() {
            console.log('Starting chatbot initialization...');
            
            // Load chat history from sessionStorage (safer than localStorage)
            function loadChatHistory() {
                try {
                    var savedHistory = sessionStorage.getItem('chatbot_history');
                    if (savedHistory) {
                        var history = JSON.parse(savedHistory);
                        var messagesContainer = document.getElementById('messagesContainer');
                        var welcomeMsg = document.getElementById('welcomeMessage');
                        
                        if (history.length > 0 && welcomeMsg) {
                            welcomeMsg.style.display = 'none';
                        }
                        
                        history.forEach(function(msg) {
                            var msgDiv = document.createElement('div');
                            msgDiv.style.cssText = 
                                'display: flex; margin-bottom: 12px;' +
                                (msg.isUser ? 'justify-content: flex-end;' : 'justify-content: flex-start;');

                            var bubble = document.createElement('div');
                            bubble.className = 'message-bubble ' + (msg.isUser ? 'message-user' : 'message-bot');
                            
                            if (msg.isUser) {
                                // Use textContent for user messages (XSS-safe)
                                bubble.textContent = msg.text;
                            } else {
                                // For bot messages, safely build HTML elements
                                var lines = msg.text.split('\n');
                                lines.forEach(function(line, index) {
                                    if (index > 0) {
                                        bubble.appendChild(document.createElement('br'));
                                    }
                                    
                                    // Check if line contains a product link
                                    var linkMatch = line.match(/<a href="([^"]+)"[^>]*>([^<]+)<\/a>/);
                                    if (linkMatch) {
                                        var link = document.createElement('a');
                                        link.href = linkMatch[1];
                                        link.textContent = linkMatch[2];
                                        link.target = '_blank';
                                        link.style.color = '#667eea';
                                        link.style.textDecoration = 'underline';
                                        bubble.appendChild(link);
                                        
                                        // Add the rest of the line after the link
                                        var remainingText = line.replace(/<a[^>]*>.*?<\/a>/, '').trim();
                                        if (remainingText) {
                                            var span = document.createElement('span');
                                            span.textContent = remainingText;
                                            bubble.appendChild(span);
                                        }
                                    } else {
                                        // Regular text line
                                        var span = document.createElement('span');
                                        span.textContent = line;
                                        bubble.appendChild(span);
                                    }
                                });
                            }
                            
                            msgDiv.appendChild(bubble);
                            messagesContainer.appendChild(msgDiv);
                        });
                        
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        console.log('Loaded', history.length, 'messages from history');
                    }
                } catch (e) {
                    console.error('Error loading chat history:', e);
                }
            }
            
            // Save chat history to sessionStorage (safer than localStorage)
            function saveChatHistory() {
                try {
                    var messagesContainer = document.getElementById('messagesContainer');
                    var messages = [];
                    
                    // Get all message divs (skip welcome message)
                    var messageDivs = messagesContainer.querySelectorAll('div[style*="display: flex"]');
                    messageDivs.forEach(function(msgDiv) {
                        var bubble = msgDiv.querySelector('div[style*="max-width: 75%"]');
                        if (bubble) {
                            var isUser = msgDiv.style.justifyContent === 'flex-end';
                            var text = bubble.textContent || bubble.innerText || '';
                            messages.push({
                                text: text,
                                isUser: isUser,
                                timestamp: Date.now()
                            });
                        }
                    });
                    
                    sessionStorage.setItem('chatbot_history', JSON.stringify(messages));
                    console.log('Saved', messages.length, 'messages to history');
                } catch (e) {
                    console.error('Error saving chat history:', e);
                }
            }
            
        
        var sendBtn = document.getElementById('sendBtn');
        var chatInput = document.getElementById('chatInput');
        var messagesContainer = document.getElementById('messagesContainer');
        var chatbot = document.getElementById('chatbot');
        var chatToggle = document.getElementById('chatToggle');
        var toggleBtn = document.getElementById('toggleChat');
        var clearHistoryBtn = document.getElementById('clearHistory');
        
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
            bubble.className = 'message-bubble ' + (isUser ? 'message-user' : 'message-bot');

            if (isUser) {
                // Use textContent for user messages to prevent XSS
                bubble.textContent = text;
            } else {
                // For bot messages, safely build HTML elements
                var lines = text.split('\n');
                lines.forEach(function(line, index) {
                    if (index > 0) {
                        bubble.appendChild(document.createElement('br'));
                    }
                    
                    // Check if line contains a product link
                    var linkMatch = line.match(/<a href="([^"]+)"[^>]*>([^<]+)<\/a>/);
                    if (linkMatch) {
                        var link = document.createElement('a');
                        link.href = linkMatch[1];
                        link.textContent = linkMatch[2];
                        link.target = '_blank';
                        link.style.color = '#667eea';
                        link.style.textDecoration = 'underline';
                        bubble.appendChild(link);
                        
                        // Add the rest of the line after the link
                        var remainingText = line.replace(/<a[^>]*>.*?<\/a>/, '').trim();
                        if (remainingText) {
                            var span = document.createElement('span');
                            span.textContent = remainingText;
                            bubble.appendChild(span);
                        }
                    } else {
                        // Regular text line
                        var span = document.createElement('span');
                        span.textContent = line;
                        bubble.appendChild(span);
                    }
                });
            }
            
            msgDiv.appendChild(bubble);
            messagesContainer.appendChild(msgDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Save chat history after adding message
            setTimeout(saveChatHistory, 100);
            
            return msgDiv;
        }

        function sendMessage() {
            var message = chatInput.value.trim();
            if (!message) return;
            
            console.log('Sending message:', message);
            
            // Store original send button HTML
            var originalSendBtnHTML = sendBtn.innerHTML;
            
            // Add user message
            addMessage(message, true);
            
            // Clear input and show loading
            chatInput.value = '';
            sendBtn.disabled = true;
            sendBtn.innerHTML = '⏳';
            
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
                            var productName = '';
                            var productUrl = '';
                            
                            for (var key in row) {
                                if (row.hasOwnProperty(key)) {
                                    if (key === 'name') {
                                        productName = formatValue(key, row[key]);
                                    } else if (key === 'product_url') {
                                        productUrl = row[key];
                                    } else {
                                        var displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, function(l){ return l.toUpperCase(); });
                                        var displayValue = formatValue(key, row[key]);
                                        fields.push(displayKey + ': ' + displayValue);
                                    }
                                }
                            }
                            
                            // Add product name as clickable link if URL exists
                            if (productUrl && productName) {
                                fields.unshift('<a href="' + productUrl + '" target="_blank" style="color: #667eea; text-decoration: underline;">' + productName + '</a>');
                            } else if (productName) {
                                fields.unshift('Name: ' + productName);
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
                sendBtn.innerHTML = originalSendBtnHTML;
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
        
        // Clear history functionality
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to clear the chat history?')) {
                    // Clear sessionStorage
                    sessionStorage.removeItem('chatbot_history');
                    
                    // Clear the messages container
                    messagesContainer.innerHTML = '';
                    
                    // Show welcome message again
                    var welcomeMsg = document.getElementById('welcomeMessage');
                    if (welcomeMsg) {
                        welcomeMsg.style.display = 'block';
                    }
                    
                    console.log('Chat history cleared');
                }
            });
        }
        
        // Load chat history on initialization
        loadChatHistory();
        
        console.log('Chatbot initialized successfully!');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();