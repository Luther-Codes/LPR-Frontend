// app/auth/callback/route.ts
import { createClient } from "@/lib/supabase/client";
// import { cookies, headers } from 'next/headers';
import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");

  if (code) {
    const supabase = createClient();
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(url.origin + "/");
}
