Architectural Overview: The "Analyze" Application
The "Analyze" application is an advanced AI orchestration system designed to answer complex user queries by leveraging a variety of internal and external data sources. Its architecture is founded on an AI-First, Zero Hardcoded Rules principle, meaning every decision, from routing to data synthesis, is made by a language model rather than through predefined logic or keyword matching.

The system follows a three-phase workflow: Plan → Execute → Synthesize, with each phase strategically employing different AI models to balance performance, cost, and complexity.
Core Architectural Pattern: Plan → Execute → Synthesize
Phase 1: Planning (Powered by Gemini 2.5 Flash)

Goal: Deconstruct the user query and select the appropriate tools.
Latency: 2-5 seconds.
Process: This phase is a two-stage process. First, it performs Capability Selection, where it identifies which high-level tools are needed (e.g., Departments, Dataverse Marts, External Tools). Second, it performs Question Specialization, generating optimized, domain-specific questions for each selected capability. This ensures that a financial data query is phrased differently than a product strategy query.

Phase 2: Execution (Parallel Processing)

Goal: Concurrently run all selected capabilities to gather information.
Latency: 30-90 seconds.
Process: The system executes queries against three distinct capability types in parallel for maximum efficiency. Each capability has a unique execution pattern:
Departments (Gemini 2.5 Pro): For qualitative analysis and document-based answers.
Dataverse Marts (Gemini 2.5 Flash): For quantitative analysis and structured data retrieval from enterprise databases.
External Tools (Direct Python): For web research and fetching content from URLs.

Phase 3: Synthesis & Validation (Powered by Gemini 2.5 Pro & Granite Guardian)

Goal: Consolidate all gathered information into a single, accurate, and safe response.
Latency: 7-20 seconds.
Process: First, the Synthesizer merges the insights from all execution paths, preserving citations and integrating structured data with narrative responses. Immediately following, the AI Safety Validator (Granite Guardian 3.3) performs critical checks and automatic remediation before presenting the final answer to the user.
Model Strategy: Optimized for Cost and Performance
The application employs a strategic, multi-model approach, using a 90% Gemini and 10% optional Opus model distribution to optimize for cost and speed.

Model
Usage Share
Primary Role & Rationale
Gemini 2.5 Flash
30%
Low-cost, high-speed tasks. Used for initial planning, query routing, and formatting structured data from Dataverse. It is 95% cheaper than Opus and 40% faster than Pro.
Gemini 3.0 Pro
60%
Default for complex reasoning. Used for document analysis, expert responses from Department agents, and final synthesis of all results.
Opus 4.5
10% (Optional)
Advanced, complex orchestration. Can be optionally enabled (--planner opus) for highly ambiguous queries requiring extended autonomous reasoning during the planning phase.
Granite Guardian 3.3
100%
AI safety and validation. Runs on every final response to detect hallucinations, check citation accuracy, and ensure context relevance.



Detailed Phase Breakdown
Phase 1: Unified Two-Stage Planning
The planning phase is driven by a fast, cost-effective model (Gemini 2.5 Flash) to intelligently prepare for execution.

Stage 1: Capability Selection: The planner receives the user query and a list of available capabilities (9 Departments, dynamic Dataverse Marts, 2 External Tools). It uses semantic understanding to determine the optimal combination of tools needed for a comprehensive answer.
Stage 2: Question Specialization: The planner takes the original query and the selected capabilities to generate reframed, optimized questions for each one. This includes personalizing queries (e.g., changing "my direct reports" to a query including the user's email) and adapting the language to the target domain (e.g., financial vs. technical).
Phase 2: Parallel Execution Engine
The system's core performance comes from executing all specialized questions concurrently.

Department Execution (Depth-First Delegation):

Each of the 9 departments (e.g., Finance, Product, Engineering) acts as a high-level agent.
It uses a RecursiveDelegator to automatically discover and delegate tasks to specialized sub-agents (e.g., finance might delegate to finance.earnings).
Delegation and document searches within the department's Google Drive folder run in parallel.
Cost Optimization: If a sub-agent returns a response with a confidence score of ≥0.85, the more expensive document search is skipped, making the response 2x faster and 50% cheaper.

Dataverse Execution (4-Step SQL Workflow):

This capability provides access to Red Hat's enterprise data marts (e.g., RevenueMaster, Apptio) via a structured, Python-based workflow.
shortlist_tables: An AI call identifies the most relevant tables for the query.
get_sql: A second AI call generates a safe, read-only SQL query.
execute_sql: The query is executed against Snowflake.
format_with_gemini: Gemini 2.5 Flash formats the raw SQL results into a natural language summary.
This workflow is highly resilient, with built-in retry logic and timeouts for each step.

External Tools Execution (Direct API Calls):

This is the simplest execution path. Tools like fetch (for URLs) and tavily (for web search) are called directly via their Python APIs without any intermediary AI model.
Phase 3: Synthesis and Guardian Validation
Synthesis: A powerful model (Gemini 2.5 Pro) receives the outputs from all parallel executions. Its job is to weave together qualitative insights from departments, quantitative data from Dataverse, and external research from web tools into a single, cohesive, and comprehensive answer, while carefully preserving all source citations.

Guardian Validation: Before the response is finalized, Granite Guardian 3.3 runs a suite of AI safety checks known as the RAG Triad, which is enabled by default:

Hallucination Detection: Are all claims supported by the provided sources?
Citation Accuracy: Are the citations valid and relevant to the claims?
Context Relevance: Does the answer directly address the user's query intent?
Automatic Remediation: If any issues are found (e.g., a citation has a ≥80% hallucination risk), Guardian will automatically remove the problematic citation, rewrite the affected sentences, and renumber the remaining citations to maintain the integrity of the response.


System Components and Design Patterns
Specification-Driven Development: The architecture is built on an interface-first design principle. Core component interfaces (e.g., Department, Model, Storage) are defined in specs/ and treated as "sacred contracts." This allows implementation details to be changed and optimized without breaking the overall system.

Hierarchical Configuration: The system uses a deep-merging configuration system. Global defaults are set in config/base.json and can be progressively overridden by more specific configurations, such as config/departments/finance.json and config/departments/finance.earnings.json. This makes behavior modification declarative and code-free.

Configuration-Driven Model Selection: The specific AI model used for a task is never hardcoded. The code dynamically selects and instantiates the correct model class (e.g., GeminiModel, OpusModel) based on the string provided in the configuration files.

Provider-Agnostic Document Storage: A three-layer, provider-agnostic architecture manages document handling. Abstract base classes for DocumentStorage and Document ensure that the system can work with any backend (currently Google Drive, with SharePoint and Box designed). AI-generated indexes with driveFileId references enable lazy-loading of documents, and the system transparently resolves Google Drive shortcuts.

Security Patterns: Security is multi-layered, including OAuth with PKCE for service authentication, strict read-only enforcement for all Dataverse SQL queries, document permission isolation via the storage provider, and prompt sanitization to defend against injection attacks.

