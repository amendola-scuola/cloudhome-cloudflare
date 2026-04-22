import { createClient } from "@supabase/supabase-js";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE
);

export async function onRequestPost(context) {
  const { nome, password } = await context.request.json();

  const { data: user } = await supabase
    .from("utente")
    .select("*")
    .eq("nome", nome)
    .single();

  if (!user) {
    return new Response("User not found", { status: 401 });
  }

  const valid = await bcrypt.compare(password, user.user_password);
  if (!valid) {
    return new Response("Wrong password", { status: 401 });
  }

  const token = jwt.sign(
    { id: user.id_utente },
    process.env.JWT_SECRET,
    { expiresIn: "1h" }
  );

  return Response.json({ token });
}