# Research Assistant

The research assistant uses AWS Bedrock Claude to answer OT/ICS security questions with citations.

## How It Works

```mermaid
flowchart TD
    A([1. Analyst submits question]) --> B[2. Retrieval pipeline<br/>finds relevant chunks]
    B --> C[3. Context + source IDs<br/>formatted into prompt]
    C --> D[4. Bedrock Claude generates<br/>structured JSON response]
    D --> E([5. Citations + recommendations<br/>attached to response])
```

## Prompt Templates

The assistant uses versioned prompt templates:

- **Research Query**: Answer questions with citations
- **Summarize**: Summarize threat reports
- **Compare**: Compare incidents or advisories

## Tool Calling

The assistant supports Bedrock tool-calling for:

- `search_threats`: Search the threat database
- `get_advisory`: Retrieve a specific advisory
- `get_recommendations`: Get ML-powered recommendations
