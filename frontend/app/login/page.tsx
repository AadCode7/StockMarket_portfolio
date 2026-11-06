"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setLoading(true);
    try {
      const { error: authError } = await createClient().auth.signInWithPassword({ email, password });
      if (authError) throw authError;
      window.location.assign("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally { setLoading(false); }
  }

  return <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
    <Link href="/" className="mb-8 text-sm text-blue-400">← MarketLens</Link>
    <h1 className="text-3xl font-semibold">Welcome back</h1>
    <p className="mt-2 text-slate-400">Sign in to access your research workspace.</p>
    <form onSubmit={submit} className="mt-8 space-y-4">
      <label className="block text-sm text-slate-300">Email
        <input required type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)}
          className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 outline-none focus:border-blue-400" />
      </label>
      <label className="block text-sm text-slate-300">Password
        <input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)}
          className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 outline-none focus:border-blue-400" />
      </label>
      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      <button disabled={loading} className="w-full rounded-lg bg-blue-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{loading ? "Signing in…" : "Sign in"}</button>
    </form>
    <p className="mt-6 text-sm text-slate-400">New here? <Link className="text-blue-400" href="/signup">Create an account</Link></p>
  </main>;
}
