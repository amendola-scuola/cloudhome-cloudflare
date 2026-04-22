import jwt from "jsonwebtoken";

export function auth(request) {
  const token = request.headers.get("Authorization")?.replace("Bearer ", "");
  if (!token) throw new Error("No token");

  return jwt.verify(token, process.env.JWT_SECRET);
}