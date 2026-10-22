import { createClient } from "@supabase/supabase-js";
const base = (import.meta.env.VITE_VIDEL_API_URL || "").replace(/\/$/, "");
const url = import.meta.env.VITE_SUPABASE_URL || "";
const key = import.meta.env.VITE_SUPABASE_ANON_KEY || "";
export const auth = url && key ? createClient(url, key) : null;
export const configured = Boolean(auth && base);
export type Job = { id: string; state: string; progress: number; error: string | null; filename: string };
export async function token(): Promise<string> {
  if (!auth) throw new Error("Supabase login is not configured");
  const { data, error } = await auth.auth.getSession();
  if (error || !data.session) throw new Error("Sign in to enhance videos");
  return data.session.access_token;
}
export async function createJob(file: File, scale: number, quality: string): Promise<Job> {
  if (!configured) throw new Error("GPU API is not configured");
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(base + "/jobs?scale=" + scale + "&quality=" + encodeURIComponent(quality), {
    method: "POST", headers: { Authorization: "Bearer " + await token() }, body
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Upload failed");
  return payload as Job;
}
export async function getJob(id: string): Promise<Job> {
  const response = await fetch(base + "/jobs/" + id, { headers: { Authorization: "Bearer " + await token() } });
  if (!response.ok) throw new Error("Could not check job progress");
  return response.json();
}
export async function downloadJob(id: string): Promise<void> {
  const response = await fetch(base + "/jobs/" + id + "/download", { headers: { Authorization: "Bearer " + await token() } });
  if (!response.ok) throw new Error("Download failed");
  const objectUrl = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = "videl-enhanced.mp4";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
}
