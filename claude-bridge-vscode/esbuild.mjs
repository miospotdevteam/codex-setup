import * as esbuild from 'esbuild';

const isWatch = process.argv.includes('--watch');

const config = {
    entryPoints: ['src/extension.ts'],
    bundle: true,
    outfile: 'out/extension.js',
    platform: 'node',
    target: 'node18',
    format: 'cjs',
    external: ['vscode'],
    sourcemap: true,
};

async function main() {
    if (isWatch) {
        const ctx = await esbuild.context(config);
        await ctx.watch();
        console.log('Watching claude-bridge extension...');
        return;
    }
    await esbuild.build(config);
    console.log('Built claude-bridge extension.');
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});

