import { createClient } from "@supabase/supabase-js";
import bcrypt from "bcryptjs";

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE
);

export async function onRequestPost(context) {
  try {
    const { nome, cognome, password } = await context.request.json();

    if (!nome || !password) {
      return new Response("Missing fields", { status: 400 });
    }

    // hash password
    const hash = await bcrypt.hash(password, 10);

    const { error } = await supabase
      .from("utente")
      .insert({
        nome,
        cognome,
        user_password: hash
      });

    if (error) {
      return new Response(error.message, { status: 500 });
    }

    return new Response("User created");
  } catch (err) {
    return new Response("Error", { status: 500 });
  }
}