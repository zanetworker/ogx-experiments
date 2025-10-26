# Changelog

All notable changes to the Llama Stack Ollama configuration.

## [2.0.0] - 2025-10-21

### 🎉 Complete Migration to v2 Format

Successfully migrated from deprecated two-step workflow to v2 configuration format.

### Added
- ✅ Centralized `storage` configuration with reusable backends
- ✅ Conditional provider activation based on environment variables
- ✅ Proper `registered_resources` structure
- ✅ Environment variable support for all configurable values
- ✅ Virtual environment check in run script
- ✅ Comprehensive documentation suite:
  - SUMMARY.md - Migration overview and success metrics
  - MIGRATION-GUIDE.md - Complete v1→v2 migration guide
  - TROUBLESHOOTING.md - Common errors and solutions
  - V2-FORMAT-CHANGES.md - Detailed format reference
  - FIXES.md - Technical implementation details

### Changed
- 🔄 **BREAKING**: Workflow simplified - no more `llama stack build` step
- 🔄 **BREAKING**: Provider storage configs use correct field names (`kvstore` vs `persistence`)
- 🔄 **BREAKING**: Resources moved under `registered_resources` namespace
- 🔄 **BREAKING**: Centralized storage backends replace individual database paths
- 🔄 Server configuration simplified (removed invalid `host` field)
- 🔄 Telemetry configuration simplified to `enabled: true`
- 🔄 Provider IDs use conditional syntax (e.g., `${env.API_KEY:+provider}`)

### Removed
- ❌ `llama stack build` workflow (deprecated)
- ❌ Invalid `inline::rag-runtime` provider (RAG is built-in)
- ❌ Invalid telemetry fields
- ❌ Invalid server host configuration
- ❌ Individual database paths in provider configs

### Fixed
- 🐛 Server host validation error
- 🐛 Telemetry schema validation errors
- 🐛 DatasetIO field name (`persistence` → `kvstore`)
- 🐛 Eval field name (`persistence` → `kvstore`)
- 🐛 Tool groups conditional provider_id
- 🐛 RAG runtime provider error
- 🐛 Stale database schema (v1 `vector_db` → v2 `vector_store`)
- 🐛 Python environment detection
- 🐛 File caching issues

**Total Issues Fixed**: 10

See [MIGRATION-GUIDE.md](MIGRATION-GUIDE.md) for complete details.

### Environment Variables

**New in v2**:
- `LLAMA_STACK_PORT` - Server port (default: 8321)
- `SQLITE_STORE_DIR` - Base directory for SQLite databases
- `FILES_STORAGE_DIR` - Directory for file storage
- `OLLAMA_URL` - Ollama server URL (default: http://localhost:11434)

**Conditional Providers** (only enabled if env var is set):
- `OPENAI_API_KEY` - Enables OpenAI and Braintrust providers
- `BRAVE_SEARCH_API_KEY` - Enables Brave Search
- `TAVILY_SEARCH_API_KEY` - Enables Tavily Search

### Documentation

See the documentation suite for complete information:
- **[SUMMARY.md](SUMMARY.md)** - Start here! Migration overview
- **[MIGRATION-GUIDE.md](MIGRATION-GUIDE.md)** - Complete migration guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Error solutions
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference
- **[README.md](README.md)** - Main documentation

### Validation

Configuration validated against:
- ✅ StackRunConfig v2 schema
- ✅ Starter distribution format
- ✅ All provider configuration requirements
- ✅ Pydantic validation (all errors resolved)

### Status

✅ **COMPLETE AND WORKING**

---

## [1.0.0] - Previous

Initial configuration using v1 format and two-step workflow (deprecated).

