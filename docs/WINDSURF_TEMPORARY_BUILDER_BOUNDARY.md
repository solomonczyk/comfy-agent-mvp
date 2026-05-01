# Windsurf Temporary Builder Boundary

## Windsurf Allowed During Development

Windsurf is allowed to:
- **Edit code**: Modify source files during development
- **Run CLI**: Execute CLI commands for testing and verification
- **Return logs/proof**: Provide execution logs and proof of work
- **Commit/push**: Commit changes and push to repository

## Windsurf Forbidden

Windsurf is forbidden from:
- **Orchestrator**: Windsurf must NOT act as the orchestrator in production
- **Production decision-maker**: Windsurf must NOT make production decisions
- **QA agent**: Windsurf must NOT act as QA agent
- **Director**: Windsurf must NOT act as director
- **Source of state transitions**: Windsurf must NOT be the source of state transitions
- **Final runtime dependency**: Final runtime must NOT require Windsurf

## Final Runtime Requirements

The final runtime must:
- Work with operator + combine only
- NOT require Windsurf
- NOT depend on Windsurf for any production functionality
- NOT use Windsurf for state management
- NOT use Windsurf for decision-making

## Development vs Production

### Development Phase
- Windsurf is used as a build-helper
- Windsurf edits code, runs tests, provides feedback
- Windsurf helps implement features and fix bugs

### Production Phase
- Windsurf is NOT present
- Operator + combine only
- All functionality works without Windsurf
- No Windsurf dependencies in production code

## Boundary Enforcement

The boundary is enforced by:
- Architecture documentation explicitly stating Windsurf's temporary role
- No Windsurf-specific code in production paths
- No Windsurf API calls in orchestrator
- No Windsurf dependencies in final runtime
- Tests verify production works without Windsurf

## Verification

To verify Windsurf is not a production dependency:
- Check that orchestrator does not import Windsurf-specific modules
- Check that CLI commands work without Windsurf
- Check that state machine transitions work without Windsurf
- Check that generation works without Windsurf
- Check that all acceptance tests pass without Windsurf
