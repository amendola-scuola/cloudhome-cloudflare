import { createClient } from "@supabase/supabase-js";
import { auth } from "./middleware";

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE
);

export async function onRequestGet(context) {
  try {
    auth(context.request);

    const { data } = await supabase
      .from("dispositivo")
      .select("*");

    return Response.json(data);
  } catch {
    return new Response("Unauthorized", { status: 401 });
  }
}