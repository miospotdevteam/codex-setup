import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const server = new McpServer({
  name: 'claude-bridge',
  version: '0.1.0',
});

function pythonCommand() {
  return process.env.CLAUDE_BRIDGE_PYTHON || 'python3';
}

function bridgeCliPath() {
  return path.join(__dirname, 'bridge_cli.py');
}

function invokeBridge(action, payload) {
  return new Promise((resolve, reject) => {
    const child = spawn(pythonCommand(), [bridgeCliPath(), action], {
      cwd: process.cwd(),
      env: process.env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', chunk => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', chunk => {
      stderr += chunk.toString();
    });
    child.on('error', reject);
    child.on('close', code => {
      const text = stdout.trim();
      if (!text) {
        reject(new Error(stderr.trim() || 'claude-bridge backend returned empty output.'));
        return;
      }

      try {
        resolve({
          code: code ?? 1,
          parsed: JSON.parse(text),
          stderr: stderr.trim(),
        });
      } catch (error) {
        reject(
          new Error(
            stderr.trim() || `claude-bridge backend returned invalid JSON: ${text}`,
          ),
        );
      }
    });

    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  });
}

function toToolResult(payload, isError = false) {
  return {
    content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
    isError,
  };
}

async function callBridge(action, payload) {
  const { code, parsed, stderr } = await invokeBridge(action, payload);
  if (code === 0) {
    return toToolResult(parsed);
  }

  const errorPayload = stderr ? { ...parsed, stderr } : parsed;
  return toToolResult(errorPayload, true);
}

server.registerTool(
  'brainstorm_start',
  {
    description:
      'Queue a live Claude brainstorming session in VS Code. Use this for interactive brainstorming where the user will talk to Claude directly and Codex will read the transcript via brainstorm_status.',
    inputSchema: {
      cwd: z.string(),
      title: z.string(),
      prompt: z.string(),
      sessionId: z.string().optional(),
      pluginDir: z.string().optional(),
    },
  },
  async input => callBridge('brainstorm_start', input),
);

server.registerTool(
  'brainstorm_status',
  {
    description:
      'Read machine-visible status and recent transcript events from a live Claude brainstorming session launched by brainstorm_start.',
    inputSchema: {
      sessionId: z.string(),
      tailEvents: z.number().int().min(1).max(200).optional(),
    },
  },
  async input => callBridge('brainstorm_status', input),
);

server.registerTool(
  'frontend_implement',
  {
    description:
      'Run a headless Claude frontend implementation pass for a visually material step. Claude edits the same working tree directly. Reuse bridgeSessionId to send Codex follow-up on the same thread.',
    inputSchema: {
      cwd: z.string(),
      planName: z.string().optional(),
      stepId: z.number().int(),
      stepTitle: z.string(),
      description: z.string(),
      acceptanceCriteria: z.string(),
      filesInScope: z.array(z.string()).optional(),
      discoverySummary: z.string().optional(),
      designSummary: z.string().optional(),
      prompt: z.string(),
      followUpPrompt: z.string().optional(),
      bridgeSessionId: z.string().optional(),
      pluginDir: z.string().optional(),
    },
  },
  async input => callBridge('frontend_implement', input),
);

server.registerTool(
  'verify_step',
  {
    description:
      'Run a headless Claude verification pass for a plan step. This is a hard reviewer gate. Reuse bridgeSessionId for re-verification on the same Claude thread. Non-PASS rounds write JSON findings files.',
    inputSchema: {
      cwd: z.string(),
      planName: z.string(),
      stepId: z.number().int(),
      stepTitle: z.string(),
      description: z.string(),
      acceptanceCriteria: z.string(),
      filesInScope: z.array(z.string()).optional(),
      discoveryScope: z.string().optional(),
      discoveryConsumers: z.string().optional(),
      discoveryBlastRadius: z.string().optional(),
      verificationCommands: z.string().optional(),
      bridgeSessionId: z.string().optional(),
      pluginDir: z.string().optional(),
      findingsDir: z.string().optional(),
    },
  },
  async input => callBridge('verify_step', input),
);

console.error('claude-bridge MCP server running on stdio');
await server.connect(new StdioServerTransport());
