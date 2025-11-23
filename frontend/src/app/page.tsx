'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { COUNTRIES, LANGUAGES, Mode, SearchParams, API_OPTIONS } from '@/types';

export default function Home() {
  const router = useRouter();
  const [formData, setFormData] = useState<SearchParams>({
    prompt: '',
    keywords: '',
    country: 'us',
    language: 'en',
    mode: 'Standard',
    apis: ['google_search'],
    llm_provider: 'gemini-1.5-flash',
  });

  const handleApiToggle = (apiId: string) => {
    setFormData((prev) => {
      const apis = prev.apis.includes(apiId)
        ? prev.apis.filter((id) => id !== apiId)
        : [...prev.apis, apiId];
      return { ...prev, apis };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error('Failed to start search');

      const data = await res.json();
      router.push(`/dashboard?jobId=${data.id}`);
    } catch (error) {
      console.error(error);
      alert('Error starting search. Is the backend running?');
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl my-8">
        <h1 className="text-4xl font-bold text-center mb-2 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
          Keyword RAG Service
        </h1>
        <p className="text-slate-400 text-center mb-8">
          Generate high-quality prompts from real-world data.
        </p>

        <div className="flex justify-center mb-8">
          <Link
            href="/prompt-generator"
            className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
          >
            Or generate prompts from existing CSV hierarchy &rarr;
          </Link>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Prompt Input */}
          <div className="space-y-2">
            <label htmlFor="prompt" className="block text-sm font-medium text-slate-300">
              Core Prompt / Topic
            </label>
            <textarea
              id="prompt"
              required
              rows={4}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder-slate-500 resize-y"
              placeholder="e.g., Best coffee machine for home"
              value={formData.prompt}
              onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
            />
          </div>

          {/* Reference Keywords */}
          <div className="space-y-2">
            <label htmlFor="keywords" className="block text-sm font-medium text-slate-300">
              Reference Keywords (Optional)
            </label>
            <textarea
              id="keywords"
              rows={3}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder-slate-500 resize-y"
              placeholder="espresso, latte, barista (comma separated)"
              value={formData.keywords}
              onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Country */}
            <div className="space-y-2">
              <label htmlFor="country" className="block text-sm font-medium text-slate-300">
                Country
              </label>
              <select
                id="country"
                className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              >
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Language */}
            <div className="space-y-2">
              <label htmlFor="language" className="block text-sm font-medium text-slate-300">
                Language
              </label>
              <select
                id="language"
                className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Mode */}
            <div className="space-y-2">
              <label htmlFor="mode" className="block text-sm font-medium text-slate-300">
                Mode
              </label>
              <select
                id="mode"
                className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                value={formData.mode}
                onChange={(e) => setFormData({ ...formData, mode: e.target.value as Mode })}
              >
                <option value="Light">Light</option>
                <option value="Standard">Standard</option>
                <option value="Full">Full</option>
              </select>
            </div>

            {/* LLM Provider */}
            <div className="space-y-2">
              <label htmlFor="llm" className="block text-sm font-medium text-slate-300">
                LLM Model
              </label>
              <select
                id="llm"
                className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                value={formData.llm_provider}
                onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
              >
                <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="gemini-3.0-preview">Gemini 3.0 Preview</option>
                <option value="gpt-4o">GPT-4o (OpenAI)</option>
              </select>
            </div>
          </div>

          {/* API Selection */}
          <div className="space-y-4 pt-4 border-t border-slate-700/50">
            <h3 className="text-lg font-semibold text-slate-300">Data Sources</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {API_OPTIONS.map((category) => (
                <div key={category.category} className="space-y-3">
                  <h4 className="text-sm font-medium text-blue-400 uppercase tracking-wider">
                    {category.category}
                  </h4>
                  <div className="space-y-2">
                    {category.items.map((api) => (
                      <label key={api.id} className="flex items-center space-x-3 cursor-pointer group">
                        <div className="relative flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.apis.includes(api.id)}
                            onChange={() => handleApiToggle(api.id)}
                            className="peer h-5 w-5 cursor-pointer appearance-none rounded-md border border-slate-600 bg-slate-800/50 transition-all checked:border-blue-500 checked:bg-blue-500 hover:border-blue-400"
                          />
                          <svg
                            className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white opacity-0 transition-opacity peer-checked:opacity-100"
                            width="12"
                            height="12"
                            viewBox="0 0 12 12"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              d="M10 3L4.5 8.5L2 6"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </div>
                        <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
                          {api.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-4 rounded-lg shadow-lg transform transition-all active:scale-[0.98] hover:shadow-blue-500/25 mt-8"
          >
            Start Generation
          </button>
        </form>
      </div>
    </main>
  );
}
