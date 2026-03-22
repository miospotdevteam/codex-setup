import * as fs from 'node:fs/promises';
import * as os from 'node:os';
import * as path from 'node:path';
import * as vscode from 'vscode';

type StartBrainstormRequest = {
    action: 'start-brainstorm';
    sessionId: string;
    title: string;
    cwd: string;
    sessionDir: string;
    promptFile: string;
    scriptPath: string;
    claudeCommand: string;
    pluginDir?: string | null;
    createdAt: string;
};

const HEARTBEAT_FILE = 'extension-heartbeat.json';

function expandHome(input: string): string {
    if (input.startsWith('~/')) {
        return path.join(os.homedir(), input.slice(2));
    }
    return input;
}

function stateRoot(): string {
    const configured = vscode.workspace
        .getConfiguration('claudeBridge')
        .get<string>('stateRoot', '~/.claude-bridge');
    return path.resolve(expandHome(configured));
}

async function writeJson(filePath: string, payload: unknown): Promise<void> {
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    const tempPath = `${filePath}.tmp`;
    await fs.writeFile(tempPath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
    await fs.rename(tempPath, filePath);
}

async function writeHeartbeat(): Promise<void> {
    await writeJson(path.join(stateRoot(), HEARTBEAT_FILE), {
        timestamp: new Date().toISOString(),
        extensionVersion: '0.1.0',
        pid: process.pid,
    });
}

async function listRequestFiles(): Promise<string[]> {
    const requestsDir = path.join(stateRoot(), 'requests');
    await fs.mkdir(requestsDir, { recursive: true });
    const entries = await fs.readdir(requestsDir);
    return entries
        .filter((name) => name.endsWith('.json'))
        .sort()
        .map((name) => path.join(requestsDir, name));
}

async function readRequest(filePath: string): Promise<StartBrainstormRequest> {
    const raw = await fs.readFile(filePath, 'utf8');
    return JSON.parse(raw) as StartBrainstormRequest;
}

async function markStatus(sessionDir: string, payload: Record<string, unknown>): Promise<void> {
    await writeJson(path.join(sessionDir, 'status.json'), {
        ...payload,
        updatedAt: new Date().toISOString(),
    });
}

async function processRequest(filePath: string): Promise<void> {
    const processingPath = `${filePath}.processing`;
    try {
        await fs.rename(filePath, processingPath);
    } catch {
        return;
    }

    try {
        const request = await readRequest(processingPath);
        if (request.action !== 'start-brainstorm') {
            throw new Error(`Unsupported request action: ${request.action}`);
        }

        const pythonPath = vscode.workspace
            .getConfiguration('claudeBridge')
            .get<string>('pythonPath', 'python3');
        const shellArgs = [
            request.scriptPath,
            '--session-dir',
            request.sessionDir,
            '--cwd',
            request.cwd,
            '--prompt-file',
            request.promptFile,
            '--claude-command',
            request.claudeCommand,
            '--title',
            request.title,
        ];
        if (request.pluginDir) {
            shellArgs.push('--plugin-dir', request.pluginDir);
        }

        await markStatus(request.sessionDir, {
            state: 'launching',
            cwd: request.cwd,
            title: request.title,
            requestedAt: request.createdAt,
            transcriptPath: path.join(request.sessionDir, 'transcript.jsonl'),
        });

        const terminal = vscode.window.createTerminal({
            name: `Claude Brainstorm: ${request.title}`,
            cwd: request.cwd,
            shellPath: pythonPath,
            shellArgs,
        });
        terminal.show(true);

        await markStatus(request.sessionDir, {
            state: 'launched',
            cwd: request.cwd,
            title: request.title,
            requestedAt: request.createdAt,
            launchedAt: new Date().toISOString(),
            transcriptPath: path.join(request.sessionDir, 'transcript.jsonl'),
        });
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        try {
            const raw = await fs.readFile(processingPath, 'utf8');
            const request = JSON.parse(raw) as Partial<StartBrainstormRequest>;
            if (request.sessionDir) {
                await markStatus(request.sessionDir, {
                    state: 'error',
                    error: message,
                });
            }
        } catch {
            // Ignore secondary failure while surfacing the original one.
        }
        vscode.window.showErrorMessage(`claude-bridge failed to start a brainstorm session: ${message}`);
    } finally {
        await fs.rm(processingPath, { force: true });
    }
}

async function pumpRequests(): Promise<void> {
    const files = await listRequestFiles();
    for (const filePath of files) {
        await processRequest(filePath);
    }
}

export function activate(context: vscode.ExtensionContext): void {
    void writeHeartbeat();

    const heartbeat = setInterval(() => {
        void writeHeartbeat();
    }, 5000);
    const pollInterval = vscode.workspace
        .getConfiguration('claudeBridge')
        .get<number>('pollIntervalMs', 1200);
    const poller = setInterval(() => {
        void pumpRequests();
    }, pollInterval);
    void pumpRequests();

    context.subscriptions.push(
        new vscode.Disposable(() => {
            clearInterval(heartbeat);
            clearInterval(poller);
        }),
    );
}

export function deactivate(): void {
    // Timers are disposed through the extension context.
}
