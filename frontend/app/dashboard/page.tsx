import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import ResearchWorkspace from "./workspace";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");
  return <ResearchWorkspace email={user.email ?? "Authenticated user"} />;
}
