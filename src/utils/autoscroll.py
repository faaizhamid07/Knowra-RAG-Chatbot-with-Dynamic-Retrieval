"""Auto-scroll component for Streamlit chat interface."""

AUTO_SCROLL_JS = """
<script>
(function() {
    try {
        const pDoc = window.parent.document;
        if (!pDoc) return;

        function scrollToBottom() {
            try {
                // 1. Scroll chat history wrapper if present
                const chatHistory = pDoc.querySelector('.chat-history-container');
                if (chatHistory && chatHistory.scrollHeight > chatHistory.clientHeight) {
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }

                // 2. Scroll all potential Streamlit scroll containers
                const containers = [
                    pDoc.querySelector('[data-testid="stAppViewContainer"]'),
                    pDoc.querySelector('section.main'),
                    pDoc.querySelector('[data-testid="stMain"]'),
                    pDoc.querySelector('[data-testid="stMainBlockContainer"]'),
                    pDoc.documentElement,
                    pDoc.body,
                    pDoc.scrollingElement
                ];

                for (const el of containers) {
                    if (el && el.scrollHeight > el.clientHeight) {
                        el.scrollTop = el.scrollHeight;
                    }
                }

                // 3. Scroll the newest chat message into view
                const chatMessages = pDoc.querySelectorAll('[data-testid="stChatMessage"]');
                if (chatMessages && chatMessages.length > 0) {
                    const lastMessage = chatMessages[chatMessages.length - 1];
                    lastMessage.scrollIntoView({ behavior: 'auto', block: 'end' });
                }
            } catch (err) {
                // Silent catch for sandboxed environments
            }
        }

        // Immediate and staggered scrolls on render
        scrollToBottom();
        setTimeout(scrollToBottom, 50);
        setTimeout(scrollToBottom, 150);
        setTimeout(scrollToBottom, 300);

        // Track intentional user scrolling
        let userScrolledUp = false;
        const mainContainer = pDoc.querySelector('[data-testid="stAppViewContainer"]') ||
                              pDoc.querySelector('section.main') ||
                              pDoc.body;

        if (mainContainer) {
            pDoc.addEventListener('wheel', function(e) {
                if (e.deltaY < 0) {
                    userScrolledUp = true;
                } else if (e.deltaY > 0) {
                    const dist = mainContainer.scrollHeight - mainContainer.scrollTop - mainContainer.clientHeight;
                    if (dist < 100) {
                        userScrolledUp = false;
                    }
                }
            }, { passive: true });

            pDoc.addEventListener('keydown', function(e) {
                if (e.key === 'PageUp' || e.key === 'Home') {
                    userScrolledUp = true;
                }
                if (e.key === 'PageDown' || e.key === 'End') {
                    userScrolledUp = false;
                    scrollToBottom();
                }
            }, { passive: true });

            let touchStartY = 0;
            pDoc.addEventListener('touchstart', function(e) {
                if (e.touches && e.touches.length > 0) {
                    touchStartY = e.touches[0].clientY;
                }
            }, { passive: true });

            pDoc.addEventListener('touchmove', function(e) {
                if (e.touches && e.touches.length > 0) {
                    const currentY = e.touches[0].clientY;
                    if (currentY > touchStartY + 10) {
                        userScrolledUp = true; // Swiped down to see earlier content
                    }
                }
            }, { passive: true });
        }

        // MutationObserver triggers scroll on every typewriter character/line update
        const observer = new MutationObserver(function() {
            if (!userScrolledUp) {
                scrollToBottom();
            }
        });

        const targetNode = pDoc.querySelector('[data-testid="stAppViewContainer"]') ||
                           pDoc.querySelector('section.main') ||
                           pDoc.body;

        if (targetNode) {
            observer.observe(targetNode, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }

        // Auto-disconnect observer after 45 seconds to keep lifecycle clean
        setTimeout(function() {
            observer.disconnect();
        }, 45000);

    } catch (e) {
        // Fallback silently
    }
})();
</script>
"""
