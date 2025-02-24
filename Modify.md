     Follow-up Questions for Unclear Items
    
    Implementation Strategy
     - Modify the API response structure to include a "confidence" score for each extracted field
     - Add a "clarifications_needed" field in the response to store unclear items
     - Create a modal/dialog UI component to handle follow-up questions
     - Store intermediate results in session while waiting for clarifications

    Benefits:
    Better accuracy in data extraction
    Interactive user experience
    Improved data quality

    Interactive Q&A on Results Page

    Implementation Strategy
         - Add a new section to results.html for Q&A
     - Create a chat-like interface with:
       - Input field for questions
       - Display area for conversation history
       - Context preservation of the original analysis
     - Add endpoints:
       /api/ask (for new questions)
       /api/regenerate (for regenerating analysis)
     - Store conversation history in session

    UI Components needed:
    Question input field with submit button
    Chat/conversation display area
    "Regenerate Analysis" button
    Loading states for both Q&A and regeneration

    

