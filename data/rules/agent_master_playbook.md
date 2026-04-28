# Agent Master Playbook

This document defines the core operational principles and guidelines for the SDXL agent.

## Core Principles

1. **User Intent First**: Always prioritize the user's creative intent over technical constraints
2. **Quality Focused**: Maintain high visual quality standards for all generated images
3. **Predictable Results**: Ensure consistent behavior across different prompts and presets
4. **Safety First**: Never generate harmful, illegal, or inappropriate content

## Operational Workflow

1. **Prompt Processing**
   - Accept user prompt in natural language
   - Apply prompt rewriting if requested (via OpenRouter LLM)
   - Validate prompt length and content

2. **Preset Application**
   - Load preset configuration for the requested mode
   - Apply preset-specific parameters (resolution, steps, CFG, etc.)
   - Allow manual overrides when explicitly specified

3. **Generation Execution**
   - Queue prompt to ComfyUI
   - Monitor execution status
   - Wait for completion with timeout handling
   - Extract generated images

4. **Result Handling**
   - Save images to appropriate output directory
   - Generate metadata JSON with full execution details
   - Return comprehensive result to user

## Error Handling

- **ComfyUI Unavailable**: Return clear error message with connection troubleshooting
- **Invalid Preset**: List available presets and suggest alternatives
- **Generation Timeout**: Return partial results if available, suggest retry
- **API Failure (OpenRouter)**: Fall back to local prompt enhancement

## Quality Standards

- Minimum resolution: 512x512
- Recommended steps: 20-40 depending on complexity
- CFG range: 5.0-8.0 for balanced quality/creativity
- Negative prompts must include quality degraders

## Future Enhancements

- [ ] Add workflow validation before execution
- [ ] Implement prompt safety filtering
- [ ] Add batch generation support
- [ ] Create preset management UI
- [ ] Add result history and comparison tools
