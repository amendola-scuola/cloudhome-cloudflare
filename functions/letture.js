import { createClient } from "@supabase/supabase-js";
import { auth } from "./middleware";

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE
);

export async function onRequestPost(context) {
  try {
    auth(context.request);

    const body = await context.request.json();

    const { error } = await supabase
      .from("lettura")
      .insert(body);

    if (error) throw error;

    return new Response("OK");
  } catch {
    return new Response("Error", { status: 500 });
  }
}