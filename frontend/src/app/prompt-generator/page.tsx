'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function PromptGenerator() {
    const [csvContent, setCsvContent] = useState<string>('');
    const [prompts, setPrompts] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target?.result as string;
            setCsvContent(content);
        };
        reader.readAsText(file);
    };

    const handleGenerate = async () => {
        if (!csvContent) return;

        setLoading(true);
        setError(null);
        setPrompts([]);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/api/generate-prompts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    csv_content: csvContent,
                    llm_provider: 'gemini-2.5-flash' // Default or selectable
                }),
            });

            if (!res.ok) {
                throw new Error('Failed to generate prompts');
            }

            const data = await res.json();
            setPrompts(data.prompts || []);
        } catch (err) {
            console.error(err);
            setError('Failed to generate prompts. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-900 text-white p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                        CSV Prompt Generator
                    </h1>
                    <Link
                        href="/"
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        Back to Home
                    </Link>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 space-y-6">
                    <div className="space-y-4">
                        <label className="block text-sm font-medium text-slate-300">
                            Upload Hierarchy CSV
                        </label>
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileUpload}
                            className="block w-full text-sm text-slate-400
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-full file:border-0
                                file:text-sm file:font-semibold
                                file:bg-blue-600 file:text-white
                                hover:file:bg-blue-700
                                cursor-pointer"
                        />
                        <p className="text-xs text-slate-500">
                            Expected format: Depth1, Depth2, Depth3
                        </p>
                    </div>

                    {csvContent && (
                        <div className="space-y-2">
                            <h3 className="text-sm font-medium text-slate-300">CSV Preview</h3>
                            <div className="bg-slate-900/50 p-4 rounded-lg max-h-40 overflow-y-auto text-xs font-mono text-slate-400 whitespace-pre-wrap">
                                {csvContent}
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleGenerate}
                        disabled={!csvContent || loading}
                        className={`w-full py-3 rounded-lg font-semibold transition-all ${!csvContent || loading
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg shadow-blue-500/25'
                            }`}
                    >
                        {loading ? 'Generating Prompts...' : 'Generate Prompts from CSV'}
                    </button>

                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}
                </div>

                {prompts.length > 0 && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <h2 className="text-xl font-semibold text-slate-300">Generated Prompts</h2>
                        <div className="grid gap-4">
                            {prompts.map((prompt: any, i: number) => (
                                <div
                                    key={i}
                                    className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-blue-500/50 transition-colors group"
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <span className="bg-blue-500/10 text-blue-400 text-xs px-2 py-1 rounded-full">
                                            {prompt.type || 'Prompt'}
                                        </span>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(prompt.content || prompt.text)}
                                            className="text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            Copy
                                        </button>
                                    </div>
                                    <div className="mb-2 text-sm font-semibold text-blue-300">
                                        Topic: {prompt.topic}
                                    </div>
                                    <p className="text-slate-200 leading-relaxed">
                                        {prompt.content || prompt.text}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
