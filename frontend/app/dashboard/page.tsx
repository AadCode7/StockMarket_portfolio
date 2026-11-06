import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");
  const modules = [
    ["Stock research", "Instrument lookup and market-data validation."],
    ["Portfolio intelligence", "Holdings, transactions and risk analytics."],
    ["Model lab", "Chronological model evaluation and explainability."],
    ["Research copilot", "Evidence-grounded answers from structured data and documents."],
  ];
  return <main className="mx-auto min-h-screen max-w-6xl px-6 py-12">
    <header className="flex items-center justify-between border-b border-slate-800 pb-6">
      <Link href="/" className="text-lg font-semibold">MarketLens</Link>
      <form action="/auth/signout" method="post"><button className="rounded-lg border border-slate-700 px-4 py-2 text-sm">Sign out</button></form>
    </header>
    <h1 className="mt-10 text-3xl font-semibold">Research workspace</h1>
    <p className="mt-2 text-slate-400">Signed in as {user.email ?? "authenticated user"}.</p>
    <section className="mt-8 grid gap-4 md:grid-cols-2">
      {modules.map(([title, description]) => <article key={title} className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
        <span className="mt-4 inline-block text-xs uppercase tracking-wider text-amber-400">Planned module</span>
      </article>)}
    </section>
  </main>;
}
