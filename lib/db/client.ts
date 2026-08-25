// Single local SQLite connection. One user, one file, no pooling needed — spec §11.

import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";

import * as schema from "./schema";

const DB_PATH = process.env.SCOUTREACH_DB_PATH ?? "scoutreach.db";

const sqlite = new Database(DB_PATH);
sqlite.pragma("journal_mode = WAL");

export const db = drizzle(sqlite, { schema });
