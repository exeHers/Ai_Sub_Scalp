import { NextResponse } from "next/server";
import { readFile, stat } from "fs/promises";
import path from "path";

export const dynamic = "force-dynamic";

const OUTPUT_PATH = path.join(process.cwd(), "outputs", "deals.json");

export async function GET() {
  try {
    const [contents, fileStat] = await Promise.all([
      readFile(OUTPUT_PATH, "utf-8"),
      stat(OUTPUT_PATH)
    ]);
    const parsed = JSON.parse(contents);
    const dealsCount = Array.isArray(parsed) ? parsed.length : 0;

    return NextResponse.json({
      status: "ok",
      last_updated: fileStat.mtime.toISOString(),
      deals_count: dealsCount
    });
  } catch {
    return NextResponse.json({
      status: "missing",
      last_updated: null,
      deals_count: 0
    });
  }
}
