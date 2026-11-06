import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

export default async function HomePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-20">
      <div className="mb-5 text-sm font-semibold uppercase tracking-[0.24em] text-blue-400">MarketLens</div>
      <h1 className="max-w-3xl text-4xl font-semibold leading-tight md:text-6xl">
        Understand the market. Know the evidence behind every number.
      </h1>
      <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">
        Indian equity research, explainable machine learning and portfolio intelligence,
        built around traceable data rather than unsupported predictions.
      </p>
      <div className="mt-9 flex flex-wrap gap-3">
        {user ? <Link className="rounded-lg bg-blue-500 px-5 py-3 font-medium text-slate-950" href="/dashboard">Open dashboard</Link> : <>
          <Link className="rounded-lg bg-blue-500 px-5 py-3 font-medium text-slate-950" href="/login">Sign in</Link>
          <Link className="rounded-lg border border-slate-700 px-5 py-3 font-medium" href="/signup">Create account</Link>
        </>}
      </div>
      <p className="mt-16 text-sm text-slate-500">Research and education only. Not investment advice. Market data delay depends on source.</p>
    </main>
  );
}
