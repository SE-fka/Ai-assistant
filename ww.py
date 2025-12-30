   def find_relevant_documents(self, query: str) -> list:
        """Find documents relevant to the query using the database"""
        try:
            # Use the database search function
            relevant_docs = db.search_documents(query, limit=3)
            
            # Format the results to match the expected structure
            formatted_docs = []
            for doc in relevant_docs:
                if doc and 'content' in doc:
                    formatted_docs.append({
                        'path': doc.get('file_path', 'database'),
                        'filename': doc.get('filename', 'Unknown'),
                        'relevance_score': doc.get('relevance_score', 0),
                        'content': doc.get('content', '')
                    })
            
            return formatted_docs
        except Exception as e:
            print(f"Error searching documents in database: {e}")
            return []
    
    def create_human_friendly_prompt(self, user_query: str, documents: list) -> list:
        """Create a human-friendly prompt that enforces proper formatting rules"""
        
        document_context = ""
        if documents:
            document_context = "\n\n**DOCUMENT CONTEXT (Use as Reference):**\n"
            for i, doc in enumerate(documents, 1):
                content = doc['content']
                # Extract meaningful content (first 1500 chars)
                sentences = content.split('.')
                key_content = '. '.join(sentences[:8])
                if len(sentences) > 8:
                    key_content += '...'
                
                document_context += f"\n**Document {i}: {doc['filename']}**\n{key_content}\n"
        
        # Strict formatting prompt
        system_prompt = f"""You are a helpful AI assistant. You MUST format ALL responses using proper markdown syntax. DO NOT use incorrect formatting like `-` followed by colons.

    # **MANDATORY FORMATTING RULES**

    ## **1. HEADINGS**
    - Use `#` for main title ONLY
    - Use `##` for major sections
    - Use `###` for subsections
    - **NEVER use `-` as headings**

    ## **2. LISTS**
    ### **Correct:**
        
    {document_context}

    # **CRITICAL: ENFORCE THESE RULES**

    1. **NEVER** use the format `- Item: Explanation`
    2. **ALWAYS** use proper markdown tables for comparisons
    3. **ALWAYS** use headings properly (##, ###)
    4. **ALWAYS** use bullet points correctly (`- item`)
    5. **ALWAYS** separate sections with line breaks
    6. **ALWAYS** use code blocks for examples
    7. **ALWAYS** maintain conversational tone

    # **DOCUMENT INTEGRATION**
    - Reference document information naturally in paragraphs
    - If documents provide specific technical details, mention them
    - If multiple documents conflict, acknowledge it
    - If no relevant documents, say so and use general knowledge

    # **TONE GUIDELINES**
    - Start with a friendly greeting
    - Use contractions (I'm, you're, that's)
    - End with an invitation for follow-up
    - Keep paragraphs short (3-4 sentences)
    - Use transitional phrases

    # **YOUR RESPONSE STRUCTURE MUST BE:**
    1. Title with `#`
    2. Introduction paragraph
    3. Clear sections with `##` headings
    4. Subsections with `###` when needed
    5. Lists with `-` or numbers when appropriate
    6. Tables for comparisons
    7. Code examples when relevant
    8. Summary/conclusion
    9. Friendly closing

    **Failure to follow these formatting rules will result in poor user experience.**
    """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
    def create_structured_prompt(self, user_query: str, documents: list) -> list:
        """Create a structured prompt that forces organized responses"""
        
        document_context = ""
        for doc in documents:
            document_context += f"\n\n--- {doc['filename']} ---\n{doc['content']}"  #[:3000]
        
        system_prompt = f"""You are a helpful AI assistant. You provide clear, structured answers based on the provided documents when available.

RESPONSE STRUCTURE REQUIREMENTS:
1. **Title**: Clear, descriptive title using # 
2. **Executive Summary**: 2-3 sentence overview of the answer
3. **Main Content**: Organized into logical sections with ## and ### headings
4. **Key Points**: Bulleted lists (-) for important features or items
5. **Procedures**: Numbered lists (1., 2., 3.) for steps or sequences
6. **Tables**: Use markdown tables for comparisons or data
7. **Code Blocks**: ```language for code examples
8. **References**: Mention specific document names when using them
9. **Conclusion**: Summary of main takeaways
10. **Further Reading**: Suggestions if applicable

FORMATTING RULES:
- Use proper markdown syntax throughout
- Keep paragraphs under 5 sentences
- Bold important terms on first mention
- Use italics for emphasis where appropriate
- Include section breaks with horizontal rules (---)
- Add footnotes or asides in parentheses

DOCUMENT INTEGRATION:
- Quote directly from documents when relevant
- Cite which document provided specific information
- Compare information if multiple documents have differing views

If documents don't contain the information, provide your best answer based on general knowledge with appropriate structure."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    

    def fix_broken_formatting(self, response_text: str) -> str:
        """Clean up broken formatting in AI responses"""
        
        # Fix incorrect list format: "- Item: Explanation" → "**Item:** Explanation"
        lines = response_text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix broken list format
            if line.strip().startswith('- ') and ':' in line:
                # Convert "- Item: Explanation" to "**Item:** Explanation"
                parts = line.split(':', 1)
                if len(parts) == 2:
                    item = parts[0].replace('- ', '').strip()
                    explanation = parts[1].strip()
                    fixed_line = f"**{item}:** {explanation}"
                    fixed_lines.append(fixed_line)
                    continue
            
            # Fix broken table format
            if '---' in line and '|' not in line:
                # This is likely a broken table separator
                # Skip or fix based on context
                continue
                
            # Fix headings with incorrect symbols
            if line.strip().startswith('-') and len(line.strip()) > 2:
                # This might be intended as a heading
                # Check if it's followed by lowercase text (likely a heading mistake)
                rest_of_line = line.strip()[1:].strip()
                if rest_of_line and not rest_of_line[0].islower():
                    # Convert to proper heading
                    fixed_line = f"## {rest_of_line}"
                    fixed_lines.append(fixed_line)
                    continue
            
            fixed_lines.append(line)
        
        # Join back with proper line breaks
        fixed_text = '\n'.join(fixed_lines)
        
        # Ensure proper table formatting
        if 'Feature' in fixed_text and 'REST API' in fixed_text and 'GraphQL' in fixed_text:
            # Look for table-like structure and fix it
            lines = fixed_text.split('\n')
            table_start = -1
            for i, line in enumerate(lines):
                if 'Feature' in line and ('REST' in line or 'GraphQL' in line):
                    table_start = i
                    break
            
            if table_start >= 0:
                # Ensure proper table format
                if '|' not in lines[table_start]:
                    # Reformat the table
                    table_lines = []
                    for j in range(table_start, min(table_start + 10, len(lines))):
                        if '---' in lines[j] or not lines[j].strip():
                            break
                        table_lines.append(lines[j])
                    
                    if len(table_lines) > 1:
                        # Create proper markdown table
                        header = table_lines[0]
                        header_parts = [h.strip() for h in header.split('\t') if h.strip()]
                        if len(header_parts) >= 3:
                            # Build proper table
                            separator = '| ' + ' | '.join(['---'] * len(header_parts)) + ' |'
                            proper_table = f"| {' | '.join(header_parts)} |\n{separator}"
                            
                            # Add data rows
                            for row in table_lines[1:]:
                                row_parts = [r.strip() for r in row.split('\t') if r.strip()]
                                if len(row_parts) == len(header_parts):
                                    proper_table += f"\n| {' | '.join(row_parts)} |"
                            
                            # Replace the broken table
                            table_text = '\n'.join(table_lines)
                            fixed_text = fixed_text.replace(table_text, proper_table)
        
        return fixed_text
    
    async def generate_streaming_response(self, user_query: str, relevant_docs: list = None):
        """Generate streaming response with enforced formatting"""
        try:
            # Check if this is a greeting or casual conversation
            if self.is_casual_conversation(user_query):
                response_text = self.get_casual_response(user_query)
                # Apply formatting fix if needed
                response_text = self.fix_broken_formatting(response_text)
                for char in response_text:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.02)
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # For document queries with no results
            if not relevant_docs:
                intro = "I'll share what I know about that topic based on my general knowledge..."
                for char in intro:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.015)
                
                messages = [
                    {"role": "system", "content": self.create_human_friendly_prompt(user_query, [])[0]['content']},
                    {"role": "user", "content": user_query}
                ]
                
                stream = self.client.chat.completions.create(
                    messages=messages,
                    model=settings.GROQ_MODEL,
                    temperature=0.7,
                    max_tokens=1500,
                    stream=True
                )
                
                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                # Fix formatting if needed
                fixed_response = self.fix_broken_formatting(full_response)
                if fixed_response != full_response:
                    # Send correction if needed
                    correction = "\n\n*[Formatting improved for readability]*"
                    for char in correction:
                        yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # Use human-friendly prompt for document queries
            messages = self.create_human_friendly_prompt(user_query, relevant_docs)
            doc_names = [doc['filename'] for doc in relevant_docs]
            
            # First, send document info
            yield f"data: {json.dumps({'type': 'documents', 'documents': doc_names})}\n\n"
            
            # Stream the response
            stream = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=2000,  # Increased for formatted responses
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # Fix any formatting issues
            fixed_response = self.fix_broken_formatting(full_response)
            if fixed_response != full_response:
                # Note about formatting
                note = "\n\n*[Response formatted for better readability]*"
                for char in note:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': doc_names})}\n\n"
            
        except Exception as e:
            error_msg = f"Oops! I encountered an issue: {str(e)}. Could you please try again?"
            for char in error_msg:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"



{
    "total_files": 3,
    "processed": 3,
    "successful": 2,
    "failed": 1,
    "skipped": 0,
    "errors": [],
    "successful_files": [
        "Java programming",
        "React Js"
    ],
    "failed_files": {
        "AIorML.rtf": "Failed to insert document into database"
    },
    "skipped_files": []
}